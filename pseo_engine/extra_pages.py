"""Extra high-CPC programmatic SEO page generators (KR Salary/Severance/RealEstate/Auto + Global EN USD)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pseo_engine.config import SiteConfig
from pseo_engine.extra_calculators import (
    calculate_kr_auto_finance,
    calculate_kr_realestate_cost,
    calculate_kr_salary,
    calculate_kr_severance,
    calculate_usd_compound,
    calculate_usd_mortgage,
)


EXTRA_WIDGET_JS = """
(function () {
  function fmtKrw(n) { return Math.round(n).toLocaleString('ko-KR') + '원'; }
  function fmtUsd(n) { return '$' + Math.round(n).toLocaleString('en-US'); }

  document.querySelectorAll('[data-widget="salary-calc"]').forEach(function (root) {
    var sEl = root.querySelector('[name="salary"]');
    var ntEl = root.querySelector('[name="nontax"]');
    function update() {
      var annual = Math.max(0, Number(sEl.value || 0));
      var nt = Math.max(0, Number(ntEl.value || 0));
      var gross = annual / 12;
      var taxable = Math.max(0, gross - nt);
      var np = Math.min(taxable, 6170000) * 0.045;
      var hi = taxable * 0.03545;
      var ltc = hi * 0.1295;
      var ei = taxable * 0.009;
      var at = taxable * 12;
      var estAnnual = at <= 15000000 ? at * 0.015 :
        at <= 45000000 ? 225000 + (at - 15000000) * 0.06 :
        at <= 88000000 ? 2025000 + (at - 45000000) * 0.145 :
        at <= 150000000 ? 8260000 + (at - 88000000) * 0.24 :
        23140000 + (at - 150000000) * 0.33;
      var inc = estAnnual / 12;
      var loc = inc * 0.1;
      var ded = np + hi + ltc + ei + inc + loc;
      root.querySelector('[data-out="gross"]').textContent = fmtKrw(gross);
      root.querySelector('[data-out="ded"]').textContent = fmtKrw(ded);
      root.querySelector('[data-out="net"]').textContent = fmtKrw(Math.max(0, gross - ded));
    }
    [sEl, ntEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="severance-calc"]').forEach(function (root) {
    var mEl = root.querySelector('[name="monthly"]');
    var yEl = root.querySelector('[name="years"]');
    function update() {
      var m = Math.max(0, Number(mEl.value || 0));
      var y = Math.max(1, Number(yEl.value || 1));
      var daily = (m * 3) / 91;
      var sev = daily * 30 * y;
      var dUnemp = Math.min(66000, Math.max(64192, daily * 0.6));
      var days = y < 1 ? 120 : y < 3 ? 150 : y < 5 ? 180 : y < 10 ? 210 : 240;
      root.querySelector('[data-out="sev"]').textContent = fmtKrw(sev);
      root.querySelector('[data-out="unemp"]').textContent = fmtKrw(dUnemp * days);
    }
    [mEl, yEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="realestate-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="price"]');
    var hEl = root.querySelector('[name="houses"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var h = Number(hEl.value || 1);
      var rate = h === 1 ? (p <= 600000000 ? 0.01 : p <= 900000000 ? ((p / 100000000) * (2 / 3) - 3) / 100 : 0.03) : (h === 2 ? 0.08 : 0.12);
      var acq = p * rate;
      var totalTax = acq * 1.1;
      var bRate = p < 200000000 ? 0.005 : p < 900000000 ? 0.004 : p < 1200000000 ? 0.005 : p < 1500000000 ? 0.006 : 0.007;
      var broker = p * bRate;
      root.querySelector('[data-out="tax"]').textContent = fmtKrw(totalTax);
      root.querySelector('[data-out="broker"]').textContent = fmtKrw(broker);
      root.querySelector('[data-out="total"]').textContent = fmtKrw(totalTax + broker);
    }
    [pEl, hEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="auto-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="price"]');
    var mEl = root.querySelector('[name="months"]');
    var rEl = root.querySelector('[name="rate"]');
    var dEl = root.querySelector('[name="down"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var m = Math.max(1, Number(mEl.value || 36));
      var mr = Math.max(0, Number(rEl.value || 0)) / 100 / 12;
      var down = p * (Math.max(0, Number(dEl.value || 0)) / 100);
      var loan = Math.max(0, p - down);
      var acq = (p / 1.1) * 0.07;
      var pmt = mr === 0 ? loan / m : loan * (mr * Math.pow(1 + mr, m)) / (Math.pow(1 + mr, m) - 1);
      root.querySelector('[data-out="acq"]').textContent = fmtKrw(acq);
      root.querySelector('[data-out="monthly"]').textContent = fmtKrw(pmt);
      root.querySelector('[data-out="interest"]').textContent = fmtKrw(Math.max(0, pmt * m - loan));
    }
    [pEl, mEl, rEl, dEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="usd-mortgage-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="principal"]');
    var yEl = root.querySelector('[name="years"]');
    var rEl = root.querySelector('[name="rate"]');
    function update() {
      var p = Math.max(0, Number(pEl.value || 0));
      var m = Math.max(12, Number(yEl.value || 30) * 12);
      var mr = Math.max(0, Number(rEl.value || 0)) / 100 / 12;
      var pmt = mr === 0 ? p / m : p * (mr * Math.pow(1 + mr, m)) / (Math.pow(1 + mr, m) - 1);
      root.querySelector('[data-out="monthly"]').textContent = fmtUsd(pmt);
      root.querySelector('[data-out="interest"]').textContent = fmtUsd(Math.max(0, pmt * m - p));
      root.querySelector('[data-out="total"]').textContent = fmtUsd(pmt * m);
    }
    [pEl, yEl, rEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  document.querySelectorAll('[data-widget="usd-compound-calc"]').forEach(function (root) {
    var iEl = root.querySelector('[name="initial"]');
    var cEl = root.querySelector('[name="monthly"]');
    var yEl = root.querySelector('[name="years"]');
    var rEl = root.querySelector('[name="rate"]');
    function update() {
      var init = Math.max(0, Number(iEl.value || 0));
      var mc = Math.max(0, Number(cEl.value || 0));
      var m = Math.max(12, Number(yEl.value || 20) * 12);
      var mr = Math.max(0.0001, Number(rEl.value || 8) / 100 / 12);
      var fv = init * Math.pow(1 + mr, m) + mc * ((Math.pow(1 + mr, m) - 1) / mr);
      var contrib = init + mc * m;
      root.querySelector('[data-out="fv"]').textContent = fmtUsd(fv);
      root.querySelector('[data-out="contrib"]').textContent = fmtUsd(contrib);
      root.querySelector('[data-out="growth"]').textContent = fmtUsd(Math.max(0, fv - contrib));
    }
    [iEl, cEl, yEl, rEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });
})();
"""


def generate_extra_pages(
    cfg: SiteConfig,
    dist: Path,
    *,
    is_sample_data: bool,
    base_layout_fn: Callable[..., str],
    adsense_slot_fn: Callable[[SiteConfig, str], str],
    affiliate_box_fn: Callable[[str, str, str, str], str],
    faq_section_fn: Callable[[list[tuple[str, str]]], tuple[str, dict[str, Any]]],
    page_cls: type,
    esc_fn: Callable[[Any], str],
    fmt_krw_fn: Callable[[int], str],
    fmt_manwon_fn: Callable[[int], str],
) -> tuple[list[Any], dict[str, list[tuple[str, str]]]]:
    """Generate 130 extra high-CPC KR & Global EN USD calculator pages."""
    pages: list[Any] = []
    hub_links: dict[str, list[tuple[str, str]]] = {
        "salary": [],
        "severance": [],
        "realestate": [],
        "auto": [],
        "en_global": [],
    }

    # 1. 2026 연봉 실수령액 계산기 (26페이지)
    sal_dir = dist / "salary"
    sal_dir.mkdir(parents=True, exist_ok=True)
    salaries = [
        24_000_000, 28_000_000, 30_000_000, 32_000_000, 35_000_000,
        38_000_000, 40_000_000, 42_000_000, 45_000_000, 48_000_000,
        50_000_000, 55_000_000, 60_000_000, 65_000_000, 70_000_000,
        75_000_000, 80_000_000, 85_000_000, 90_000_000, 95_000_000,
        100_000_000, 110_000_000, 120_000_000, 130_000_000, 140_000_000, 150_000_000,
    ]
    for sal in salaries:
        hub_links["salary"].append((f"연봉 {fmt_manwon_fn(sal)} 실수령액", f"salary/salary-{sal // 10_000}man.html"))

    for sal in salaries:
        rel_path = f"salary/salary-{sal // 10_000}man.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_kr_salary(sal)
        title = f"2026 연봉 {fmt_manwon_fn(sal)} 실수령액 계산기 (4대보험·세금 공제표)"
        desc = (
            f"연봉 {fmt_manwon_fn(sal)}의 2026년 예상 월 실수령액은 {fmt_krw_fn(res.monthly_net_krw)} "
            f"(세전 {fmt_krw_fn(res.monthly_gross_krw)}, 공제 {fmt_krw_fn(res.total_deduction_krw)}). "
            f"국민연금·건강보험·소득세 실시간 계산."
        )
        related = "".join(
            f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>'
            for l, h in hub_links["salary"] if h != rel_path
        )[:2400]
        faq_html, faq_ld = faq_section_fn([
            (f"연봉 {fmt_manwon_fn(sal)}의 월 4대보험 공제액은 얼마인가요?",
             f"국민연금 {fmt_krw_fn(res.national_pension_krw)}, 건강보험 {fmt_krw_fn(res.health_insurance_krw)}, "
             f"장기요양 {fmt_krw_fn(res.long_term_care_krw)}, 고용보험 {fmt_krw_fn(res.employment_insurance_krw)}입니다."),
            ("비과세 식대(월 20만 원)가 실수령액에 미치는 영향은?",
             "비과세 식대가 높을수록 4대보험 및 소득세 과세표준이 줄어들어 매월 실수령액이 늘어납니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#salary-hub">연봉 실수령액</a> › 연봉 {esc_fn(fmt_manwon_fn(sal))}</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">2026년 4대보험 요율과 근로소득세 기준을 반영한 연봉 {esc_fn(fmt_manwon_fn(sal))} 실시간 월 실수령액 계산기입니다.</p>
{adsense_slot_fn(cfg, "salary-top")}
<section class="card" data-widget="salary-calc">
  <h2>실시간 연봉 실수령액 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>세전 연봉 (원)</label><input type="number" name="salary" value="{sal}" step="1000000"></div>
    <div class="field"><label>월 비과세 식대 (원)</label><input type="number" name="nontax" value="200000" step="50000"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">세전 월급</div><div class="metric-value" data-out="gross">{fmt_krw_fn(res.monthly_gross_krw)}</div></div>
    <div class="metric-box"><div class="metric-label">월 공제액 합계</div><div class="metric-value" data-out="ded">{fmt_krw_fn(res.total_deduction_krw)}</div></div>
    <div class="metric-box highlight"><div class="metric-label">예상 월 실수령액</div><div class="metric-value" data-out="net">{fmt_krw_fn(res.monthly_net_krw)}</div></div>
  </div>
</section>
{affiliate_box_fn("발급 조건 없는 연회비 무료 머니트리카드 (소득공제 30%)", "연봉 실수령액 절약과 첫 결제 혜택까지! 발급 조건 없이 누구나 간편 신청할 수 있습니다.", "머니트리카드 무료 발급 신청하기", "https://iryan.kr/t8hdd04j25")}
{adsense_slot_fn(cfg, "salary-mid")}
{faq_html}
<section class="card"><h2>다른 연봉 구간 실수령액 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "salary"))

    # 2. 퇴직금 & 실업급여 계산기 (20페이지)
    sev_dir = dist / "severance"
    sev_dir.mkdir(parents=True, exist_ok=True)
    sev_specs = [(m, y) for m in (2_500_000, 3_500_000, 5_000_000, 7_000_000) for y in (1, 2, 3, 5, 10)]
    for m, y in sev_specs:
        hub_links["severance"].append((f"월 {fmt_manwon_fn(m)} {y}년 퇴직금", f"severance/sev-{m // 10_000}man-{y}y.html"))
    for m, y in sev_specs:
        rel_path = f"severance/sev-{m // 10_000}man-{y}y.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_kr_severance(m, y)
        title = f"월급 {fmt_manwon_fn(m)} {y}년 근속 퇴직금·실업급여 계산기 (2026 기준)"
        desc = f"월급 {fmt_manwon_fn(m)}으로 {y}년 근속 시 예상 법정 퇴직금 {fmt_krw_fn(res['severance_gross_krw'])}, 실업급여 총 {fmt_krw_fn(res['total_unemployment_krw'])} ({res['unemployment_days']}일)."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hub_links["severance"] if h != rel_path)
        faq_html, faq_ld = faq_section_fn([
            ("퇴직금 수령 시 IRP 계좌가 필수인가요?", "만 55세 미만 퇴직자는 원칙적으로 개인형 퇴직연금(IRP) 계좌로 수령해야 하며, 퇴직소득세 이연 혜택을 받을 수 있습니다."),
            ("실업급여 수급 조건은 어떻게 되나요?", "퇴직 전 18개월간 고용보험 피보험단위기간 180일 이상이고 비자발적 이직 사유에 해당해야 합니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#severance-hub">퇴직금·실업급여</a> › 월 {esc_fn(fmt_manwon_fn(m))} {y}년</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">근로기준법 퇴직금 산식과 고용보험 실업급여 상·하한액 기준으로 월급 {esc_fn(fmt_manwon_fn(m))}, {y}년 근속 시 수령액을 계산합니다.</p>
{adsense_slot_fn(cfg, "sev-top")}
<section class="card" data-widget="severance-calc">
  <h2>실시간 퇴직금·실업급여 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>퇴직 전 3개월 평균 월급 (원)</label><input type="number" name="monthly" value="{m}" step="100000"></div>
    <div class="field"><label>총 근속연수 (년)</label><input type="number" name="years" value="{y}" min="1" max="40"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">예상 법정 퇴직금 (세전)</div><div class="metric-value" data-out="sev">{fmt_krw_fn(res['severance_gross_krw'])}</div></div>
    <div class="metric-box"><div class="metric-label">예상 실업급여 총액</div><div class="metric-value" data-out="unemp">{fmt_krw_fn(res['total_unemployment_krw'])}</div></div>
  </div>
</section>
{affiliate_box_fn("퇴직금 IRP 수수료 무료·고금리 예금 비교", "퇴직금을 안전하게 굴릴 수 있는 비대면 IRP 계좌와 정기예금 금리를 비교해 보세요.", "IRP·퇴직금 굴리기 비교", cfg.affiliate_deposit_url)}
{faq_html}
<section class="card"><h2>다른 근속·월급 퇴직금 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "severance"))

    # 3. 부동산 취득세·중개보수(복비) 계산기 (18페이지)
    re_dir = dist / "realestate"
    re_dir.mkdir(parents=True, exist_ok=True)
    re_specs = [(p, h) for p in (300_000_000, 500_000_000, 700_000_000, 900_000_000, 1_200_000_000, 1_500_000_000) for h in (1, 2, 3)]
    for p, h in re_specs:
        hub_links["realestate"].append((f"{fmt_manwon_fn(p)} {h}주택 취득세·복비", f"realestate/re-{p // 100_000_000}eok-{h}h.html"))
    for p, h in re_specs:
        rel_path = f"realestate/re-{p // 100_000_000}eok-{h}h.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_kr_realestate_cost(p, h)
        title = f"아파트 {fmt_manwon_fn(p)} {h}주택 취득세·중개보수(복비) 계산기 (2026)"
        desc = f"{fmt_manwon_fn(p)} 주택 매매({h}주택) 시 취득세+지방교육세 {fmt_krw_fn(int(res['total_tax_krw']))}, 복비 상한 {fmt_krw_fn(int(res['brokerage_fee_krw']))}, 총 부대비용 {fmt_krw_fn(int(res['total_closing_cost_krw']))}."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in hub_links["realestate"] if hr != rel_path)
        faq_html, faq_ld = faq_section_fn([
            (f"{fmt_manwon_fn(p)} 아파트 중개보수 상한요율은 몇 %인가요?", f"매매가 기준 최대 {res['broker_rate_pct']}%({fmt_krw_fn(int(res['brokerage_fee_krw']))}, 부가세 별도) 이내에서 협의 가능합니다."),
            ("생애최초 주택구입 취득세 감면 혜택은?", "요건을 충족하는 생애최초 주택 구입자는 최대 200만 원 한도로 취득세 감면 혜택을 받을 수 있습니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#realestate-hub">부동산 취득세·복비</a> › {esc_fn(fmt_manwon_fn(p))} {h}주택</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">{esc_fn(fmt_manwon_fn(p))} 주택 매매({h}주택 기준) 시 납부할 취득세·지방교육세 및 공인중개사 복비 상한액을 실시간으로 계산합니다.</p>
{adsense_slot_fn(cfg, "re-top")}
<section class="card" data-widget="realestate-calc">
  <h2>실시간 부동산 취득세·복비 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>주택 매매가 (원)</label><input type="number" name="price" value="{p}" step="50000000"></div>
    <div class="field"><label>보유 주택 수</label>
      <select name="houses">
        <option value="1" {"selected" if h == 1 else ""}>1주택 (일반)</option>
        <option value="2" {"selected" if h == 2 else ""}>2주택 (조정대상 중과 참고)</option>
        <option value="3" {"selected" if h == 3 else ""}>3주택 이상</option>
      </select>
    </div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">취득세+교육세</div><div class="metric-value" data-out="tax">{fmt_krw_fn(int(res['total_tax_krw']))}</div></div>
    <div class="metric-box"><div class="metric-label">중개보수(복비) 상한</div><div class="metric-value" data-out="broker">{fmt_krw_fn(int(res['brokerage_fee_krw']))}</div></div>
    <div class="metric-box highlight"><div class="metric-label">총 예상 부대비용</div><div class="metric-value" data-out="total">{fmt_krw_fn(int(res['total_closing_cost_krw']))}</div></div>
  </div>
</section>
{affiliate_box_fn("주택담보대출 최저금리 & 이사·인테리어 견적 비교", "잔금일 전 1금융권 주담대 금리와 포장이사·입주청소 견적을 한 번에 비교해 비용을 줄이세요.", "주담대·이사 견적 비교하기", cfg.affiliate_loan_url)}
{faq_html}
<section class="card"><h2>다른 금액대 부동산 취득세 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "realestate"))

    # 4. 자동차 할부·취등록세 계산기 (20페이지 — 자동차보험 최상위 CPC)
    auto_dir = dist / "auto"
    auto_dir.mkdir(parents=True, exist_ok=True)
    auto_specs = [(p, m) for p in (20_000_000, 30_000_000, 40_000_000, 50_000_000, 70_000_000) for m in (24, 36, 48, 60)]
    for p, m in auto_specs:
        hub_links["auto"].append((f"{fmt_manwon_fn(p)} 차량 {m}개월 할부", f"auto/auto-{p // 10_000}man-{m}m.html"))
    for p, m in auto_specs:
        rel_path = f"auto/auto-{p // 10_000}man-{m}m.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_kr_auto_finance(p, m)
        title = f"자동차 {fmt_manwon_fn(p)} {m}개월 할부 월납입금·취등록세 계산기 (2026)"
        desc = f"{fmt_manwon_fn(p)} 신차 구매 시(선수금 20%, 연 5.5%, {m}개월) 취등록세 약 {fmt_krw_fn(res['acq_tax_krw'])}, 월 할부금 {fmt_krw_fn(res['monthly_payment_krw'])}."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in hub_links["auto"] if hr != rel_path)
        faq_html, faq_ld = faq_section_fn([
            ("승용차 취등록세는 차량가의 몇 %인가요?", "비영업용 승용차 기준 부가세를 제외한 공급가액의 7%가 부과되며, 경차·전기차·하이브리드는 법정 감면 혜택이 적용됩니다."),
            ("자동차 할부와 장기렌트 중 무엇이 유리한가요?", "초기 취등록세·보험료 부담을 줄이고 경비처리가 필요한 사업자는 장기렌트가 유리할 수 있으며, 장기 보유 시 저금리 오토할부가 총비용 면에서 유리합니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#auto-hub">자동차 할부·취등록세</a> › {esc_fn(fmt_manwon_fn(p))} {m}개월</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">차량가 {esc_fn(fmt_manwon_fn(p))} 신차·중고차 구매 시 취등록세(7%)와 {m}개월 월 할부금, 총 이자를 즉시 계산합니다.</p>
{adsense_slot_fn(cfg, "auto-top")}
<section class="card" data-widget="auto-calc">
  <h2>실시간 자동차 할부·취등록세 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>차량 가격 (원)</label><input type="number" name="price" value="{p}" step="1000000"></div>
    <div class="field"><label>할부 기간 (개월)</label><input type="number" name="months" value="{m}" min="6" max="72"></div>
    <div class="field"><label>할부 금리 (연 %)</label><input type="number" name="rate" value="5.5" step="0.1"></div>
    <div class="field"><label>선수금 비율 (%)</label><input type="number" name="down" value="20" min="0" max="90"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">예상 취등록세 (7%)</div><div class="metric-value" data-out="acq">{fmt_krw_fn(res['acq_tax_krw'])}</div></div>
    <div class="metric-box highlight"><div class="metric-label">월 할부 납입금</div><div class="metric-value" data-out="monthly">{fmt_krw_fn(res['monthly_payment_krw'])}</div></div>
    <div class="metric-box"><div class="metric-label">총 할부 이자</div><div class="metric-value" data-out="interest">{fmt_krw_fn(res['total_interest_krw'])}</div></div>
  </div>
</section>
{affiliate_box_fn("신차 장기렌트·오토리스 전 렌트사 최저가 1분 비교 (ONEPICK)", "초기 취등록세·보험료 부담 없이 전국 렌트사 월 납입금을 한 번에 비교해 보세요.", "신차 장기렌트 최저가 무료 상담", "https://iryan.kr/t8hdd04rss")}
{faq_html}
<section class="card"><h2>다른 차량가·할부기간 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "auto"))

    # 5. Global English USD High-RPM Calculators (/en/, 36 pages: US Mortgage 20 + Compound Interest 16)
    en_dir = dist / "en"
    en_dir.mkdir(parents=True, exist_ok=True)
    us_mortgages = [(amt, yr) for amt in (200_000, 300_000, 400_000, 500_000, 600_000, 750_000, 900_000, 1_000_000, 1_200_000, 1_500_000) for yr in (15, 30)]
    for amt, yr in us_mortgages:
        hub_links["en_global"].append((f"${amt // 1000:,}K {yr}Y US Mortgage", f"en/mortgage-{amt // 1000}k-{yr}y.html"))
    for amt, yr in us_mortgages:
        rel_path = f"en/mortgage-{amt // 1000}k-{yr}y.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_usd_mortgage(amt, yr, 6.25)
        title = f"${amt:,} Mortgage Payment Calculator ({yr}-Year Fixed, 2026 Rates)"
        desc = f"Calculate monthly P&I payment on a ${amt:,} {yr}-year fixed mortgage at 6.25%: ${res['monthly_payment_usd']:,}/mo, total interest ${res['total_interest_usd']:,}."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in hub_links["en_global"][:16] if hr != rel_path)
        faq_html, faq_ld = faq_section_fn([
            (f"What is the monthly payment on a ${amt:,} mortgage for {yr} years?",
             f"At a 6.25% fixed interest rate, principal and interest is ${res['monthly_payment_usd']:,} per month (excluding property taxes and homeowners insurance)."),
            ("How much can a 15-year mortgage save versus a 30-year mortgage?",
             "A 15-year fixed loan has higher monthly payments but typically cuts total lifetime interest by more than half. Adjust the term above to compare."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-hub">Global USD Calculators</a> › ${amt:,} ({yr}Y)</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Free interactive US mortgage amortization calculator for a ${amt:,} home loan over {yr} years. Adjust loan amount, interest rate, and term in real time.</p>
{adsense_slot_fn(cfg, "en-mortgage-top")}
<section class="card" data-widget="usd-mortgage-calc">
  <h2>Interactive US Mortgage Payment Calculator</h2>
  <div class="calc-grid">
    <div class="field"><label>Loan Amount (USD)</label><input type="number" name="principal" value="{amt}" step="10000"></div>
    <div class="field"><label>Loan Term (Years)</label><input type="number" name="years" value="{yr}" min="5" max="40"></div>
    <div class="field"><label>Interest Rate (%)</label><input type="number" name="rate" value="6.25" step="0.125"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">Monthly P&amp;I Payment</div><div class="metric-value" data-out="monthly">${res['monthly_payment_usd']:,}</div></div>
    <div class="metric-box"><div class="metric-label">Total Interest Paid</div><div class="metric-value" data-out="interest">${res['total_interest_usd']:,}</div></div>
    <div class="metric-box"><div class="metric-label">Total Cost of Loan</div><div class="metric-value" data-out="total">${res['total_payment_usd']:,}</div></div>
  </div>
</section>
{adsense_slot_fn(cfg, "en-mortgage-mid")}
{faq_html}
<section class="card"><h2>More USD Finance Calculators</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "en_global"))

    us_compounds = [(init, mc, yr) for init in (10_000, 25_000, 50_000, 100_000) for mc in (500, 1000) for yr in (15, 30)]
    for init, mc, yr in us_compounds:
        hub_links["en_global"].append((f"${init // 1000}K + ${mc}/mo ({yr}Y Compound)", f"en/compound-{init // 1000}k-{mc}m-{yr}y.html"))
    for init, mc, yr in us_compounds:
        rel_path = f"en/compound-{init // 1000}k-{mc}m-{yr}y.html"
        url = f"{cfg.site_url}/{rel_path}"
        res = calculate_usd_compound(init, mc, yr, 8.0)
        title = f"${init:,} Invested + ${mc:,}/Month for {yr} Years — Compound Interest Calculator"
        desc = f"Starting with ${init:,} and contributing ${mc:,}/month at 8% annual return grows to ${res['future_value_usd']:,} in {yr} years (${res['total_growth_usd']:,} investment growth)."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in hub_links["en_global"][20:] if hr != rel_path)
        faq_html, faq_ld = faq_section_fn([
            (f"How much will ${init:,} plus ${mc:,}/month be worth in {yr} years?",
             f"At an 8% average annual return compounded monthly, your portfolio reaches ${res['future_value_usd']:,}, including ${res['total_growth_usd']:,} in compound interest."),
            ("Is 8% a realistic S&P 500 return assumption?",
             "Historically the S&P 500 has averaged around 7%–10% annually before inflation. You can test conservative (6%) or aggressive (10%) returns above."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-hub">Global USD Calculators</a> › Compound Interest</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Calculate long-term 401(k), Roth IRA, and index fund compounding growth for ${init:,} initial principal and ${mc:,} monthly contributions over {yr} years.</p>
{adsense_slot_fn(cfg, "en-compound-top")}
<section class="card" data-widget="usd-compound-calc">
  <h2>Interactive Compound Interest &amp; Retirement Calculator</h2>
  <div class="calc-grid">
    <div class="field"><label>Initial Investment (USD)</label><input type="number" name="initial" value="{init}" step="5000"></div>
    <div class="field"><label>Monthly Contribution (USD)</label><input type="number" name="monthly" value="{mc}" step="100"></div>
    <div class="field"><label>Investment Horizon (Years)</label><input type="number" name="years" value="{yr}" min="1" max="50"></div>
    <div class="field"><label>Expected Annual Return (%)</label><input type="number" name="rate" value="8.0" step="0.5"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">Projected Future Value</div><div class="metric-value" data-out="fv">${res['future_value_usd']:,}</div></div>
    <div class="metric-box"><div class="metric-label">Total Contributions</div><div class="metric-value" data-out="contrib">${res['total_contributions_usd']:,}</div></div>
    <div class="metric-box"><div class="metric-label">Total Compound Growth</div><div class="metric-value" data-out="growth">${res['total_growth_usd']:,}</div></div>
  </div>
</section>
{adsense_slot_fn(cfg, "en-compound-mid")}
{faq_html}
<section class="card"><h2>More Compound Growth Scenarios</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel_path).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_path, url, title, desc, "en_global"))

    return pages, hub_links
