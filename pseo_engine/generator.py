"""Programmatic SEO static site generator with interactive calculators, JSON-LD, AdSense & CPA slots."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pseo_engine.calculators import calculate_deposit, calculate_loan, calculate_saving
from pseo_engine.config import SiteConfig
from pseo_engine.extra_pages import EXTRA_WIDGET_JS, generate_extra_pages
from pseo_engine.fetchers import FinancialProduct, SubsidyProgram
from pseo_engine.mega_expansion import MEGA_EXPANSION_JS, generate_mega_expansion_pages
from pseo_engine.public_hubs import PUBLIC_HUBS_JS, generate_public_hub_pages
from pseo_engine.ultra_expansion import ULTRA_EXPANSION_JS, generate_ultra_expansion_pages
from pseo_engine.web_tools import TOOLS_JS, generate_web_tool_pages


@dataclass
class GeneratedPage:
    rel_path: str
    url: str
    title: str
    description: str
    category: str


def _fmt_krw(amount: int) -> str:
    return f"{amount:,}원"


def _fmt_manwon(amount: int) -> str:
    if amount >= 100_000_000 and amount % 100_000_000 == 0:
        return f"{amount // 100_000_000}억 원"
    if amount >= 100_000_000:
        eok = amount // 100_000_000
        man = (amount % 100_000_000) // 10_000
        return f"{eok}억 {man:,}만 원"
    return f"{amount // 10_000:,}만 원"


def _esc(text: Any) -> str:
    return html.escape(str(text), quote=True)


def _adsense_slot(cfg: SiteConfig, slot_label: str) -> str:
    if cfg.adsense_client_id:
        return (
            f'<div class="ad-slot" data-ad-slot="{_esc(slot_label)}">'
            f'<ins class="adsbygoogle" style="display:block" '
            f'data-ad-client="{_esc(cfg.adsense_client_id)}" data-ad-format="auto" '
            f'data-full-width-responsive="true"></ins>'
            f"<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>"
            f"</div>"
        )
    return (
        f'<div class="ad-slot ad-slot-placeholder" data-ad-slot="{_esc(slot_label)}" '
        f'aria-label="광고 영역">'
        f'<span>Google AdSense 자동 광고 슬롯 ({_esc(slot_label)}) — .env에 ADSENSE_CLIENT_ID 입력 시 활성화</span>'
        f"</div>"
    )


def _affiliate_box(title: str, subtitle: str, cta_label: str, href: str) -> str:
    return f"""
<aside class="affiliate-card" data-compliance="economic-disclosure">
  <div class="affiliate-badge">쿠팡 파트너스 추천 · 제휴 안내</div>
  <h3>{_esc(title)}</h3>
  <p>{_esc(subtitle)}</p>
  <a class="btn-cta" href="{_esc(href)}" rel="nofollow sponsored noopener" target="_blank">{_esc(cta_label)} (쿠팡 특가 바로가기) →</a>
  <p class="disclosure-note">※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. (공정위 표시광고법 경제적 이해관계 고지)</p>
</aside>
"""


def _base_layout(
    cfg: SiteConfig,
    *,
    title: str,
    description: str,
    canonical_url: str,
    body_html: str,
    json_ld_objects: list[dict[str, Any]],
    asset_prefix: str = "",
    is_sample_data: bool = False,
) -> str:
    adsense_head = ""
    if cfg.adsense_client_id:
        adsense_head = (
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
            f'?client={_esc(cfg.adsense_client_id)}" crossorigin="anonymous"></script>'
        )
    ga4_head = ""
    if cfg.ga4_measurement_id:
        ga4_head = (
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={_esc(cfg.ga4_measurement_id)}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js',new Date());gtag('config','{_esc(cfg.ga4_measurement_id)}');</script>"
        )
    ld_scripts = "\n".join(
        f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'
        for obj in json_ld_objects
    )
    updated_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sample_banner = ""
    if is_sample_data:
        sample_banner = (
            '<div class="sample-banner" data-mode="sample">'
            "※ 현재 <strong>예시(샘플) 데이터 프리뷰 모드</strong>입니다. "
            "실제 실시간 공시 반영을 위해 <code>.env</code>에 금융감독원·보조금24 API 키를 입력하고 "
            "<code>DRY_RUN=false</code>로 빌드하세요."
            "</div>"
        )
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{_esc(canonical_url)}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{_esc(title)}">
  <meta property="og:description" content="{_esc(description)}">
  <meta property="og:url" content="{_esc(canonical_url)}">
  <meta property="og:site_name" content="{_esc(cfg.site_name)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="{_esc(asset_prefix)}assets/style.css?v=20261122c">
  {adsense_head}
  {ga4_head}
  {ld_scripts}
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="{_esc(asset_prefix)}index.html">{_esc(cfg.site_name)}</a>
      <nav class="main-nav" aria-label="주요 메뉴">
        <a href="{_esc(asset_prefix)}index.html#deposit-hub">예적금</a>
        <a href="{_esc(asset_prefix)}index.html#loan-hub">대출</a>
        <a href="{_esc(asset_prefix)}index.html#salary-hub">연봉·세금</a>
        <a href="{_esc(asset_prefix)}index.html#subsidy-hub">보조금24</a>
        <a href="{_esc(asset_prefix)}index.html#tools-hub">웹 유틸리티</a>
        <a href="{_esc(asset_prefix)}index.html#en-hub">Global EN</a>
        <button id="theme-toggle" class="theme-btn" type="button" aria-label="테마 전환">🌓</button>
      </nav>
    </div>
  </header>

  <main class="container main-content">
    {sample_banner}
    {body_html}
  </main>

  <footer class="site-footer">
    <div class="container">
      <p><strong>{_esc(cfg.site_name)}</strong> | 최종 데이터 갱신일: {updated_date}</p>
      <p class="ymyl-disclaimer">※ 공식 출처: 금융감독원 금융상품한눈에 오픈 API 및 행정안전부 보조금24 공공서비스 API. 본 사이트의 계산 결과와 정책 요약은 정보 제공 목적이며 실제 금융상품 가입·보조금 신청 전 해당 기관의 최신 공시를 반드시 확인하시기 바랍니다.</p>
      <p class="footer-links">
        <a href="{_esc(asset_prefix)}index.html">홈</a> ·
        <a href="{_esc(asset_prefix)}privacy.html">개인정보처리방침</a> ·
        <a href="{_esc(asset_prefix)}disclaimer.html">면책고지 및 데이터 출처</a> ·
        <span>문의: {_esc(cfg.contact_email)}</span>
      </p>
    </div>
  </footer>
  <script src="{_esc(asset_prefix)}assets/app.js?v=20261122c" defer></script>
</body>
</html>
"""


def _write_assets(dist_dir: Path) -> None:
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    css = """:root {
  --bg: #f1f5f9;
  --card: #ffffff;
  --card-elev: #ffffff;
  --text: #0f172a;
  --muted: #475569;
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --primary-soft: #eff6ff;
  --accent: #059669;
  --accent-soft: #ecfdf5;
  --border: #e2e8f0;
  --input-bg: #ffffff;
  --header-bg: rgba(255, 255, 255, 0.86);
  --shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.06);
}
[data-theme="dark"] {
  --bg: #0b1120;
  --card: #111827;
  --card-elev: #1e293b;
  --text: #f8fafc;
  --muted: #94a3b8;
  --primary: #3b82f6;
  --primary-dark: #60a5fa;
  --primary-soft: rgba(59, 130, 246, 0.14);
  --accent: #10b981;
  --accent-soft: rgba(16, 185, 129, 0.14);
  --border: #1f2937;
  --input-bg: #0f172a;
  --header-bg: rgba(17, 24, 39, 0.86);
  --shadow: 0 8px 28px -4px rgba(0, 0, 0, 0.45);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
  transition: background 0.2s ease, color 0.2s ease;
}
.container { max-width: 1020px; margin: 0 auto; padding: 0 20px; }
.site-header {
  background: var(--header-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 30;
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 13px 0;
  flex-wrap: wrap;
}
.brand {
  font-weight: 800;
  font-size: 1.12rem;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, var(--primary), #06b6d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-decoration: none;
}
.main-nav { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.main-nav a {
  color: var(--muted);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 5px 8px;
  border-radius: 8px;
  transition: background 0.15s, color 0.15s;
}
.main-nav a:hover { background: var(--primary-soft); color: var(--primary); }
.theme-btn {
  border: 1px solid var(--border);
  background: var(--card-elev);
  color: var(--text);
  border-radius: 8px;
  padding: 5px 9px;
  cursor: pointer;
  font-size: 0.9rem;
}
.main-content { padding: 28px 0 56px; }
.breadcrumb { font-size: 0.85rem; color: var(--muted); margin-bottom: 12px; }
.breadcrumb a { color: var(--muted); text-decoration: none; }
.breadcrumb a:hover { color: var(--primary); }
h1 { font-size: 1.85rem; letter-spacing: -0.025em; line-height: 1.28; margin: 0 0 10px; }
h2 {
  font-size: 1.24rem;
  letter-spacing: -0.015em;
  margin: 26px 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
h2::before {
  content: "";
  width: 4px;
  height: 1.05em;
  border-radius: 99px;
  background: linear-gradient(180deg, var(--primary), var(--accent));
}
.lead { color: var(--muted); margin-bottom: 22px; font-size: 0.98rem; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px;
  margin-bottom: 22px;
  box-shadow: var(--shadow);
  overflow-x: auto;
}
.hero-search {
  width: 100%;
  margin-top: 16px;
  padding: 13px 16px;
  border: 1.5px solid var(--border);
  border-radius: 12px;
  font-size: 0.98rem;
  background: var(--input-bg);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.hero-search:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-soft); }
.calc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.field label { display: block; font-size: 0.85rem; font-weight: 700; margin-bottom: 6px; color: var(--muted); }
.field input, .field select, .field textarea {
  width: 100%;
  padding: 11px 13px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  font-size: 0.98rem;
  background: var(--input-bg);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.field input:focus, .field select:focus, .field textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-soft);
}
.result-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
  gap: 12px;
  margin-top: 20px;
}
.metric-box {
  background: var(--primary-soft);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 15px 16px;
}
.metric-box.highlight {
  background: var(--accent-soft);
  border-color: rgba(16, 185, 129, 0.35);
}
.metric-label { font-size: 0.8rem; font-weight: 600; color: var(--muted); }
.metric-value {
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--text);
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}
table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.92rem; min-width: 560px; }
th, td { padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; }
th { background: var(--primary-soft); font-weight: 700; font-size: 0.85rem; }
tbody tr:hover { background: var(--primary-soft); }
.rate-badge {
  display: inline-block;
  background: var(--primary-soft);
  color: var(--primary);
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 0.84rem;
}
.ad-slot { margin: 22px 0; min-height: 90px; text-align: center; }
.ad-slot-placeholder {
  background: var(--card-elev);
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 22px 12px;
  color: var(--muted);
  font-size: 0.84rem;
}
.affiliate-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #0f766e 100%);
  color: #ffffff;
  border-radius: 16px;
  padding: 24px;
  margin: 24px 0;
  box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.3);
}
.affiliate-badge {
  display: inline-block;
  background: rgba(255,255,255,0.16);
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.affiliate-card h3 { margin: 4px 0 8px; font-size: 1.2rem; }
.affiliate-card p { margin: 0 0 14px; color: #e2e8f0; }
.btn-cta {
  display: inline-block;
  background: #10b981;
  color: #ffffff;
  font-weight: 700;
  text-decoration: none;
  border: none;
  cursor: pointer;
  padding: 11px 18px;
  border-radius: 10px;
  font-size: 0.94rem;
  transition: transform 0.12s ease, background 0.15s ease;
}
.btn-cta:hover { background: #059669; transform: translateY(-1px); }
.disclosure-note { font-size: 0.78rem; color: #cbd5e1 !important; margin-top: 12px !important; margin-bottom: 0 !important; }
.link-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(225px, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.link-pill {
  display: block;
  background: var(--card-elev);
  border: 1px solid var(--border);
  border-radius: 11px;
  padding: 12px 14px;
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  font-size: 0.9rem;
  transition: border-color 0.15s, transform 0.12s, color 0.15s;
}
.link-pill:hover { border-color: var(--primary); color: var(--primary); transform: translateY(-1px); }
.faq-item { border-bottom: 1px solid var(--border); padding: 13px 0; }
.faq-item:last-child { border-bottom: none; }
.faq-item h3 { margin: 0 0 6px; font-size: 1rem; }
.faq-item p { margin: 0; color: var(--muted); font-size: 0.93rem; }
.subsidy-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  background: var(--card-elev);
}
.subsidy-item h3 { margin: 0 0 6px; font-size: 1.05rem; }
.tag {
  display: inline-block;
  background: var(--primary-soft);
  color: var(--primary);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  margin-right: 6px;
}
.site-footer {
  background: var(--card);
  border-top: 1px solid var(--border);
  padding: 26px 0 40px;
  font-size: 0.86rem;
  color: var(--muted);
}
.ymyl-disclaimer { font-size: 0.81rem; color: var(--muted); }
.footer-links a { color: var(--muted); }
.sample-banner {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 18px;
  font-size: 0.9rem;
}
.subsidy-item.matched { border-color: #10b981; background: var(--accent-soft); }
.subsidy-item.dimmed { opacity: 0.55; }
"""
    (assets_dir / "style.css").write_text(css, encoding="utf-8")

    js = """(function () {
  var savedTheme = localStorage.getItem('mpl-theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
  var themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
      localStorage.setItem('mpl-theme', isDark ? 'light' : 'dark');
    });
  }
  var searchEl = document.getElementById('hub-search');
  if (searchEl) {
    searchEl.addEventListener('input', function () {
      var q = searchEl.value.trim().toLowerCase();
      document.querySelectorAll('.link-pill').forEach(function (a) {
        a.style.display = (!q || a.textContent.toLowerCase().indexOf(q) >= 0) ? '' : 'none';
      });
    });
  }
  function fmtKrw(n) {
    return Math.round(n).toLocaleString('ko-KR') + '원';
  }

  document.querySelectorAll('[data-widget="deposit-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="principal"]');
    var mEl = root.querySelector('[name="months"]');
    var rEl = root.querySelector('[name="rate"]');
    var tEl = root.querySelector('[name="tax"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var m = Math.max(1, Number(mEl.value || 12));
      var r = Math.max(0, Number(rEl.value || 0)) / 100;
      var taxRate = Number(tEl.value || 0.154);
      var gross = p * r * (m / 12);
      var tax = gross * taxRate;
      var net = gross - tax;
      root.querySelector('[data-out="gross"]').textContent = fmtKrw(gross);
      root.querySelector('[data-out="tax"]').textContent = fmtKrw(tax);
      root.querySelector('[data-out="net"]').textContent = fmtKrw(net);
      root.querySelector('[data-out="maturity"]').textContent = fmtKrw(p + net);
    }
    [pEl, mEl, rEl, tEl].forEach(function (el) { el.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="saving-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="monthly"]');
    var mEl = root.querySelector('[name="months"]');
    var rEl = root.querySelector('[name="rate"]');
    var tEl = root.querySelector('[name="tax"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var m = Math.max(1, Number(mEl.value || 12));
      var r = Math.max(0, Number(rEl.value || 0)) / 100;
      var taxRate = Number(tEl.value || 0.154);
      var principal = p * m;
      var gross = p * (r / 12) * (m * (m + 1) / 2);
      var tax = gross * taxRate;
      var net = gross - tax;
      root.querySelector('[data-out="principal"]').textContent = fmtKrw(principal);
      root.querySelector('[data-out="tax"]').textContent = fmtKrw(tax);
      root.querySelector('[data-out="net"]').textContent = fmtKrw(net);
      root.querySelector('[data-out="maturity"]').textContent = fmtKrw(principal + net);
    }
    [pEl, mEl, rEl, tEl].forEach(function (el) { el.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="loan-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="principal"]');
    var mEl = root.querySelector('[name="months"]');
    var rEl = root.querySelector('[name="rate"]');
    var typeEl = root.querySelector('[name="repayment"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var m = Math.max(1, Number(mEl.value || 12));
      var mr = Math.max(0, Number(rEl.value || 0)) / 100 / 12;
      var rtype = typeEl.value;
      var firstPay = 0;
      var totalInterest = 0;
      if (rtype === 'bullet') {
        firstPay = p * mr;
        totalInterest = firstPay * m;
      } else if (rtype === 'equal_principal') {
        var mp = p / m;
        firstPay = mp + p * mr;
        for (var i = 0; i < m; i++) {
          totalInterest += (p - mp * i) * mr;
        }
      } else {
        if (mr === 0) {
          firstPay = p / m;
        } else {
          var factor = Math.pow(1 + mr, m);
          firstPay = p * (mr * factor) / (factor - 1);
        }
        totalInterest = Math.max(0, firstPay * m - p);
      }
      root.querySelector('[data-out="monthly"]').textContent = fmtKrw(firstPay);
      root.querySelector('[data-out="interest"]').textContent = fmtKrw(totalInterest);
      root.querySelector('[data-out="total"]').textContent = fmtKrw(p + totalInterest);
    }
    [pEl, mEl, rEl, typeEl].forEach(function (el) { el.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="subsidy-checker"]').forEach(function (root) {
    var incomeEl = root.querySelector('[name="income"]');
    var ageEl = root.querySelector('[name="age"]');
    var outEl = root.querySelector('[data-out="match-summary"]');
    var cards = root.querySelectorAll('[data-subsidy-card]');
    function update() {
      var income = Number(incomeEl.value || 100);
      var age = Number(ageEl.value || 30);
      var matchedCount = 0;
      cards.forEach(function (card) {
        var limit = Number(card.getAttribute('data-max-income') || 999);
        if (income <= limit) {
          card.classList.add('matched');
          card.classList.remove('dimmed');
          matchedCount += 1;
        } else {
          card.classList.remove('matched');
          card.classList.add('dimmed');
        }
      });
      var note = '현재 조건(만 ' + age + '세, 중위소득 ' + income + '% 이하 구간) 기준 총 ' + cards.length + '건 중 ' + matchedCount + '건이 우선 검토 대상입니다.';
      outEl.textContent = note;
    }
    [incomeEl, ageEl].forEach(function (el) { el.addEventListener('input', update); });
    update();
  });
})();
"""
    (assets_dir / "app.js").write_text(
        js
        + "\n"
        + EXTRA_WIDGET_JS
        + "\n"
        + TOOLS_JS
        + "\n"
        + PUBLIC_HUBS_JS
        + "\n"
        + MEGA_EXPANSION_JS
        + "\n"
        + ULTRA_EXPANSION_JS,
        encoding="utf-8",
    )


def _build_product_table(products: list[FinancialProduct], rate_col_label: str) -> str:
    rows = []
    for p in products:
        rows.append(
            f"<tr>"
            f"<td><strong>{_esc(p.bank_name)}</strong></td>"
            f"<td>{_esc(p.product_name)}</td>"
            f"<td><span class='rate-badge'>{p.base_rate_pct:.2f}%</span></td>"
            f"<td><strong>{p.max_rate_pct:.2f}%</strong></td>"
            f"<td>{_esc(p.special_condition)}</td>"
            f"</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>금융회사</th><th>상품명</th>"
        f"<th>{_esc(rate_col_label)}</th><th>최고/상단 금리</th><th>우대·주요 조건</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _faq_section(faqs: list[tuple[str, str]]) -> tuple[str, dict[str, Any]]:
    items_html = []
    ld_entities = []
    for q, a in faqs:
        items_html.append(f'<div class="faq-item"><h3>Q. {_esc(q)}</h3><p>{_esc(a)}</p></div>')
        ld_entities.append(
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
        )
    html_block = f'<section class="card"><h2>자주 묻는 질문 (FAQ)</h2>{"".join(items_html)}</section>'
    ld_obj = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ld_entities}
    return html_block, ld_obj


def _infer_max_income_pct(eligibility: str) -> int:
    if "60%" in eligibility:
        return 60
    if "100%" in eligibility:
        return 100
    if "150%" in eligibility:
        return 150
    return 999


def generate_site(
    cfg: SiteConfig,
    products: list[FinancialProduct],
    subsidies: list[SubsidyProgram],
    *,
    is_sample_data: bool = False,
) -> list[GeneratedPage]:
    """Generate the full programmatic SEO static site into cfg.dist_dir."""
    dist = cfg.dist_dir
    dist.mkdir(parents=True, exist_ok=True)
    _write_assets(dist)

    deposits = sorted(
        [p for p in products if p.product_type == "deposit"],
        key=lambda x: x.max_rate_pct,
        reverse=True,
    )
    savings = sorted(
        [p for p in products if p.product_type == "saving"],
        key=lambda x: x.max_rate_pct,
        reverse=True,
    )
    mortgages = sorted(
        [p for p in products if p.product_type == "mortgage"],
        key=lambda x: x.base_rate_pct,
    )
    jeonses = sorted(
        [p for p in products if p.product_type == "jeonse"],
        key=lambda x: x.base_rate_pct,
    )

    best_deposit_rate = deposits[0].max_rate_pct if deposits else 3.25
    best_saving_rate = savings[0].max_rate_pct if savings else 4.30
    best_mortgage_rate = mortgages[0].base_rate_pct if mortgages else 3.72
    best_jeonse_rate = jeonses[0].base_rate_pct if jeonses else 3.45

    pages: list[GeneratedPage] = []

    # 1. 정기예금 pSEO 매트릭스 (4 금액 × 3 기간 = 12페이지)
    deposit_dir = dist / "deposit"
    deposit_dir.mkdir(parents=True, exist_ok=True)
    deposit_amounts = [10_000_000, 30_000_000, 50_000_000, 100_000_000]
    deposit_terms = [6, 12, 24]
    deposit_links: list[tuple[str, str]] = []
    for amt in deposit_amounts:
        for term in deposit_terms:
            slug = f"deposit-{amt // 10_000}man-{term}m.html"
            deposit_links.append((f"{_fmt_manwon(amt)} {term}개월 예금 이자", f"deposit/{slug}"))

    for amt in deposit_amounts:
        for term in deposit_terms:
            slug = f"deposit-{amt // 10_000}man-{term}m.html"
            rel_path = f"deposit/{slug}"
            url = f"{cfg.site_url}/{rel_path}"
            res = calculate_deposit(amt, term, best_deposit_rate, "general")
            title = f"정기예금 {_fmt_manwon(amt)} {term}개월 세후 이자 계산기 & 2026 은행별 금리 비교"
            desc = (
                f"정기예금 {_fmt_manwon(amt)}을 연 {best_deposit_rate:.2f}%로 {term}개월 예치 시 "
                f"세후 이자 {_fmt_krw(res.net_interest_krw)}, 만기 수령액 {_fmt_krw(res.maturity_amount_krw)}. "
                f"금융감독원 공시 기반 실시간 계산기."
            )
            related = "".join(
                f'<a class="link-pill" href="../{_esc(href)}">{_esc(label)}</a>'
                for label, href in deposit_links
                if href != rel_path
            )
            faq_html, faq_ld = _faq_section(
                [
                    (
                        f"정기예금 {_fmt_manwon(amt)} {term}개월 이자소득세는 얼마인가요?",
                        f"일반과세(15.4%) 기준 연 {best_deposit_rate:.2f}% 적용 시 세전 이자는 {_fmt_krw(res.gross_interest_krw)}, "
                        f"이자소득세는 {_fmt_krw(res.tax_krw)}이며 실수령 세후 이자는 {_fmt_krw(res.net_interest_krw)}입니다.",
                    ),
                    (
                        "세금우대나 비과세 혜택을 받으면 얼마나 유리한가요?",
                        "상호금융 조합원 저율과세 또는 비과세종합저축 대상자는 이자소득세 15.4%를 크게 줄일 수 있어 "
                        "위 계산기의 과세 유형을 변경해 즉시 비교해 보실 수 있습니다.",
                    ),
                ]
            )
            body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#deposit-hub">정기예금 계산기</a> › {_esc(_fmt_manwon(amt))} {term}개월</nav>
<h1>{_esc(title)}</h1>
<p class="lead">금융감독원 금융상품한눈에 공시 금리(최고 연 {best_deposit_rate:.2f}%)를 반영한 실시간 정기예금 세후 이자 계산기입니다. 금액·기간·금리·과세 유형을 직접 조정해 보세요.</p>

{_adsense_slot(cfg, "deposit-top")}

<section class="card" data-widget="deposit-calc">
  <h2>실시간 정기예금 세후 이자 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>예치 원금 (원)</label><input type="number" name="principal" value="{amt}" step="1000000"></div>
    <div class="field"><label>예치 기간 (개월)</label><input type="number" name="months" value="{term}" min="1" max="60"></div>
    <div class="field"><label>연 이자율 (%)</label><input type="number" name="rate" value="{best_deposit_rate:.2f}" step="0.05"></div>
    <div class="field"><label>과세 유형</label>
      <select name="tax">
        <option value="0.154" selected>일반과세 (15.4%)</option>
        <option value="0.095">세금우대 (9.5%)</option>
        <option value="0">비과세 (0%)</option>
      </select>
    </div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">세전 이자</div><div class="metric-value" data-out="gross">{_fmt_krw(res.gross_interest_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">이자소득세</div><div class="metric-value" data-out="tax">{_fmt_krw(res.tax_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">세후 실수령 이자</div><div class="metric-value" data-out="net">{_fmt_krw(res.net_interest_krw)}</div></div>
    <div class="metric-box highlight"><div class="metric-label">만기 실수령액</div><div class="metric-value" data-out="maturity">{_fmt_krw(res.maturity_amount_krw)}</div></div>
  </div>
</section>

<section class="card">
  <h2>2026 시중은행·인터넷은행 정기예금 금리 비교표</h2>
  {_build_product_table(deposits, "기본 금리")}
</section>

{_affiliate_box(
    f"{_fmt_manwon(amt)} 목돈 굴리기 — 특판 예금 & 파킹통장 금리 한눈에 비교",
    "우대조건 없이 높은 금리를 주는 비대면 특판 예금과 ISA 절세 계좌 혜택을 비교해 보세요.",
    "최신 고금리 예금·파킹통장 확인하기",
    cfg.affiliate_deposit_url,
)}

{_adsense_slot(cfg, "deposit-mid")}
{faq_html}

<section class="card">
  <h2>다른 금액·기간 정기예금 계산기</h2>
  <div class="link-grid">{related}</div>
</section>
"""
            ld = [
                {
                    "@context": "https://schema.org",
                    "@type": "WebApplication",
                    "name": title,
                    "url": url,
                    "applicationCategory": "FinanceApplication",
                    "operatingSystem": "All",
                },
                faq_ld,
            ]
            (dist / rel_path).write_text(
                _base_layout(
                    cfg,
                    title=title,
                    description=desc,
                    canonical_url=url,
                    body_html=body,
                    json_ld_objects=ld,
                    asset_prefix="../",
                    is_sample_data=is_sample_data,
                ),
                encoding="utf-8",
            )
            pages.append(GeneratedPage(rel_path, url, title, desc, "deposit"))

    # 2. 적금 pSEO 매트릭스 (4 월납입 × 3 기간 = 12페이지)
    saving_dir = dist / "saving"
    saving_dir.mkdir(parents=True, exist_ok=True)
    saving_monthly = [300_000, 500_000, 1_000_000, 2_000_000]
    saving_terms = [12, 24, 36]
    saving_links: list[tuple[str, str]] = []
    for mon in saving_monthly:
        for term in saving_terms:
            slug = f"saving-{mon // 10_000}man-{term}m.html"
            saving_links.append((f"월 {_fmt_manwon(mon)} {term}개월 적금", f"saving/{slug}"))

    for mon in saving_monthly:
        for term in saving_terms:
            slug = f"saving-{mon // 10_000}man-{term}m.html"
            rel_path = f"saving/{slug}"
            url = f"{cfg.site_url}/{rel_path}"
            res = calculate_saving(mon, term, best_saving_rate, "general")
            title = f"적금 월 {_fmt_manwon(mon)} {term}개월 만기 수령액 계산기 & 2026 고금리 적금 비교"
            desc = (
                f"매월 {_fmt_manwon(mon)}씩 {term}개월 적금 납입 시(연 {best_saving_rate:.2f}%) "
                f"원금 {_fmt_krw(res.total_principal_krw)}, 세후 이자 {_fmt_krw(res.net_interest_krw)}, "
                f"만기 수령액 {_fmt_krw(res.maturity_amount_krw)}."
            )
            related = "".join(
                f'<a class="link-pill" href="../{_esc(href)}">{_esc(label)}</a>'
                for label, href in saving_links
                if href != rel_path
            )
            faq_html, faq_ld = _faq_section(
                [
                    (
                        f"월 {_fmt_manwon(mon)} {term}개월 적금 이자가 예금보다 적게 느껴지는 이유는?",
                        "적금은 매달 나눠서 입금하므로 첫 달 납입금만 전체 기간 이자가 붙고, 마지막 달 납입금은 1개월치 이자만 적용되는 구조(평균 예치기간 약 절반)이기 때문입니다.",
                    ),
                    (
                        "고금리 적금 우대금리 조건을 놓치지 않으려면?",
                        "급여이체, 자동이체 횟수, 체크카드 실적 등 우대조건 달성 난이도를 반드시 비교하고 기본금리가 높은 상품을 우선 선택하는 것이 유리합니다.",
                    ),
                ]
            )
            body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#saving-hub">적금 계산기</a> › 월 {_esc(_fmt_manwon(mon))} {term}개월</nav>
<h1>{_esc(title)}</h1>
<p class="lead">정액적립식 단리 기준으로 월 {_esc(_fmt_manwon(mon))}씩 {term}개월 저축 시 세후 만기 수령액을 즉시 계산하고 은행별 최신 적금 금리를 비교합니다.</p>

{_adsense_slot(cfg, "saving-top")}

<section class="card" data-widget="saving-calc">
  <h2>실시간 적금 만기 수령액 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>월 납입액 (원)</label><input type="number" name="monthly" value="{mon}" step="50000"></div>
    <div class="field"><label>적립 기간 (개월)</label><input type="number" name="months" value="{term}" min="3" max="60"></div>
    <div class="field"><label>연 이자율 (%)</label><input type="number" name="rate" value="{best_saving_rate:.2f}" step="0.1"></div>
    <div class="field"><label>과세 유형</label>
      <select name="tax">
        <option value="0.154" selected>일반과세 (15.4%)</option>
        <option value="0.095">세금우대 (9.5%)</option>
        <option value="0">비과세 (0%)</option>
      </select>
    </div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">총 납입 원금</div><div class="metric-value" data-out="principal">{_fmt_krw(res.total_principal_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">이자소득세</div><div class="metric-value" data-out="tax">{_fmt_krw(res.tax_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">세후 이자</div><div class="metric-value" data-out="net">{_fmt_krw(res.net_interest_krw)}</div></div>
    <div class="metric-box highlight"><div class="metric-label">만기 실수령액</div><div class="metric-value" data-out="maturity">{_fmt_krw(res.maturity_amount_krw)}</div></div>
  </div>
</section>

<section class="card">
  <h2>2026 은행별 고금리 적금 비교표</h2>
  {_build_product_table(savings, "기본 금리")}
</section>

{_affiliate_box(
    "적금 만기 목돈 + 청년·직장인 절세 통장 비교",
    "일반과세 15.4% 대신 비과세 혜택을 챙길 수 있는 정책 저축·ISA 상품 조건을 확인하세요.",
    "절세 적금·ISA 혜택 비교하기",
    cfg.affiliate_deposit_url,
)}

{_adsense_slot(cfg, "saving-mid")}
{faq_html}

<section class="card">
  <h2>다른 월납입·기간 적금 계산기</h2>
  <div class="link-grid">{related}</div>
</section>
"""
            ld = [
                {
                    "@context": "https://schema.org",
                    "@type": "WebApplication",
                    "name": title,
                    "url": url,
                    "applicationCategory": "FinanceApplication",
                    "operatingSystem": "All",
                },
                faq_ld,
            ]
            (dist / rel_path).write_text(
                _base_layout(
                    cfg,
                    title=title,
                    description=desc,
                    canonical_url=url,
                    body_html=body,
                    json_ld_objects=ld,
                    asset_prefix="../",
                    is_sample_data=is_sample_data,
                ),
                encoding="utf-8",
            )
            pages.append(GeneratedPage(rel_path, url, title, desc, "saving"))

    # 3. 대출 pSEO 매트릭스 (주택담보대출 8페이지 + 전세자금대출 8페이지 = 16페이지)
    loan_dir = dist / "loan"
    loan_dir.mkdir(parents=True, exist_ok=True)
    loan_specs = []
    for amt in (200_000_000, 300_000_000, 500_000_000, 700_000_000):
        for yrs in (20, 30):
            loan_specs.append(("mortgage", "주택담보대출", amt, yrs * 12, yrs, best_mortgage_rate, "equal_installment", mortgages))
    for amt in (100_000_000, 200_000_000, 300_000_000, 400_000_000):
        for yrs in (2, 4):
            loan_specs.append(("jeonse", "전세자금대출", amt, yrs * 12, yrs, best_jeonse_rate, "bullet", jeonses))

    loan_links = [
        (f"{label} {_fmt_manwon(amt)} {yrs}년", f"loan/{kind}-{amt // 100_000_000}eok-{yrs}y.html")
        for kind, label, amt, _, yrs, _, _, _ in loan_specs
    ]

    for kind, label, amt, months, yrs, rate, default_repay, prods in loan_specs:
        slug = f"{kind}-{amt // 100_000_000}eok-{yrs}y.html"
        rel_path = f"loan/{slug}"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_loan(amt, months, rate, default_repay)
        title = f"{label} {_fmt_manwon(amt)} {yrs}년 월 상환액·이자 계산기 & 2026 최저금리 비교"
        desc = (
            f"{label} {_fmt_manwon(amt)}을 연 {rate:.2f}%로 {yrs}년 이용 시 "
            f"첫 달 납입액 {_fmt_krw(res.first_month_payment_krw)}, 총 대출이자 {_fmt_krw(res.total_interest_krw)}. "
            f"원리금균등·원금균등·만기일시 실시간 비교."
        )
        related = "".join(
            f'<a class="link-pill" href="../{_esc(href)}">{_esc(lbl)}</a>'
            for lbl, href in loan_links
            if href != rel_path
        )
        sel_ei = "selected" if default_repay == "equal_installment" else ""
        sel_ep = "selected" if default_repay == "equal_principal" else ""
        sel_bu = "selected" if default_repay == "bullet" else ""
        faq_html, faq_ld = _faq_section(
            [
                (
                    f"{label} {_fmt_manwon(amt)} 금리가 0.5%p 낮아지면 얼마나 아낄 수 있나요?",
                    "대출 금액과 기간이 길수록 0.5%p 금리 차이가 수백만~수천만 원의 총 이자 절감으로 이어집니다. 위 계산기에서 금리를 0.5%p 낮춰 즉시 확인해 보세요.",
                ),
                (
                    "원리금균등과 원금균등 중 어떤 상환 방식이 유리한가요?",
                    "총 이자 부담은 원금균등상환이 더 적지만 초기 월 상환액이 높습니다. 매달 일정한 현금흐름을 원하신다면 원리금균등상환, 전세대출은 주로 만기일시상환을 선택합니다.",
                ),
            ]
        )
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#loan-hub">대출 계산기</a> › {_esc(label)} {_esc(_fmt_manwon(amt))} {yrs}년</nav>
<h1>{_esc(title)}</h1>
<p class="lead">금융감독원 공시 최저금리(연 {rate:.2f}%) 기준으로 {_esc(label)} {_esc(_fmt_manwon(amt))} {yrs}년 상환 시 월 부담액과 총 이자를 실시간 계산합니다.</p>

{_adsense_slot(cfg, "loan-top")}

<section class="card" data-widget="loan-calc">
  <h2>실시간 {_esc(label)} 이자·상환액 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>대출 원금 (원)</label><input type="number" name="principal" value="{amt}" step="10000000"></div>
    <div class="field"><label>대출 기간 (개월)</label><input type="number" name="months" value="{months}" min="6" max="480"></div>
    <div class="field"><label>연 대출금리 (%)</label><input type="number" name="rate" value="{rate:.2f}" step="0.05"></div>
    <div class="field"><label>상환 방식</label>
      <select name="repayment">
        <option value="equal_installment" {sel_ei}>원리금균등상환</option>
        <option value="equal_principal" {sel_ep}>원금균등상환</option>
        <option value="bullet" {sel_bu}>만기일시상환</option>
      </select>
    </div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">첫 달 상환액 (원금+이자)</div><div class="metric-value" data-out="monthly">{_fmt_krw(res.first_month_payment_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">총 대출 이자</div><div class="metric-value" data-out="interest">{_fmt_krw(res.total_interest_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">총 상환 금액</div><div class="metric-value" data-out="total">{_fmt_krw(res.total_repayment_krw)}</div></div>
  </div>
</section>

<section class="card">
  <h2>2026 은행별 {_esc(label)} 금리 비교표</h2>
  {_build_product_table(prods, "최저 금리")}
</section>

{_affiliate_box(
    f"{label} 갈아타기(대환) — 내 조건 최저금리 1분 조회",
    "신용점수 영향 없이 1금융권·인터넷은행 대환대출 가능 한도와 우대금리를 한 번에 비교하세요.",
    "내 최저금리 무료 비교하기",
    cfg.affiliate_loan_url,
)}

{_adsense_slot(cfg, "loan-mid")}
{faq_html}

<section class="card">
  <h2>다른 대출 금액·기간 계산기</h2>
  <div class="link-grid">{related}</div>
</section>
"""
        ld = [
            {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": title,
                "url": url,
                "applicationCategory": "FinanceApplication",
                "operatingSystem": "All",
            },
            faq_ld,
        ]
        (dist / rel_path).write_text(
            _base_layout(
                cfg,
                title=title,
                description=desc,
                canonical_url=url,
                body_html=body,
                json_ld_objects=ld,
                asset_prefix="../",
                is_sample_data=is_sample_data,
            ),
            encoding="utf-8",
        )
        pages.append(GeneratedPage(rel_path, url, title, desc, "loan"))

    # 4. 보조금24 지역 × 대상 pSEO 매트릭스 (5 지역 × 4 대상 = 20페이지)
    subsidy_dir = dist / "subsidy"
    subsidy_dir.mkdir(parents=True, exist_ok=True)
    regions = [("all", "전국"), ("seoul", "서울"), ("gyeonggi", "경기"), ("incheon", "인천"), ("busan", "부산")]
    groups = [("youth", "청년"), ("family", "신혼부부·출산"), ("smallbiz", "소상공인"), ("living", "주거·생활")]
    subsidy_links = [
        (f"{r_kr} {g_kr} 지원금", f"subsidy/{r_slug}-{g_slug}.html")
        for r_slug, r_kr in regions
        for g_slug, g_kr in groups
    ]

    for r_slug, r_kr in regions:
        for g_slug, g_kr in groups:
            rel_path = f"subsidy/{r_slug}-{g_slug}.html"
            url = f"{cfg.site_url}/{rel_path}"
            matched = [
                s
                for s in subsidies
                if s.target_group == g_kr and (r_kr == "전국" or s.region in {r_kr, "전국"})
            ]
            if not matched:
                matched = [s for s in subsidies if s.region in {r_kr, "전국"}][:3]
            title = f"2026 {r_kr} {g_kr} 정부지원금·보조금24 자격 자가진단 & 신청 방법 총정리"
            desc = (
                f"{r_kr} 거주 {g_kr} 대상이 신청할 수 있는 2026년 정부·지자체 보조금 {len(matched)}종 "
                f"자격 요건, 지원 금액, 온라인 신청 링크를 한눈에 확인하세요."
            )
            cards_html = "".join(
                f"""<article class="subsidy-item" data-subsidy-card="1" data-max-income="{_infer_max_income_pct(s.eligibility)}">
  <div><span class="tag">{_esc(s.region)}</span><span class="tag">{_esc(s.target_group)}</span><span class="tag">{_esc(s.agency)}</span></div>
  <h3>{_esc(s.title)}</h3>
  <p><strong>지원 내용:</strong> {_esc(s.support_summary)}</p>
  <p><strong>지원 대상:</strong> {_esc(s.eligibility)}</p>
  <p><strong>신청 방법:</strong> {_esc(s.apply_method)} — <a href="{_esc(s.apply_url)}" rel="noopener noreferrer" target="_blank">공식 신청 사이트 바로가기 ↗</a></p>
</article>"""
                for s in matched
            )
            related = "".join(
                f'<a class="link-pill" href="../{_esc(href)}">{_esc(lbl)}</a>'
                for lbl, href in subsidy_links
                if href != rel_path
            )
            faq_html, faq_ld = _faq_section(
                [
                    (
                        f"{r_kr} {g_kr} 정부지원금은 중복 신청이 가능한가요?",
                        "중앙부처 사업과 지자체 자체 사업은 목적이 다르거나 보완적일 경우 중복 수혜가 가능한 경우가 많습니다. 다만 유사 성격의 현금성 지원금은 중복지원이 제한될 수 있으므로 공고문을 확인하세요.",
                    ),
                    (
                        "보조금24 공식 조회는 어디서 하나요?",
                        "정부24(gov.kr) 로그인 후 '보조금24' 메뉴에서 본인 및 세대원 정보를 연동하면 실시간 맞춤 혜택을 확인할 수 있습니다.",
                    ),
                ]
            )
            body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#subsidy-hub">보조금24 진단</a> › {_esc(r_kr)} {_esc(g_kr)}</nav>
<h1>{_esc(title)}</h1>
<p class="lead">행정안전부 보조금24 공공서비스 데이터를 기반으로 {_esc(r_kr)} 지역 {_esc(g_kr)} 대상 핵심 지원금 {len(matched)}종을 정리했습니다.</p>

{_adsense_slot(cfg, "subsidy-top")}

<section class="card" data-widget="subsidy-checker">
  <h2>30초 {_esc(r_kr)} {_esc(g_kr)} 보조금 자격 자가진단</h2>
  <div class="calc-grid">
    <div class="field"><label>만 나이 (세)</label><input type="number" name="age" value="30" min="0" max="100"></div>
    <div class="field"><label>가구 기준 중위소득 구간 (%)</label>
      <select name="income">
        <option value="60">중위소득 60% 이하</option>
        <option value="100" selected>중위소득 100% 이하</option>
        <option value="150">중위소득 150% 이하</option>
        <option value="200">중위소득 150% 초과 (보편지원 중심)</option>
      </select>
    </div>
  </div>
  <div class="metric-box highlight" style="margin-top:14px;">
    <div class="metric-label">진단 결과 요약</div>
    <div class="metric-value" style="font-size:1rem;font-weight:700;" data-out="match-summary">조건을 선택하면 맞춤 혜택 검토 결과가 표시됩니다.</div>
  </div>
  <div style="margin-top:18px;">
    {cards_html}
  </div>
</section>

{_affiliate_box(
    f"{r_kr} {g_kr} 생활비 절감 — 통신비·렌탈·보험 고정지출 체크",
    "정부지원금 신청과 함께 매달 나가는 인터넷·가전렌탈·보험 고정비를 점검해 추가 절감 혜택을 확인하세요.",
    "고정지출 절감 혜택 확인하기",
    cfg.affiliate_subsidy_url,
)}

{_adsense_slot(cfg, "subsidy-mid")}
{faq_html}

<section class="card">
  <h2>다른 지역·대상 보조금24 진단기</h2>
  <div class="link-grid">{related}</div>
</section>
"""
            ld = [
                {
                    "@context": "https://schema.org",
                    "@type": "WebApplication",
                    "name": title,
                    "url": url,
                    "applicationCategory": "GovernmentService",
                    "operatingSystem": "All",
                },
                faq_ld,
            ]
            (dist / rel_path).write_text(
                _base_layout(
                    cfg,
                    title=title,
                    description=desc,
                    canonical_url=url,
                    body_html=body,
                    json_ld_objects=ld,
                    asset_prefix="../",
                    is_sample_data=is_sample_data,
                ),
                encoding="utf-8",
            )
            pages.append(GeneratedPage(rel_path, url, title, desc, "subsidy"))

    # 4.5. 추가 초고CPC 한국어(연봉·퇴직금·부동산·자동차) + 글로벌 USD(/en/) 계산기 120페이지
    extra_pages, extra_hubs = generate_extra_pages(
        cfg,
        dist,
        is_sample_data=is_sample_data,
        base_layout_fn=_base_layout,
        adsense_slot_fn=_adsense_slot,
        affiliate_box_fn=_affiliate_box,
        faq_section_fn=_faq_section,
        page_cls=GeneratedPage,
        esc_fn=_esc,
        fmt_krw_fn=_fmt_krw,
        fmt_manwon_fn=_fmt_manwon,
    )
    pages.extend(extra_pages)

    # 4.6. 제2 수익 파이프라인: 비계산기 브라우저 로컬 웹 유틸리티 스튜디오 (한/영 24페이지)
    tool_pages, tool_links_kr, tool_links_en = generate_web_tool_pages(
        cfg,
        dist,
        is_sample_data=is_sample_data,
        base_layout_fn=_base_layout,
        adsense_slot_fn=_adsense_slot,
        faq_section_fn=_faq_section,
        page_cls=GeneratedPage,
        esc_fn=_esc,
    )
    pages.extend(tool_pages)

    # 4.7. 4갈래 실시간 공공데이터 허브 (국토부 아파트 실거래가 · 청약홈 · K-Startup · 심평원 비급여 = 30페이지)
    pub_pages, pub_hubs, _pub_sources = generate_public_hub_pages(
        cfg,
        dist,
        is_sample_data=is_sample_data,
        base_layout_fn=_base_layout,
        adsense_slot_fn=_adsense_slot,
        affiliate_box_fn=_affiliate_box,
        faq_section_fn=_faq_section,
        page_cls=GeneratedPage,
        esc_fn=_esc,
    )
    pages.extend(pub_pages)

    # 4.8. 메가 확장: 한국 세금(증여·종소세·양도세) + 생활금융 + 글로벌 USD 프로 (+120p)
    mega_pages, mega_hubs = generate_mega_expansion_pages(
        cfg,
        dist,
        is_sample_data=is_sample_data,
        base_layout_fn=_base_layout,
        adsense_slot_fn=_adsense_slot,
        affiliate_box_fn=_affiliate_box,
        faq_section_fn=_faq_section,
        page_cls=GeneratedPage,
        esc_fn=_esc,
        fmt_manwon_fn=_fmt_manwon,
    )
    pages.extend(mega_pages)

    # 4.9. 울트라 확장: 투자·복리·물타기 + 평수·마진·건강(BMI/TDEE) (+150p -> 총 500p+)
    ultra_pages, ultra_hubs = generate_ultra_expansion_pages(
        cfg,
        dist,
        is_sample_data=is_sample_data,
        base_layout_fn=_base_layout,
        adsense_slot_fn=_adsense_slot,
        affiliate_box_fn=_affiliate_box,
        faq_section_fn=_faq_section,
        page_cls=GeneratedPage,
        esc_fn=_esc,
        fmt_manwon_fn=_fmt_manwon,
    )
    pages.extend(ultra_pages)

    # 5. 필수 신뢰 페이지 (privacy.html, disclaimer.html — 애드센스 심사 통과 필수)
    for rel_path, p_title, p_desc, p_body in [
        (
            "privacy.html",
            f"개인정보처리방침 | {cfg.site_name}",
            f"{cfg.site_name}의 개인정보 처리방침 및 쿠키·광고(Google AdSense) 운영 안내입니다.",
            f"""<h1>개인정보처리방침</h1>
<section class="card">
  <p>{_esc(cfg.site_name)}은(는) 이용자의 개인정보를 별도 서버에 수집·저장하지 않으며, 모든 금융 계산기 및 보조금 자가진단 입력값은 이용자의 브라우저 내에서만 즉시 처리됩니다.</p>
  <h2>1. 쿠키 및 맞춤형 광고(Google AdSense)</h2>
  <p>본 사이트는 Google AdSense 등 제3자 광고 네트워크를 통해 광고를 게재할 수 있으며, 광고 사업자는 이용자의 관심사에 기반한 광고를 제공하기 위해 쿠키를 사용할 수 있습니다. 이용자는 Google 광고 설정에서 맞춤형 광고를 언제든지 거부할 수 있습니다.</p>
  <h2>2. 제휴 마케팅 고지</h2>
  <p>본 사이트 내 일부 링크는 제휴(CPA/어필리에이트) 링크이며, 해당 링크를 통한 신청·가입 시 운영자에게 소정의 수수료가 지급될 수 있습니다.</p>
  <h2>3. 문의처</h2>
  <p>이메일: {_esc(cfg.contact_email)}</p>
</section>""",
        ),
        (
            "disclaimer.html",
            f"면책고지 및 공공데이터 출처 | {cfg.site_name}",
            f"{cfg.site_name}의 금융·정부지원금 데이터 공식 출처 및 법적 면책고지 안내입니다.",
            f"""<h1>면책고지 및 공공데이터 출처</h1>
<section class="card">
  <h2>1. 공식 데이터 출처</h2>
  <ul>
    <li>금융상품 금리 정보: 금융감독원 「금융상품한눈에」 공공 오픈 API</li>
    <li>정부·지자체 지원금 정보: 행정안전부 「보조금24」 대한민국 공공서비스 정보 오픈 API</li>
  </ul>
  <h2>2. 면책 조항 (YMYL 안내)</h2>
  <p>본 사이트에서 제공하는 계산 결과, 금리 비교표, 보조금 요약 정보는 일반적인 참고용이며, 금융상품 계약 또는 정부지원금 신청에 대한 법적·세무적·재무적 자문을 구성하지 않습니다. 실제 금리·세율·지원 자격은 금융기관 및 관할 행정기관의 최신 공식 공고를 반드시 확인하시기 바랍니다.</p>
</section>""",
        ),
    ]:
        url = f"{cfg.site_url}/{rel_path}"
        (dist / rel_path).write_text(
            _base_layout(
                cfg,
                title=p_title,
                description=p_desc,
                canonical_url=url,
                body_html=p_body,
                json_ld_objects=[],
                asset_prefix="",
                is_sample_data=is_sample_data,
            ),
            encoding="utf-8",
        )
        pages.append(GeneratedPage(rel_path, url, p_title, p_desc, "legal"))

    # 6. 메인 허브 페이지 (index.html)
    index_body = f"""
<section class="card">
  <h1>{_esc(cfg.site_name)}</h1>
  <p class="lead">{_esc(cfg.site_description)} — 금융감독원·행정안전부 공공데이터를 매일 자동 반영합니다.</p>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">최고 정기예금 금리</div><div class="metric-value">연 {best_deposit_rate:.2f}%</div></div>
    <div class="metric-box"><div class="metric-label">최고 적금 금리</div><div class="metric-value">연 {best_saving_rate:.2f}%</div></div>
    <div class="metric-box"><div class="metric-label">주담대 최저 금리</div><div class="metric-value">연 {best_mortgage_rate:.2f}%</div></div>
    <div class="metric-box highlight"><div class="metric-label">자동 생성 SEO 도구</div><div class="metric-value">{len(pages) + 1}개 페이지</div></div>
  </div>
  <input id="hub-search" class="hero-search" type="search" placeholder="🔍 207개 계산기·보조금·웹 유틸리티 즉시 검색 (예: 연봉, 주담대, WebP, JSON, Mortgage)..." aria-label="도구 검색">
</section>

{_adsense_slot(cfg, "home-top")}

{_affiliate_box(
    "오늘의 쿠팡 골드박스 · 로켓배송 생활비 절약 특가 모음",
    "금융·세금·보조금 계산과 함께 매일 업데이트되는 생필품·가전·디지털 로켓배송 초특가 할인을 확인하세요.",
    "오늘의 쿠팡 골드박스 초특가 확인하기",
    cfg.affiliate_subsidy_url,
)}

<section class="card" id="deposit-hub">
  <h2>정기예금 금액·기간별 세후 이자 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in deposit_links)}</div>
</section>

<section class="card" id="saving-hub">
  <h2>적금 월납입·기간별 만기 수령액 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in saving_links)}</div>
</section>

<section class="card" id="loan-hub">
  <h2>주택담보대출 · 전세자금대출 월 상환액 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in loan_links)}</div>
</section>

<section class="card" id="subsidy-hub">
  <h2>2026 지역·대상별 보조금24 자격 자가진단기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in subsidy_links)}</div>
</section>

<section class="card" id="salary-hub">
  <h2>2026 연봉 실수령액 계산기 (4대보험·세금)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in extra_hubs["salary"])}</div>
</section>

<section class="card" id="severance-hub">
  <h2>퇴직금 · 실업급여 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in extra_hubs["severance"])}</div>
</section>

<section class="card" id="realestate-hub">
  <h2>부동산 취득세 · 중개보수(복비) 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in extra_hubs["realestate"])}</div>
</section>

<section class="card" id="auto-hub">
  <h2>자동차 할부 · 취등록세 계산기</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in extra_hubs["auto"])}</div>
</section>

<section class="card" id="en-hub">
  <h2>Global USD Finance Calculators (US Mortgage &amp; Compound Interest)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in extra_hubs["en_global"])}</div>
</section>

<section class="card" id="tools-hub">
  <h2>무료 브라우저 웹 유틸리티 &amp; 파일 변환 스튜디오 (서버 전송 없음)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in tool_links_kr)}</div>
</section>

<section class="card" id="en-tools-hub">
  <h2>Free Online Web Utilities &amp; Converters (Global English Studio)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in tool_links_en)}</div>
</section>

<section class="card" id="apt-hub">
  <h2>2026 지역별 아파트 매매 실거래가 실시간 조회 (국토교통부 API)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in pub_hubs["apt"])}</div>
</section>

<section class="card" id="cheongyak-hub">
  <h2>2026 전국 청약홈 분양 일정 &amp; 84점 청약가점 계산기 (한국부동산원 API)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in pub_hubs["cheongyak"])}</div>
</section>

<section class="card" id="startup-hub">
  <h2>2026 K-Startup 정부 창업·소상공인 지원사업 실시간 공고 (창업진흥원 API)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in pub_hubs["startup"])}</div>
</section>

<section class="card" id="medical-hub">
  <h2>2026 비급여 진료비 안내 &amp; 4세대 실손보험 환급액 계산기 (심평원 API)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in pub_hubs["medical"])}</div>
</section>

<section class="card" id="tax-hub">
  <h2>2026 증여세 · 프리랜서 3.3% 종소세 · 양도소득세 계산기 (40종)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in mega_hubs["tax"])}</div>
</section>

<section class="card" id="life-hub">
  <h2>국민연금 · 해외직구 관부가세 · 전월세 전환율 계산기 (36종)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in mega_hubs["life"])}</div>
</section>

<section class="card" id="invest-hub">
  <h2>적립식 복리(S&amp;P500·배당) · 주식 물타기 평단가 계산기 (50종)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in ultra_hubs["invest"])}</div>
</section>

<section class="card" id="convert-hub">
  <h2>아파트 평수(㎡) · 마진율 · BMI·칼로리(TDEE) 변환기 (100종)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in ultra_hubs["convert"])}</div>
</section>

<section class="card" id="en-pro-hub">
  <h2>Global USD Pro Calculators (US Auto Loan, Hourly Salary, SaaS LTV:CAC)</h2>
  <div class="link-grid">{"".join(f'<a class="link-pill" href="{_esc(href)}">{_esc(lbl)}</a>' for lbl, href in mega_hubs["en_pro"])}</div>
</section>
"""
    index_url = f"{cfg.site_url}/index.html"
    index_ld = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": cfg.site_name,
            "url": cfg.site_url,
            "description": cfg.site_description,
        }
    ]
    (dist / "index.html").write_text(
        _base_layout(
            cfg,
            title=f"{cfg.site_name} | 예적금·대출 이자 계산기 & 2026 보조금24",
            description=cfg.site_description,
            canonical_url=index_url,
            body_html=index_body,
            json_ld_objects=index_ld,
            asset_prefix="",
            is_sample_data=is_sample_data,
        ),
        encoding="utf-8",
    )
    pages.insert(0, GeneratedPage("index.html", index_url, cfg.site_name, cfg.site_description, "home"))

    # 7. SEO 기술 파일: sitemap.xml, robots.txt, ads.txt, rss.xml, IndexNow key
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sitemap_urls = "\n".join(
        f"  <url><loc>{_esc(p.url)}</loc><lastmod>{now_iso}</lastmod><changefreq>daily</changefreq></url>"
        for p in pages
    )
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap_urls}\n</urlset>\n",
        encoding="utf-8",
    )

    (dist / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {cfg.site_url}/sitemap.xml\n",
        encoding="utf-8",
    )

    if cfg.adsense_client_id:
        pub_id = cfg.adsense_client_id.replace("ca-", "")
        ads_txt = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    else:
        ads_txt = "# .env에 ADSENSE_CLIENT_ID 설정 후 자동 생성됩니다.\n"
    (dist / "ads.txt").write_text(ads_txt, encoding="utf-8")

    rss_items = "\n".join(
        f"    <item><title>{_esc(p.title)}</title><link>{_esc(p.url)}</link>"
        f"<description>{_esc(p.description)}</description></item>"
        for p in pages[:30]
    )
    (dist / "rss.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        f"  <title>{_esc(cfg.site_name)}</title>\n"
        f"  <link>{_esc(cfg.site_url)}</link>\n"
        f"  <description>{_esc(cfg.site_description)}</description>\n"
        f"{rss_items}\n</channel></rss>\n",
        encoding="utf-8",
    )

    if cfg.indexnow_key:
        (dist / f"{cfg.indexnow_key}.txt").write_text(cfg.indexnow_key, encoding="utf-8")

    # 8. 정적 검증 파일 및 AI 검색 인용 파일(llms.txt, llms-full.txt) 복사
    static_dir = cfg.dist_dir.parent / "static"
    if static_dir.exists() and static_dir.is_dir():
        for item in static_dir.iterdir():
            if item.is_file():
                (dist / item.name).write_bytes(item.read_bytes())

    # 9. Stage 3 Zero-Cost AI Referrer & First/Last-Touch Attribution Hook自动주입
    app_js_path = dist / "assets" / "app.js"
    if app_js_path.is_file():
        attr_js = """
;(function(){
  try {
    var ref = (document.referrer || '').toLowerCase();
    var params = new URLSearchParams(window.location.search);
    var ch = params.get('utm_source') || 'direct_or_organic';
    if (ref.indexOf('chatgpt.com') >= 0 || ref.indexOf('openai.com') >= 0) ch = 'ai_chatgpt_search';
    else if (ref.indexOf('perplexity.ai') >= 0) ch = 'ai_perplexity';
    else if (ref.indexOf('claude.ai') >= 0) ch = 'ai_claude';
    else if (ref.indexOf('gemini.google.com') >= 0) ch = 'ai_gemini';
    else if (ref.indexOf('search.naver.com') >= 0) ch = 'seo_naver';
    else if (ref.indexOf('google.') >= 0) ch = 'seo_google';
    if (!localStorage.getItem('bm_first_channel')) localStorage.setItem('bm_first_channel', ch);
    localStorage.setItem('bm_last_channel', ch);
    window.__BORING_ATTRIBUTION__ = {
      first_touch: localStorage.getItem('bm_first_channel'),
      last_touch: ch,
      hook_id: params.get('utm_content') || 'organic_aio'
    };
  } catch (e) {}
})();
"""
        app_js_path.write_text(app_js_path.read_text(encoding="utf-8") + attr_js, encoding="utf-8")

    return pages
