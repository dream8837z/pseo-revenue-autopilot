"""Mega Expansion: KR Tax (Gift/Freelance/CapitalGains), Life Finance (Pension/Customs/Jeonse-Wolse), and Global USD Pro Calculators (+120 pages)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pseo_engine.config import SiteConfig


MEGA_EXPANSION_JS = """
(function () {
  function fmtKrw(n) { return Math.round(n).toLocaleString('ko-KR') + '원'; }
  function fmtUsd(n) { return '$' + Math.round(n).toLocaleString('en-US'); }

  // 1. KR Gift Tax (증여세)
  document.querySelectorAll('[data-widget="gift-tax-calc"]').forEach(function (root) {
    var aEl = root.querySelector('[name="amount"]');
    var dEl = root.querySelector('[name="deduction"]');
    function update() {
      var amt = Math.max(0, Number(aEl.value || 0));
      var ded = Math.max(0, Number(dEl.value || 0));
      var base = Math.max(0, amt - ded);
      var tax = 0;
      if (base <= 100000000) tax = base * 0.10;
      else if (base <= 500000000) tax = base * 0.20 - 10000000;
      else if (base <= 1000000000) tax = base * 0.30 - 60000000;
      else if (base <= 3000000000) tax = base * 0.40 - 160000000;
      else tax = base * 0.50 - 460000000;
      var netTax = Math.max(0, tax * 0.97); // 신고세액공제 3%
      root.querySelector('[data-out="base"]').textContent = fmtKrw(base);
      root.querySelector('[data-out="tax"]').textContent = fmtKrw(netTax);
    }
    [aEl, dEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 2. KR Freelance 3.3% Tax Refund Estimator (종합소득세)
  document.querySelectorAll('[data-widget="freelance-tax-calc"]').forEach(function (root) {
    var rEl = root.querySelector('[name="revenue"]');
    var eEl = root.querySelector('[name="expense_pct"]');
    function update() {
      var rev = Math.max(0, Number(rEl.value || 0));
      var expPct = Math.min(90, Math.max(0, Number(eEl.value || 60))) / 100;
      var prepaid = rev * 0.033;
      var base = Math.max(0, rev * (1 - expPct) - 1500000);
      var calc = base <= 14000000 ? base * 0.06 :
        base <= 50000000 ? base * 0.15 - 1260000 :
        base <= 88000000 ? base * 0.24 - 5760000 : base * 0.35 - 15440000;
      var finalTax = Math.max(0, calc * 1.1);
      var diff = prepaid - finalTax;
      root.querySelector('[data-out="prepaid"]').textContent = fmtKrw(prepaid);
      root.querySelector('[data-out="final"]').textContent = fmtKrw(finalTax);
      root.querySelector('[data-out="diff"]').textContent = diff >= 0 ? ('예상 환급 +' + fmtKrw(diff)) : ('추가 납부 ' + fmtKrw(-diff));
    }
    [rEl, eEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 3. KR Capital Gains Tax (양도소득세)
  document.querySelectorAll('[data-widget="capgains-calc"]').forEach(function (root) {
    var gEl = root.querySelector('[name="gain"]');
    var yEl = root.querySelector('[name="years"]');
    function update() {
      var gain = Math.max(0, Number(gEl.value || 0));
      var yrs = Math.max(0, Number(yEl.value || 3));
      var ltDedPct = yrs >= 3 ? Math.min(0.30, yrs * 0.02) : 0;
      var base = Math.max(0, gain * (1 - ltDedPct) - 2500000);
      var tax = base <= 14000000 ? base * 0.06 :
        base <= 50000000 ? base * 0.15 - 1260000 :
        base <= 88000000 ? base * 0.24 - 5760000 :
        base <= 150000000 ? base * 0.35 - 15440000 : base * 0.38 - 19940000;
      var total = Math.max(0, tax * 1.1);
      root.querySelector('[data-out="base"]').textContent = fmtKrw(base);
      root.querySelector('[data-out="tax"]').textContent = fmtKrw(total);
    }
    [gEl, yEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 4. KR National Pension Estimator (국민연금)
  document.querySelectorAll('[data-widget="pension-calc"]').forEach(function (root) {
    var mEl = root.querySelector('[name="monthly"]');
    var yEl = root.querySelector('[name="years"]');
    function update() {
      var inc = Math.min(6170000, Math.max(390000, Number(mEl.value || 3500000)));
      var yrs = Math.min(40, Math.max(10, Number(yEl.value || 20)));
      // 단순화 근사: A값(약 298만원) + B값(본인소득) 평균 × 지급률
      var monthlyBenefit = ((2980000 + inc) / 2) * 0.0115 * yrs;
      root.querySelector('[data-out="benefit"]').textContent = fmtKrw(monthlyBenefit) + ' / 월';
      root.querySelector('[data-out="annual"]').textContent = fmtKrw(monthlyBenefit * 12) + ' / 년';
    }
    [mEl, yEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 5. KR Overseas Customs Duty Calculator (해외직구 관부가세)
  document.querySelectorAll('[data-widget="customs-calc"]').forEach(function (root) {
    var uEl = root.querySelector('[name="usd"]');
    var fxEl = root.querySelector('[name="fx"]');
    var limEl = root.querySelector('[name="limit"]');
    var rateEl = root.querySelector('[name="duty_pct"]');
    function update() {
      var usd = Math.max(0, Number(uEl.value || 0));
      var fx = Math.max(500, Number(fxEl.value || 1380));
      var lim = Number(limEl.value || 150);
      var dutyPct = Math.max(0, Number(rateEl.value || 8)) / 100;
      var krw = usd * fx;
      if (usd <= lim) {
        root.querySelector('[data-out="duty"]').textContent = '0원 (면세 구간)';
        root.querySelector('[data-out="vat"]').textContent = '0원';
        root.querySelector('[data-out="total"]').textContent = fmtKrw(krw);
      } else {
        var duty = krw * dutyPct;
        var vat = (krw + duty) * 0.10;
        root.querySelector('[data-out="duty"]').textContent = fmtKrw(duty);
        root.querySelector('[data-out="vat"]').textContent = fmtKrw(vat);
        root.querySelector('[data-out="total"]').textContent = fmtKrw(krw + duty + vat);
      }
    }
    [uEl, fxEl, limEl, rateEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 6. KR Jeonse <-> Wolse Converter (전월세 전환)
  document.querySelectorAll('[data-widget="jeonse-wolse-calc"]').forEach(function (root) {
    var dEl = root.querySelector('[name="deposit_diff"]');
    var rEl = root.querySelector('[name="rate"]');
    function update() {
      var diff = Math.max(0, Number(dEl.value || 0));
      var rate = Math.max(0, Number(rEl.value || 5.0)) / 100;
      var monthly = (diff * rate) / 12;
      root.querySelector('[data-out="monthly"]').textContent = fmtKrw(monthly) + ' / 월';
      root.querySelector('[data-out="yearly"]').textContent = fmtKrw(monthly * 12) + ' / 년';
    }
    [dEl, rEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 7. Global US Auto Loan Calculator
  document.querySelectorAll('[data-widget="us-auto-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="price"]');
    var dEl = root.querySelector('[name="down"]');
    var mEl = root.querySelector('[name="months"]');
    var rEl = root.querySelector('[name="apr"]');
    function update() {
      var loan = Math.max(0, Number(pEl.value || 0) - Number(dEl.value || 0));
      var m = Math.max(12, Number(mEl.value || 60));
      var mr = Math.max(0, Number(rEl.value || 6.5)) / 100 / 12;
      var pmt = mr === 0 ? loan / m : loan * (mr * Math.pow(1 + mr, m)) / (Math.pow(1 + mr, m) - 1);
      root.querySelector('[data-out="monthly"]').textContent = fmtUsd(pmt) + '/mo';
      root.querySelector('[data-out="interest"]').textContent = fmtUsd(Math.max(0, pmt * m - loan));
    }
    [pEl, dEl, mEl, rEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 8. Global US Hourly to Annual Salary Converter
  document.querySelectorAll('[data-widget="us-hourly-calc"]').forEach(function (root) {
    var hEl = root.querySelector('[name="hourly"]');
    var wEl = root.querySelector('[name="hours"]');
    function update() {
      var hr = Math.max(0, Number(hEl.value || 0));
      var hrs = Math.max(1, Number(wEl.value || 40));
      var annual = hr * hrs * 52;
      root.querySelector('[data-out="annual"]').textContent = fmtUsd(annual) + '/yr';
      root.querySelector('[data-out="monthly"]').textContent = fmtUsd(annual / 12) + '/mo';
      root.querySelector('[data-out="biweekly"]').textContent = fmtUsd(annual / 26) + '/2wks';
    }
    [hEl, wEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 9. Global SaaS Margin & Break-Even ROI Calculator
  document.querySelectorAll('[data-widget="saas-roi-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="price"]');
    var cEl = root.querySelector('[name="cac"]');
    var chEl = root.querySelector('[name="churn"]');
    function update() {
      var mrr = Math.max(1, Number(pEl.value || 49));
      var cac = Math.max(1, Number(cEl.value || 250));
      var churn = Math.max(0.5, Number(chEl.value || 4)) / 100;
      var ltv = mrr / churn;
      var ratio = ltv / cac;
      var payback = cac / mrr;
      root.querySelector('[data-out="ltv"]').textContent = fmtUsd(ltv);
      root.querySelector('[data-out="ratio"]').textContent = ratio.toFixed(1) + 'x';
      root.querySelector('[data-out="payback"]').textContent = payback.toFixed(1) + ' mos';
    }
    [pEl, cEl, chEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });
})();
"""


def generate_mega_expansion_pages(
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
    fmt_manwon_fn: Callable[[int], str],
) -> tuple[list[Any], dict[str, list[tuple[str, str]]]]:
    """Generate 120 additional high-CPC KR Tax/Life + Global USD Pro SEO pages."""
    pages: list[Any] = []
    hubs: dict[str, list[tuple[str, str]]] = {
        "tax": [],
        "life": [],
        "en_pro": [],
    }

    # --- 1. KR Tax (40 pages: Gift 15 + Freelance 15 + Capital Gains 10) ---
    tax_dir = dist / "tax"
    tax_dir.mkdir(parents=True, exist_ok=True)

    gift_targets = [("spouse", "배우자", 600_000_000), ("adult-child", "성년 자녀", 50_000_000), ("minor-child", "미성년 자녀", 20_000_000)]
    gift_amounts = [100_000_000, 300_000_000, 500_000_000, 1_000_000_000, 2_000_000_000]
    for tslug, tname, ded in gift_targets:
        for amt in gift_amounts:
            hubs["tax"].append((f"{tname} {fmt_manwon_fn(amt)} 증여세", f"tax/gift-{tslug}-{amt // 100_000_000}eok.html"))

    for tslug, tname, ded in gift_targets:
        for amt in gift_amounts:
            rel = f"tax/gift-{tslug}-{amt // 100_000_000}eok.html"
            url = f"{cfg.site_url}/{rel}"
            title = f"2026 {tname} {fmt_manwon_fn(amt)} 증여세 계산기 (10년 공제한도·신고세액공제 3%)"
            desc = f"{tname}에게 {fmt_manwon_fn(amt)} 증여 시 공제한도 {fmt_manwon_fn(ded)} 적용 후 과세표준과 예상 증여세를 즉시 계산합니다."
            faq_html, faq_ld = faq_section_fn([
                (f"{tname} 증여재산 공제 한도는 얼마인가요?", f"10년 합산 기준 {fmt_manwon_fn(ded)}까지 비과세 공제가 적용됩니다."),
                ("증여세 신고기한과 자진신고 공제는?", "증여일이 속한 달의 말일부터 3개월 이내 신고 시 산출세액의 3%를 공제받습니다."),
            ])
            related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hubs["tax"][:15] if h != rel)
            body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#tax-hub">세금 계산기</a> › {esc_fn(tname)} 증여세</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">{esc_fn(tname)} {esc_fn(fmt_manwon_fn(amt))} 증여 시 국세청 누진세율(10%~50%)과 신고세액공제 3%를 반영해 예상 세액을 즉시 계산합니다.</p>
{adsense_slot_fn(cfg, "tax-gift-top")}
<section class="card" data-widget="gift-tax-calc">
  <h2>실시간 증여세 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>증여 재산가액 (원)</label><input type="number" name="amount" value="{amt}" step="10000000"></div>
    <div class="field"><label>증여재산 공제액 (원)</label><input type="number" name="deduction" value="{ded}" step="10000000"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">과세표준</div><div class="metric-value" data-out="base">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">예상 최종 증여세 (3% 공제)</div><div class="metric-value" data-out="tax">-</div></div>
  </div>
</section>
{affiliate_box_fn("상속·증여 절세 컨설팅 & 세무기장 무료 견적", "고액 증여 전 세무 전문가 상담과 절세 금융상품(연금·신탁)을 비교해 보세요.", "절세 세무 상담 비교하기", cfg.affiliate_deposit_url)}
{faq_html}
<section class="card"><h2>다른 증여세 계산기</h2><div class="link-grid">{related}</div></section>
"""
            (dist / rel).write_text(
                base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                               json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                               asset_prefix="../", is_sample_data=is_sample_data),
                encoding="utf-8",
            )
            pages.append(page_cls(rel, url, title, desc, "tax"))

    # Freelance 3.3% (15 pages)
    fl_revs = [20_000_000, 25_000_000, 30_000_000, 35_000_000, 40_000_000, 45_000_000, 50_000_000, 60_000_000, 70_000_000, 80_000_000, 90_000_000, 100_000_000, 110_000_000, 120_000_000, 150_000_000]
    fl_links = [(f"프리랜서 연수입 {fmt_manwon_fn(r)} 종소세", f"tax/freelance-{r // 10_000}man.html") for r in fl_revs]
    hubs["tax"].extend(fl_links)
    for rev in fl_revs:
        rel = f"tax/freelance-{rev // 10_000}man.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"2026 프리랜서 연수입 {fmt_manwon_fn(rev)} 3.3% 종합소득세 환급·납부 계산기"
        desc = f"3.3% 원천징수 프리랜서 연수입 {fmt_manwon_fn(rev)}의 5월 종합소득세 예상 환급금 또는 추가 납부액을 경비율별로 즉시 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            ("프리랜서 3.3% 환급은 언제 신청하나요?", "매년 5월 1일~5월 31일 종합소득세 정기신고 기간에 홈택스에서 직접 신고하거나 세무 대행으로 환급받을 수 있습니다."),
            ("단순경비율과 기준경비율 차이는?", "직전 연도 수입금액이 업종별 기준 미만인 소규모 프리랜서는 높은 경비율(약 60% 내외)인 단순경비율이 적용되어 환급에 유리합니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in fl_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#tax-hub">세금 계산기</a> › 프리랜서 3.3% 종소세</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">연수입 {esc_fn(fmt_manwon_fn(rev))} 프리랜서·N잡러의 기납부세액(3.3%)과 결정세액을 비교해 예상 환급액을 계산합니다.</p>
{adsense_slot_fn(cfg, "tax-fl-top")}
<section class="card" data-widget="freelance-tax-calc">
  <h2>실시간 프리랜서 3.3% 종합소득세 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>연간 총 수입금액 (원)</label><input type="number" name="revenue" value="{rev}" step="1000000"></div>
    <div class="field"><label>예상 경비율 (%)</label><input type="number" name="expense_pct" value="60" min="0" max="90"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">이미 낸 3.3% 세금</div><div class="metric-value" data-out="prepaid">-</div></div>
    <div class="metric-box"><div class="metric-label">예상 결정세액</div><div class="metric-value" data-out="final">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">환급 / 추가납부 예상</div><div class="metric-value" data-out="diff">-</div></div>
  </div>
</section>
{affiliate_box_fn("프리랜서·개인사업자 세금 환급 조회 & 간편 세무기장", "숨은 3.3% 환급금 조회와 절세 경비처리 솔루션을 비교해 보세요.", "내 숨은 환급금 확인하기", cfg.affiliate_subsidy_url)}
{faq_html}
<section class="card"><h2>다른 수입 구간 프리랜서 종소세 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "tax"))

    # Capital Gains (10 pages)
    cg_specs = [(g, y) for g in (50_000_000, 100_000_000, 200_000_000, 300_000_000, 500_000_000) for y in (3, 10)]
    cg_links = [(f"양도차익 {fmt_manwon_fn(g)} ({y}년 보유) 양도세", f"tax/capgains-{g // 10_000}man-{y}y.html") for g, y in cg_specs]
    hubs["tax"].extend(cg_links)
    for g, y in cg_specs:
        rel = f"tax/capgains-{g // 10_000}man-{y}y.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"2026 부동산 양도차익 {fmt_manwon_fn(g)} {y}년 보유 양도소득세 계산기"
        desc = f"부동산 양도차익 {fmt_manwon_fn(g)}, 보유기간 {y}년 기준 장기보유특별공제와 기본공제 250만 원 적용 예상 양도소득세 계산기."
        faq_html, faq_ld = faq_section_fn([
            ("1세대 1주택 비과세 기준은 얼마인가요?", "실거래가 12억 원 이하 1세대 1주택을 2년 이상 보유(조정지역 취득 시 거주 포함)하면 양도소득세가 비과세됩니다."),
            ("장기보유특별공제는 몇 년부터 적용되나요?", "일반 부동산은 3년 이상 보유 시 연 2%씩 최대 30%(15년)까지 공제됩니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in cg_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#tax-hub">세금 계산기</a> › 양도소득세</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">양도차익 {esc_fn(fmt_manwon_fn(g))}, {y}년 보유 시 장기보유특별공제 및 지방소득세 포함 예상 양도소득세를 계산합니다.</p>
{adsense_slot_fn(cfg, "tax-cg-top")}
<section class="card" data-widget="capgains-calc">
  <h2>실시간 부동산 양도소득세 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>양도차익 (매도가-매수가-필요경비, 원)</label><input type="number" name="gain" value="{g}" step="10000000"></div>
    <div class="field"><label>보유 기간 (년)</label><input type="number" name="years" value="{y}" min="0" max="30"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">과세표준</div><div class="metric-value" data-out="base">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">예상 양도세 (지방세 포함)</div><div class="metric-value" data-out="tax">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 양도소득세 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "tax"))

    # --- 2. KR Life Finance (36 pages: Pension 12 + Customs 12 + Jeonse/Wolse 12) ---
    life_dir = dist / "life"
    life_dir.mkdir(parents=True, exist_ok=True)

    pen_specs = [(m, y) for m in (2_500_000, 3_500_000, 4_500_000, 6_000_000) for y in (10, 20, 30)]
    pen_links = [(f"월소득 {fmt_manwon_fn(m)} {y}년 국민연금", f"life/pension-{m // 10_000}man-{y}y.html") for m, y in pen_specs]
    hubs["life"].extend(pen_links)
    for m, y in pen_specs:
        rel = f"life/pension-{m // 10_000}man-{y}y.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"2026 월소득 {fmt_manwon_fn(m)} {y}년 납부 국민연금 예상 수령액 계산기"
        desc = f"평균 월소득 {fmt_manwon_fn(m)}으로 {y}년간 국민연금 가입 시 만 65세 이후 예상 월 수령액을 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            ("국민연금 최소 가입기간은 몇 년인가요?", "최소 10년(120개월) 이상 납부해야 노령연금을 평생 수령할 수 있습니다."),
            ("연기연금을 신청하면 얼마나 늘어나나요?", "수령 시기를 1년 늦출 때마다 연 7.2%(최대 5년, 36%)가 가산됩니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in pen_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#life-hub">생활금융 계산기</a> › 국민연금</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">월소득 {esc_fn(fmt_manwon_fn(m))}, {y}년 납부 기준 예상 국민연금 월 수령액을 실시간으로 추정합니다.</p>
{adsense_slot_fn(cfg, "life-pen-top")}
<section class="card" data-widget="pension-calc">
  <h2>국민연금 예상 수령액 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>평균 월소득 (원)</label><input type="number" name="monthly" value="{m}" step="100000"></div>
    <div class="field"><label>총 가입기간 (년)</label><input type="number" name="years" value="{y}" min="10" max="40"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">예상 월 수령액</div><div class="metric-value" data-out="benefit">-</div></div>
    <div class="metric-box"><div class="metric-label">예상 연 수령액</div><div class="metric-value" data-out="annual">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 국민연금 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "life"))

    cus_specs = [(u, lim, cname) for u in (150, 200, 300, 500, 800, 1200) for lim, cname in ((200, "미국"), (150, "일본·중국·유럽"))]
    cus_links = [(f"{cname} 직구 ${u} 관부가세", f"life/customs-{lim}-{u}usd.html") for u, lim, cname in cus_specs]
    hubs["life"].extend(cus_links)
    for u, lim, cname in cus_specs:
        rel = f"life/customs-{lim}-{u}usd.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"2026 {cname} 해외직구 ${u} 관세·부가세 계산기 (면세 한도 ${lim})"
        desc = f"{cname} 해외직구 ${u} 구매 시 면세 한도(${lim}) 초과 여부와 관세·부가세·총 결제액을 즉시 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            (f"{cname} 해외직구 면세 한도는 얼마인가요?", f"자가사용 목적 목록통관 기준 미화 ${lim} 이하까지 관·부가세가 면제됩니다."),
            ("관세청 고시환율은 언제 기준인가요?", "결제일이 아니라 물품이 한국에 입항해 수입신고되는 주의 관세청 고시환율이 적용됩니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in cus_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#life-hub">생활금융 계산기</a> › 해외직구 관부가세</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">{esc_fn(cname)} 직구 ${u} 결제 시 관세·부가세 및 원화 총 비용을 실시간으로 계산합니다.</p>
{adsense_slot_fn(cfg, "life-cus-top")}
<section class="card" data-widget="customs-calc">
  <h2>실시간 해외직구 관부가세 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>상품 가격 (USD $)</label><input type="number" name="usd" value="{u}" step="10"></div>
    <div class="field"><label>적용 환율 (원/달러)</label><input type="number" name="fx" value="1380" step="10"></div>
    <div class="field"><label>면세 한도 (USD $)</label><input type="number" name="limit" value="{lim}"></div>
    <div class="field"><label>관세율 (%)</label><input type="number" name="duty_pct" value="8" step="1"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">예상 관세</div><div class="metric-value" data-out="duty">-</div></div>
    <div class="metric-box"><div class="metric-label">예상 부가세 (10%)</div><div class="metric-value" data-out="vat">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">총 예상 지출액</div><div class="metric-value" data-out="total">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 금액대 해외직구 관부가세 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "life"))

    jw_specs = [(d, r) for d in (50_000_000, 100_000_000, 150_000_000, 200_000_000, 300_000_000, 500_000_000) for r in (4.5, 5.5)]
    jw_links = [(f"보증금 {fmt_manwon_fn(d)} ({r}%) 전월세 전환", f"life/jw-{d // 10_000}man-{str(r).replace('.', '')}.html") for d, r in jw_specs]
    hubs["life"].extend(jw_links)
    for d, r in jw_specs:
        rel = f"life/jw-{d // 10_000}man-{str(r).replace('.', '')}.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"2026 보증금 {fmt_manwon_fn(d)} 전환율 {r}% 전월세 전환 계산기"
        desc = f"전세 보증금 {fmt_manwon_fn(d)}을 전환율 연 {r}%로 월세 전환 시 적정 월세 금액을 즉시 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            ("법정 전월세 전환율 상한은 어떻게 계산하나요?", "한국은행 기준금리 + 2.0%p를 초과할 수 없도록 주택임대차보호법으로 규정되어 있습니다."),
            ("전세대출 이자와 월세 전환율 중 무엇을 비교해야 하나요?", "전세대출 금리가 임대인의 전월세 전환율보다 낮다면 전세대출을 받아 전세로 거주하는 것이 유리합니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in jw_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#life-hub">생활금융 계산기</a> › 전월세 전환</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">전세 보증금 차액 {esc_fn(fmt_manwon_fn(d))}을 월세로 전환할 때(연 {r}%) 월 납부액을 즉시 계산합니다.</p>
{adsense_slot_fn(cfg, "life-jw-top")}
<section class="card" data-widget="jeonse-wolse-calc">
  <h2>실시간 전월세 전환율 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>전환할 보증금 차액 (원)</label><input type="number" name="deposit_diff" value="{d}" step="10000000"></div>
    <div class="field"><label>전월세 전환율 (연 %)</label><input type="number" name="rate" value="{r}" step="0.1"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">적정 월세 환산액</div><div class="metric-value" data-out="monthly">-</div></div>
    <div class="metric-box"><div class="metric-label">연간 월세 합계</div><div class="metric-value" data-out="yearly">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 보증금 전월세 전환 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "life"))

    # --- 3. Global USD Pro Calculators (/en-pro/, 44 pages: US Auto 16 + US Hourly 16 + SaaS ROI 12) ---
    enp_dir = dist / "en-pro"
    enp_dir.mkdir(parents=True, exist_ok=True)

    auto_us = [(p, m) for p in (25_000, 35_000, 45_000, 60_000) for m in (36, 48, 60, 72)]
    auto_links = [(f"${p // 1000}K Auto Loan ({m}m)", f"en-pro/us-auto-{p // 1000}k-{m}m.html") for p, m in auto_us]
    hubs["en_pro"].extend(auto_links)
    for p, m in auto_us:
        rel = f"en-pro/us-auto-{p // 1000}k-{m}m.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"${p:,} Car Loan Payment Calculator ({m} Months, 2026 APR)"
        desc = f"Estimate your monthly auto loan payment and total interest on a ${p:,} car financed for {m} months at 6.5% APR."
        faq_html, faq_ld = faq_section_fn([
            (f"What is a good down payment on a ${p:,} car?", "Putting 20% down reduces your loan balance, lowers monthly payments, and helps avoid being upside-down on the loan."),
            ("Is a 60-month or 72-month car loan better?", "Shorter terms like 48-60 months save thousands in interest compared to 72-month loans."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in auto_links if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-pro-hub">Global USD Pro Tools</a> › US Auto Loan</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Calculate monthly car payments and total interest for a ${p:,} vehicle over {m} months with custom down payment and APR.</p>
{adsense_slot_fn(cfg, "enp-auto-top")}
<section class="card" data-widget="us-auto-calc">
  <h2>US Auto Loan Payment Calculator</h2>
  <div class="calc-grid">
    <div class="field"><label>Vehicle Price (USD)</label><input type="number" name="price" value="{p}" step="1000"></div>
    <div class="field"><label>Down Payment (USD)</label><input type="number" name="down" value="{int(p * 0.2)}" step="500"></div>
    <div class="field"><label>Term (Months)</label><input type="number" name="months" value="{m}" min="12" max="84"></div>
    <div class="field"><label>APR (%)</label><input type="number" name="apr" value="6.5" step="0.25"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">Monthly Car Payment</div><div class="metric-value" data-out="monthly">-</div></div>
    <div class="metric-box"><div class="metric-label">Total Interest Paid</div><div class="metric-value" data-out="interest">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>More US Auto Loan Scenarios</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "en_pro"))

    hourly_rates = [18, 20, 22, 25, 28, 30, 35, 40, 45, 50, 60, 75, 85, 100, 125, 150]
    hr_links = [(f"${h}/hr to Annual Salary", f"en-pro/hourly-{h}-salary.html") for h in hourly_rates]
    hubs["en_pro"].extend(hr_links)
    for h in hourly_rates:
        rel = f"en-pro/hourly-{h}-salary.html"
        url = f"{cfg.site_url}/{rel}"
        annual = h * 2080
        title = f"${h} an Hour is How Much a Year? (${annual:,} Salary Breakdown)"
        desc = f"Making ${h}/hour full-time (40 hrs/week) equals ${annual:,} per year, ${annual // 12:,} per month, or ${annual // 26:,} biweekly."
        faq_html, faq_ld = faq_section_fn([
            (f"How much is ${h} an hour per year?", f"Working 40 hours per week for 52 weeks (2,080 hours), ${h}/hour equals ${annual:,} gross annual income."),
            ("How do I adjust for part-time or overtime hours?", "Change the 'Hours per Week' input above to recalculate instantly."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in hr_links if hr != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-pro-hub">Global USD Pro Tools</a> › Hourly to Salary</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Instant conversion for ${h} per hour into annual, monthly, and biweekly gross paychecks.</p>
{adsense_slot_fn(cfg, "enp-hr-top")}
<section class="card" data-widget="us-hourly-calc">
  <h2>Hourly Wage to Annual Salary Converter</h2>
  <div class="calc-grid">
    <div class="field"><label>Hourly Wage (USD)</label><input type="number" name="hourly" value="{h}" step="1"></div>
    <div class="field"><label>Hours per Week</label><input type="number" name="hours" value="40" min="1" max="80"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">Annual Salary</div><div class="metric-value" data-out="annual">${annual:,}/yr</div></div>
    <div class="metric-box"><div class="metric-label">Monthly Pay</div><div class="metric-value" data-out="monthly">-</div></div>
    <div class="metric-box"><div class="metric-label">Biweekly Pay</div><div class="metric-value" data-out="biweekly">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>More Hourly to Salary Conversions</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "en_pro"))

    saas_specs = [(p, cac) for p in (19, 49, 99, 199) for cac in (150, 400, 900)]
    saas_links = [(f"SaaS ${p}/mo (CAC ${cac}) LTV/CAC", f"en-pro/saas-ltv-{p}-cac-{cac}.html") for p, cac in saas_specs]
    hubs["en_pro"].extend(saas_links)
    for p, cac in saas_specs:
        rel = f"en-pro/saas-ltv-{p}-cac-{cac}.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"SaaS LTV:CAC & Payback Calculator (${p}/mo Plan, ${cac} CAC)"
        desc = f"Evaluate SaaS unit economics for a ${p}/month subscription with ${cac} customer acquisition cost (CAC) and monthly churn rate."
        faq_html, faq_ld = faq_section_fn([
            ("What is a healthy SaaS LTV:CAC ratio?", "Top B2B SaaS benchmarks target an LTV:CAC ratio of 3.0x or higher with a CAC payback period under 12 months."),
            ("How is SaaS LTV calculated?", "Simple LTV equals Average Monthly Revenue Per Account (ARPA) divided by monthly customer churn rate."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(hr)}">{esc_fn(lb)}</a>' for lb, hr in saas_links if hr != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#en-pro-hub">Global USD Pro Tools</a> › SaaS LTV:CAC</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Model SaaS Lifetime Value (LTV), LTV:CAC ratio, and payback period for a ${p}/month subscription business.</p>
{adsense_slot_fn(cfg, "enp-saas-top")}
<section class="card" data-widget="saas-roi-calc">
  <h2>B2B SaaS Unit Economics (LTV:CAC) Calculator</h2>
  <div class="calc-grid">
    <div class="field"><label>Monthly Subscription Price ($)</label><input type="number" name="price" value="{p}" step="5"></div>
    <div class="field"><label>Customer Acquisition Cost ($)</label><input type="number" name="cac" value="{cac}" step="25"></div>
    <div class="field"><label>Monthly Churn Rate (%)</label><input type="number" name="churn" value="4" step="0.5"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">Customer LTV</div><div class="metric-value" data-out="ltv">-</div></div>
    <div class="metric-box"><div class="metric-label">LTV : CAC Ratio</div><div class="metric-value" data-out="ratio">-</div></div>
    <div class="metric-box"><div class="metric-label">CAC Payback</div><div class="metric-value" data-out="payback">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>More SaaS Unit Economics Models</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "BusinessApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "en_pro"))

    return pages, hubs
