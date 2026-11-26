"""CLI entry point for pSEO Revenue Autopilot."""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import socketserver
import sys
from pathlib import Path

from datetime import datetime, timezone

from pseo_engine.autopilot_brain import (
    HealthReport,
    check_affiliate_links,
    save_last_good_snapshot,
    track_evolution,
    write_health_outputs,
)
from pseo_engine.calculators import simulate_pseo_monthly_revenue
from pseo_engine.config import SiteConfig
from pseo_engine.fetchers import fetch_financial_products, fetch_subsidy_programs
from pseo_engine.generator import generate_site
from pseo_engine.indexer import submit_indexnow
from pseo_engine.seo_audit import audit_dist
from pseo_engine.social_poster import compose_daily_briefing, post_to_x


def cmd_run(cfg: SiteConfig) -> int:
    products, fin_src = fetch_financial_products(cfg)
    subsidies, sub_src = fetch_subsidy_programs(cfg)
    is_sample = fin_src.startswith("seed_") or sub_src.startswith("seed_")

    # 1) Save last-good live snapshots for future outage self-healing
    if not fin_src.startswith("seed_"):
        save_last_good_snapshot(cfg.data_dir, "finlife", [p.__dict__ for p in products], fin_src)
    if not sub_src.startswith("seed_"):
        save_last_good_snapshot(cfg.data_dir, "subsidy24", [s.__dict__ for s in subsidies], sub_src)

    # 2) Affiliate LinkGuard: verify CPA & Coupang links and auto-heal dead links
    link_map = {
        "coupang_deposit": cfg.affiliate_deposit_url,
        "coupang_loan": cfg.affiliate_loan_url,
        "coupang_subsidy": cfg.affiliate_subsidy_url,
        "tenping_auto_rent": "https://iryan.kr/t8hdd04rss",
        "tenping_money_card": "https://iryan.kr/t8hdd04j25",
    }
    _resolved_links, link_healths, healed_events = check_affiliate_links(
        link_map,
        fallback_url="https://link.coupang.com/a/iSVpT5nClE",
        dry_run=cfg.dry_run,
    )

    pages = generate_site(cfg, products, subsidies, is_sample_data=is_sample)
    report = audit_dist(cfg.dist_dir)
    index_result = submit_indexnow(cfg, [p.url for p in pages])

    # 3) Self-Evolution tracking (detect new high-rate / new subsidy items vs previous run)
    highlights = [f"[금리] {p.bank_name} {p.product_name} ({p.max_rate_pct:.2f}%)" for p in products[:5]] + [
        f"[보조금] {s.title} ({s.agency})" for s in subsidies[:5]
    ]
    new_evo = track_evolution(cfg.data_dir, highlights)

    overall = "HEALTHY" if (report.passed and not healed_events) else ("DEGRADED" if report.passed else "CRITICAL")
    health = HealthReport(
        checked_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_status=overall,
        api_sources={"finlife": fin_src, "subsidy24": sub_src},
        api_counts={"finlife": len(products), "subsidy24": len(subsidies)},
        link_checks=link_healths,
        total_pages=len(pages),
        seo_audit_passed=report.passed,
        evolution_new_items=new_evo,
        self_healed_events=healed_events,
    )
    status_path = write_health_outputs(cfg.data_dir, cfg.dist_dir, health, cfg.site_name)

    print(f"[1/5] 금융 데이터 수집 완료: {len(products)}건 ({fin_src})")
    print(f"[2/5] 보조금 데이터 수집 완료: {len(subsidies)}건 ({sub_src})")
    print(f"[3/5] pSEO 정적 사이트 빌드 완료: {len(pages)}개 페이지 -> {cfg.dist_dir}")
    print(
        f"[4/5] SEO 품질 감사: {'PASS' if report.passed else 'FAIL'} "
        f"(HTML {report.total_html_pages}개, 깨진 링크 {len(report.broken_internal_links)}건, "
        f"중복 제목 {len(report.duplicate_titles)}건)"
    )
    print(
        f"[5/5] 자가진단·진화 리포트: {overall} | 제휴 링크 {sum(1 for l in link_healths if l.alive)}/{len(link_healths)} 정상 "
        f"| 신규 탐지 {len(new_evo)}건 -> {status_path}"
    )
    print(f"      IndexNow: {index_result['message']}")
    if os.environ.get("ENABLE_X_AUTOPOST", "").strip().lower() in {"1", "true", "yes"}:
        top_p = max(products, key=lambda x: x.max_rate_pct, default=None)
        top_s = subsidies[0] if subsidies else None
        rate_line = (
            f"오늘의 최고 금리: {top_p.bank_name} {top_p.product_name} (최고 연 {top_p.max_rate_pct:.2f}%)"
            if top_p
            else "6대 공공 API 금리·실거래가 실시간 업데이트 완료"
        )
        sub_line = (
            f"핵심 지원금: {top_s.title} ({top_s.agency})"
            if top_s
            else "2026 보조금24·청약홈·K-Startup 공고 최신화 완료"
        )
        x_res = post_to_x(compose_daily_briefing(cfg.site_url, rate_line, sub_line), dry_run=cfg.dry_run)
        print(f"      X Auto-Post: {x_res}")
    return 0 if report.passed else 1


def cmd_audit(cfg: SiteConfig) -> int:
    report = audit_dist(cfg.dist_dir)
    print(f"총 HTML 페이지: {report.total_html_pages}")
    print(f"중복 제목: {len(report.duplicate_titles)}")
    print(f"중복 설명: {len(report.duplicate_descriptions)}")
    print(f"깨진 내부 링크: {len(report.broken_internal_links)}")
    print(f"JSON-LD 오류: {len(report.invalid_json_ld)}")
    print(f"YMYL 면책 누락: {len(report.missing_ymyl_disclaimer)}")
    print(f"인터랙티브 위젯 누락: {len(report.missing_interactive_widget)}")
    print(f"필수 파일 누락: {len(report.missing_core_files)}")
    print(f"최종 결과: {'PASS' if report.passed else 'FAIL'}")
    return 0 if report.passed else 1


class _ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def cmd_serve(cfg: SiteConfig, port: int) -> int:
    if not (cfg.dist_dir / "index.html").exists():
        print("dist/index.html이 없어 먼저 빌드를 실행합니다...")
        if cmd_run(cfg) != 0:
            return 1
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(cfg.dist_dir))
    with _ReusableTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"로컬 미리보기 서버 실행 중: http://127.0.0.1:{port}/index.html (종료: Ctrl+C)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다.")
    return 0


def cmd_revenue_sim() -> int:
    print("=== 한국 금융·보조금 pSEO 예상 월수익 시뮬레이션 (보수적 기준: RPM 9,000원, 제휴 CPA 25,000원) ===")
    for pv in (10_000, 30_000, 50_000, 100_000, 300_000):
        s = simulate_pseo_monthly_revenue(pv)
        print(
            f"월 PV {pv:>7,} | 애드센스 {s['adsense_revenue_krw']:>9,}원 "
            f"+ 제휴({s['affiliate_conversions']:>3}건) {s['affiliate_revenue_krw']:>9,}원 "
            f"= 합계 {s['total_monthly_revenue_krw']:>10,}원/월"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pseo-autopilot",
        description="공공데이터 기반 완전 자동화 pSEO 수익 파이프라인 CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="데이터 수집 -> 63개+ SEO 페이지 빌드 -> SEO 감사 -> IndexNow 실행")
    sub.add_parser("audit", help="dist/ 디렉터리 SEO·YMYL 품질 감사")
    serve_p = sub.add_parser("serve", help="빌드된 dist/ 로컬 미리보기 서버 실행")
    serve_p.add_argument("--port", type=int, default=8080, help="로컬 포트 (기본: 8080)")
    sub.add_parser("revenue-sim", help="월간 트래픽별 예상 애드센스 + CPA 수익 시뮬레이션")

    args = parser.parse_args(argv)
    cfg = SiteConfig.from_env(Path.cwd())

    if args.command == "run":
        return cmd_run(cfg)
    if args.command == "audit":
        return cmd_audit(cfg)
    if args.command == "serve":
        return cmd_serve(cfg, args.port)
    if args.command == "revenue-sim":
        return cmd_revenue_sim()
    return 1


if __name__ == "__main__":
    sys.exit(main())
