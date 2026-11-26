"""Self-Diagnostics, Self-Healing, Affiliate Link Guard, and Self-Evolution Brain for FinToolLab."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LinkHealth:
    name: str
    url: str
    alive: bool
    status_code: int
    replaced_with: str | None = None


@dataclass
class HealthReport:
    checked_at_utc: str
    overall_status: str  # HEALTHY | DEGRADED | CRITICAL
    api_sources: dict[str, str] = field(default_factory=dict)
    api_counts: dict[str, int] = field(default_factory=dict)
    link_checks: list[LinkHealth] = field(default_factory=list)
    total_pages: int = 0
    seo_audit_passed: bool = True
    evolution_new_items: list[str] = field(default_factory=list)
    self_healed_events: list[str] = field(default_factory=list)


def check_affiliate_links(
    links: dict[str, str],
    fallback_url: str,
    *,
    dry_run: bool = False,
    timeout: int = 6,
) -> tuple[dict[str, str], list[LinkHealth], list[str]]:
    """Verify affiliate URLs are alive; auto-heal dead/expired CPA links with fallback URL."""
    resolved: dict[str, str] = {}
    results: list[LinkHealth] = []
    healed: list[str] = []

    for name, url in links.items():
        if dry_run or not url.startswith("http"):
            resolved[name] = url
            results.append(LinkHealth(name=name, url=url, alive=True, status_code=200))
            continue
        code = 0
        alive = False
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FinToolLab-LinkGuard/1.0)"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                code = resp.status
                final_url = resp.geturl().lower()
                # Detect expired/closed Tenping/CPA campaign redirects
                alive = (200 <= code < 400) and ("error" not in final_url and "expire" not in final_url)
        except urllib.error.HTTPError as exc:
            code = exc.code
            # Some ad networks block headless bots with 403/405 while link is valid for browsers
            alive = code in {403, 405}
        except (urllib.error.URLError, TimeoutError, ValueError):
            alive = False

        if alive:
            resolved[name] = url
            results.append(LinkHealth(name=name, url=url, alive=True, status_code=code))
        else:
            resolved[name] = fallback_url
            healed.append(f"제휴 링크 '{name}' 응답 이상(HTTP {code}) -> 백업 링크({fallback_url})로 자동 자가교체")
            results.append(
                LinkHealth(name=name, url=url, alive=False, status_code=code, replaced_with=fallback_url)
            )
    return resolved, results, healed


def save_last_good_snapshot(data_dir: Path, name: str, items: list[dict[str, Any]], source: str) -> None:
    """Persist verified live API snapshot so future outages self-heal without falling back to dummy data."""
    snap_dir = data_dir / "cache" / "last_good"
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "count": len(items),
        "items": items,
    }
    (snap_dir / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_last_good_snapshot(data_dir: Path, name: str) -> tuple[list[dict[str, Any]], str] | None:
    """Load last verified live API snapshot if available."""
    path = data_dir / "cache" / "last_good" / f"{name}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items", [])
        if isinstance(items, list) and items:
            return items, f"self_healed_snapshot({payload.get('source', 'cached')})"
    except (json.JSONDecodeError, OSError):
        return None
    return None


def track_evolution(
    data_dir: Path,
    current_highlights: list[str],
) -> list[str]:
    """Compare today's live highlights against previous run to surface newly detected opportunities."""
    evo_path = data_dir / "evolution_state.json"
    prev_seen: set[str] = set()
    history: list[dict[str, Any]] = []

    if evo_path.exists():
        try:
            old = json.loads(evo_path.read_text(encoding="utf-8"))
            prev_seen = set(old.get("seen_items", []))
            history = list(old.get("history", []))[-14:]
        except (json.JSONDecodeError, OSError):
            pass

    new_items = [item for item in current_highlights if item not in prev_seen][:8]
    updated_seen = sorted(prev_seen.union(current_highlights))[-300:]
    history.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "new_count": len(new_items),
            "sample_new": new_items[:4],
        }
    )
    evo_path.parent.mkdir(parents=True, exist_ok=True)
    evo_path.write_text(
        json.dumps(
            {
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                "seen_items": updated_seen,
                "history": history,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return new_items


def write_health_outputs(data_dir: Path, dist_dir: Path, report: HealthReport, site_name: str) -> Path:
    """Write machine-readable health_report.json and human-readable dist/status.html."""
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_dir / "health_report.json"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")

    api_rows = "".join(
        f"<tr><td><strong>{k}</strong></td><td><code>{v}</code></td><td>{report.api_counts.get(k, 0)}건</td></tr>"
        for k, v in report.api_sources.items()
    )
    link_rows = "".join(
        f"<tr><td>{lc.name}</td><td><code>{lc.url}</code></td>"
        f"<td>{'✅ 정상' if lc.alive else '🩹 자동교체됨'} ({lc.status_code})</td>"
        f"<td>{lc.replaced_with or '-'}</td></tr>"
        for lc in report.link_checks
    )
    healed_html = (
        "".join(f"<li>{ev}</li>" for ev in report.self_healed_events)
        or "<li>장애 없음 — 모든 API·링크 정상 가동 중</li>"
    )
    evo_html = (
        "".join(f"<li>✨ {ev}</li>" for ev in report.evolution_new_items)
        or "<li>신규 변동 모니터링 중 (직전 스냅샷과 동일)</li>"
    )
    badge_color = "#10b981" if report.overall_status == "HEALTHY" else ("#f59e0b" if report.overall_status == "DEGRADED" else "#ef4444")

    status_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>자가진단 &amp; 자동진화 상태 대시보드 | {site_name}</title>
  <meta name="robots" content="noindex, follow">
  <link rel="stylesheet" href="assets/style.css?v=20261126">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="index.html">{site_name}</a>
      <nav class="main-nav"><a href="index.html">← 505종 전체 허브로 돌아가기</a></nav>
    </div>
  </header>
  <main class="container main-content">
    <section class="card">
      <h1>🤖 오토파일럿 자가진단 · 자가복구 · 자동진화 대시보드</h1>
      <p class="lead">최종 자가점검 시각 (UTC): <code>{report.checked_at_utc}</code> | 전체 상태: <strong style="color:{badge_color};">{report.overall_status}</strong></p>
      <div class="result-strip">
        <div class="metric-box highlight"><div class="metric-label">시스템 건강도</div><div class="metric-value" style="color:{badge_color};">{report.overall_status}</div></div>
        <div class="metric-box"><div class="metric-label">자동 배포 페이지</div><div class="metric-value">{report.total_pages}개</div></div>
        <div class="metric-box"><div class="metric-label">SEO 품질 감사</div><div class="metric-value">{'PASS' if report.seo_audit_passed else 'FAIL'}</div></div>
      </div>
    </section>
    <section class="card">
      <h2>1. 공공 오픈 API 실시간 연동 &amp; 자가복구 상태</h2>
      <table><thead><tr><th>데이터 파이프라인</th><th>데이터 소스 / 상태</th><th>수집 건수</th></tr></thead><tbody>{api_rows}</tbody></table>
    </section>
    <section class="card">
      <h2>2. 제휴(CPA · 쿠팡파트너스) 링크 생존 감시 (LinkGuard)</h2>
      <table><thead><tr><th>슬롯</th><th>원본 URL</th><th>상태</th><th>자동 교체 URL</th></tr></thead><tbody>{link_rows}</tbody></table>
    </section>
    <section class="card">
      <h2>3. 자동진화 탐지 로그 (신규 급상승 공고·금리)</h2>
      <ul>{evo_html}</ul>
    </section>
    <section class="card">
      <h2>4. 자가복구(Self-Healing) 이벤트 로그</h2>
      <ul>{healed_html}</ul>
    </section>
  </main>
  <footer class="site-footer">
    <div class="container">
      <p class="ymyl-disclaimer">공식 출처: 금융감독원·행정안전부·국토교통부·한국부동산원·창업진흥원·심평원 공공 API 자동 점검 리포트</p>
    </div>
  </footer>
</body>
</html>
"""
    status_path = dist_dir / "status.html"
    status_path.write_text(status_html, encoding="utf-8")
    return status_path
