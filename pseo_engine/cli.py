"""CLI entry point for pSEO Revenue Autopilot."""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
import sys
from pathlib import Path

from pseo_engine.calculators import simulate_pseo_monthly_revenue
from pseo_engine.config import SiteConfig
from pseo_engine.fetchers import fetch_financial_products, fetch_subsidy_programs
from pseo_engine.generator import generate_site
from pseo_engine.indexer import submit_indexnow
from pseo_engine.seo_audit import audit_dist


def cmd_run(cfg: SiteConfig) -> int:
    products, fin_src = fetch_financial_products(cfg)
    subsidies, sub_src = fetch_subsidy_programs(cfg)
    is_sample = fin_src.startswith("seed_") or sub_src.startswith("seed_")
    pages = generate_site(cfg, products, subsidies, is_sample_data=is_sample)
    report = audit_dist(cfg.dist_dir)
    index_result = submit_indexnow(cfg, [p.url for p in pages])

    print(f"[1/4] 금융 데이터 수집 완료: {len(products)}건 ({fin_src})")
    print(f"[2/4] 보조금 데이터 수집 완료: {len(subsidies)}건 ({sub_src})")
    print(f"[3/4] pSEO 정적 사이트 빌드 완료: {len(pages)}개 페이지 -> {cfg.dist_dir}")
    print(
        f"[4/4] SEO 품질 감사: {'PASS' if report.passed else 'FAIL'} "
        f"(HTML {report.total_html_pages}개, 깨진 링크 {len(report.broken_internal_links)}건, "
        f"중복 제목 {len(report.duplicate_titles)}건)"
    )
    print(f"      IndexNow: {index_result['message']}")
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
