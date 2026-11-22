"""Ultra Expansion: KR Stock/Dividend/DCA (50p) + KR Pyeong/Area & Global Margin/Health Calculators (100p) = +150 SEO pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pseo_engine.config import SiteConfig


ULTRA_EXPANSION_JS = """
(function () {
  function fmtKrw(n) { return Math.round(n).toLocaleString('ko-KR') + '원'; }
  function fmtUsd(n) { return '$' + Math.round(n).toLocaleString('en-US'); }

  // 1. KR DCA Compound / Dividend Investor Calculator
  document.querySelectorAll('[data-widget="kr-dca-calc"]').forEach(function (root) {
    var mEl = root.querySelector('[name="monthly"]');
    var yEl = root.querySelector('[name="years"]');
    var rEl = root.querySelector('[name="rate"]');
    function update() {
      var mc = Math.max(0, Number(mEl.value || 1000000));
      var yrs = Math.max(1, Number(yEl.value || 20));
      var r = Math.max(0.1, Number(rEl.value || 8)) / 100 / 12;
      var n = yrs * 12;
      var fv = mc * ((Math.pow(1 + r, n) - 1) / r);
      var principal = mc * n;
      var gain = Math.max(0, fv - principal);
      root.querySelector('[data-out="principal"]').textContent = fmtKrw(principal);
      root.querySelector('[data-out="gain"]').textContent = fmtKrw(gain);
      root.querySelector('[data-out="fv"]').textContent = fmtKrw(fv);
    }
    [mEl, yEl, rEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 2. KR Stock Average Down (물타기 평단가)
  document.querySelectorAll('[data-widget="stock-avg-calc"]').forEach(function (root) {
    var p1 = root.querySelector('[name="p1"]');
    var q1 = root.querySelector('[name="q1"]');
    var p2 = root.querySelector('[name="p2"]');
    var q2 = root.querySelector('[name="q2"]');
    function update() {
      var a = Math.max(0, Number(p1.value || 0)), b = Math.max(0, Number(q1.value || 0));
      var c = Math.max(0, Number(p2.value || 0)), d = Math.max(0, Number(q2.value || 0));
      var totalQ = b + d;
      var totalAmt = a * b + c * d;
      var avg = totalQ > 0 ? totalAmt / totalQ : 0;
      root.querySelector('[data-out="avg"]').textContent = fmtKrw(avg);
      root.querySelector('[data-out="qty"]').textContent = totalQ.toLocaleString('ko-KR') + '주';
      root.querySelector('[data-out="amt"]').textContent = fmtKrw(totalAmt);
    }
    [p1, q1, p2, q2].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 3. KR Apartment Area m2 <-> Pyeong Converter
  document.querySelectorAll('[data-widget="pyeong-conv-calc"]').forEach(function (root) {
    var mEl = root.querySelector('[name="m2"]');
    function update() {
      var m2 = Math.max(1, Number(mEl.value || 84));
      var py = m2 / 3.305785;
      var supplyPy = py * 1.32;
      root.querySelector('[data-out="py"]').textContent = py.toFixed(2) + '평';
      root.querySelector('[data-out="supply"]').textContent = '약 ' + Math.round(supplyPy) + '평형 (공급기준)';
    }
    mEl.addEventListener('input', update);
    update();
  });

  // 4. Global Profit Margin & Markup Calculator
  document.querySelectorAll('[data-widget="margin-calc"]').forEach(function (root) {
    var cEl = root.querySelector('[name="cost"]');
    var sEl = root.querySelector('[name="sell"]');
    function update() {
      var cost = Math.max(0.01, Number(cEl.value || 50));
      var sell = Math.max(0.01, Number(sEl.value || 100));
      var profit = sell - cost;
      var margin = (profit / sell) * 100;
      var markup = (profit / cost) * 100;
      root.querySelector('[data-out="profit"]').textContent = fmtUsd(profit);
      root.querySelector('[data-out="margin"]').textContent = margin.toFixed(1) + '%';
      root.querySelector('[data-out="markup"]').textContent = markup.toFixed(1) + '%';
    }
    [cEl, sEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // 5. Global & KR BMI / TDEE Calorie Calculator
  document.querySelectorAll('[data-widget="bmi-tdee-calc"]').forEach(function (root) {
    var hEl = root.querySelector('[name="cm"]');
    var wEl = root.querySelector('[name="kg"]');
    var aEl = root.querySelector('[name="age"]');
    function update() {
      var cm = Math.max(100, Number(hEl.value || 170));
      var kg = Math.max(30, Number(wEl.value || 68));
      var age = Math.max(10, Number(aEl.value || 30));
      var bmi = kg / Math.pow(cm / 100, 2);
      var bmr = 10 * kg + 6.25 * cm - 5 * age + 5;
      var tdee = bmr * 1.375;
      root.querySelector('[data-out="bmi"]').textContent = bmi.toFixed(1);
      root.querySelector('[data-out="bmr"]').textContent = Math.round(bmr) + ' kcal';
      root.querySelector('[data-out="tdee"]').textContent = Math.round(tdee) + ' kcal/day';
    }
    [hEl, wEl, aEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });
})();
"""


def generate_ultra_expansion_pages(
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
    """Generate 150 ultra-expansion SEO pages (Invest 50 + Area/Margin/Health 100)."""
    pages: list[Any] = []
    hubs: dict[str, list[tuple[str, str]]] = {
        "invest": [],
        "convert": [],
    }

    # --- 1. KR Investment: DCA Compound (30p) + Stock Average Down (20p) = 50p ---
    inv_dir = dist / "invest"
    inv_dir.mkdir(parents=True, exist_ok=True)

    dca_specs = [(m, y, r) for m in (300_000, 500_000, 1_000_000, 2_000_000, 3_000_000) for y in (10, 20, 30) for r in (7, 10)]
    dca_links = [(f"월 {fmt_manwon_fn(m)} {y}년 연{r}% 복리", f"invest/dca-{m // 10_000}man-{y}y-{r}pct.html") for m, y, r in dca_specs]
    hubs["invest"].extend(dca_links)
    for m, y, r in dca_specs:
        rel = f"invest/dca-{m // 10_000}man-{y}y-{r}pct.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"매월 {fmt_manwon_fn(m)} {y}년 적립식 복리 계산기 (연 {r}% S&P500·배당 재투자)"
        desc = f"매월 {fmt_manwon_fn(m)}씩 {y}년간 연 {r}% 수익률로 적립식 투자(ISA·연금저축·미국 ETF) 시 복리 최종 자산과 수익금을 즉시 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            ("ISA 계좌나 연금저축에서 S&P500을 모으면 어떤 혜택이 있나요?", "배당소득세(15.4%) 과세이연 및 비과세/저율과세 혜택이 적용되어 장기 복리 효과가 크게 올라갑니다."),
            ("월 적립식 투자(DCA)의 장점은?", "주가 등락에 관계없이 매월 일정 금액을 매수해 평균 매입 단가를 낮추는 코스트 애버리징 효과를 얻을 수 있습니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in dca_links[:16] if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#invest-hub">투자·복리 계산기</a> › 월 {esc_fn(fmt_manwon_fn(m))} {y}년</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">매월 {esc_fn(fmt_manwon_fn(m))}을 {y}년 동안 연 {r}%로 복리 투자할 때 원금 대비 최종 자산을 실시간 계산합니다.</p>
{adsense_slot_fn(cfg, "inv-dca-top")}
<section class="card" data-widget="kr-dca-calc">
  <h2>실시간 월 적립식 복리 · 은퇴자산 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>월 적립 금액 (원)</label><input type="number" name="monthly" value="{m}" step="100000"></div>
    <div class="field"><label>투자 기간 (년)</label><input type="number" name="years" value="{y}" min="1" max="45"></div>
    <div class="field"><label>예상 연 수익률 (%)</label><input type="number" name="rate" value="{r}" step="0.5"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">총 납입 원금</div><div class="metric-value" data-out="principal">-</div></div>
    <div class="metric-box"><div class="metric-label">복리 투자 수익</div><div class="metric-value" data-out="gain">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">최종 예상 자산</div><div class="metric-value" data-out="fv">-</div></div>
  </div>
</section>
{affiliate_box_fn("미국주식·ISA·연금저축 수수료 무료 증권사 비교", "장기 적립식 투자 수익률을 좌우하는 거래수수료·환전우대·절세 계좌 혜택을 비교해 보세요.", "절세 증권계좌 혜택 비교", cfg.affiliate_deposit_url)}
{faq_html}
<section class="card"><h2>다른 금액·기간 복리 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "invest"))

    avg_specs = [(p1, p2) for p1 in (10_000, 30_000, 50_000, 70_000, 100_000) for p2 in (7_000, 20_000, 40_000, 80_000)]
    avg_links = [(f"{p1:,}원 → {p2:,}원 주식 물타기 평단가", f"invest/avg-{p1}-{p2}.html") for p1, p2 in avg_specs]
    hubs["invest"].extend(avg_links)
    for p1, p2 in avg_specs:
        rel = f"invest/avg-{p1}-{p2}.html"
        url = f"{cfg.site_url}/{rel}"
        title = f"주식 평단가 물타기 계산기 (기존 {p1:,}원 + 추가 매수 {p2:,}원)"
        desc = f"기존 매수가 {p1:,}원에서 {p2:,}원에 추가 매수(물타기) 시 새로운 평균 매입 단가와 총 투자금을 즉시 계산합니다."
        faq_html, faq_ld = faq_section_fn([
            ("물타기 평단가 공식은 어떻게 되나요?", "(기존 매수가×보유수량 + 추가 매수가×추가수량) ÷ 총 보유수량으로 계산됩니다."),
            ("물타기 전 반드시 확인할 점은?", "단순 평단가 낮추기보다 기업의 실적 추이와 손절·분할매수 비중 계획을 먼저 점검해야 합니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in avg_links[:12] if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#invest-hub">투자·복리 계산기</a> › 주식 물타기</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">기존 보유 단가 {p1:,}원 종목을 {p2:,}원에 추가 매수할 때 최종 평단가를 실시간 계산합니다.</p>
{adsense_slot_fn(cfg, "inv-avg-top")}
<section class="card" data-widget="stock-avg-calc">
  <h2>실시간 주식 물타기 평단가 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>기존 매수 단가 (원)</label><input type="number" name="p1" value="{p1}" step="500"></div>
    <div class="field"><label>기존 보유 수량 (주)</label><input type="number" name="q1" value="100" step="10"></div>
    <div class="field"><label>추가 매수 단가 (원)</label><input type="number" name="p2" value="{p2}" step="500"></div>
    <div class="field"><label>추가 매수 수량 (주)</label><input type="number" name="q2" value="100" step="10"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">최종 평균 단가</div><div class="metric-value" data-out="avg">-</div></div>
    <div class="metric-box"><div class="metric-label">총 보유 수량</div><div class="metric-value" data-out="qty">-</div></div>
    <div class="metric-box"><div class="metric-label">총 매수 금액</div><div class="metric-value" data-out="amt">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 구간 주식 물타기 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "invest"))

    # --- 2. Convert Hub (100p: KR Pyeong 30p + Global Margin 30p + KR/EN BMI & TDEE 40p) ---
    conv_dir = dist / "convert"
    conv_dir.mkdir(parents=True, exist_ok=True)

    # 2A. KR Apartment Area m2 -> Pyeong (30 pages)
    m2_list = [29, 33, 36, 39, 42, 46, 49, 51, 55, 59, 64, 69, 72, 74, 76, 79, 82, 84, 89, 94, 99, 101, 105, 110, 114, 120, 125, 135, 150, 165]
    py_links = [(f"전용 {m}㎡ 몇 평?", f"convert/area-{m}m2-to-pyeong.html") for m in m2_list]
    hubs["convert"].extend(py_links)
    for m in m2_list:
        rel = f"convert/area-{m}m2-to-pyeong.html"
        url = f"{cfg.site_url}/{rel}"
        py = m / 3.305785
        title = f"전용면적 {m}㎡ 몇 평? ({py:.1f}평 · 아파트 공급 평형 환산기)"
        desc = f"아파트 전용면적 {m}㎡(제곱미터)는 전용 {py:.2f}평이며, 일반 아파트 공급면적 기준 약 {round(py * 1.32)}평형에 해당합니다."
        faq_html, faq_ld = faq_section_fn([
            (f"{m}㎡는 정확히 몇 평인가요?", f"1평은 3.305785㎡이므로 {m}㎡ ÷ 3.305785 = 약 {py:.2f}평입니다."),
            ("전용면적과 공급면적(평형) 차이는?", "전용면적은 실제 거주하는 내부 공간이며, 계단·복도 등 주거공용면적을 더한 것이 공급면적(약 1.3배)입니다."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in py_links[:16] if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#convert-hub">생활·단위 변환기</a> › {m}㎡ 평수</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">아파트·오피스텔 전용면적 {m}㎡의 정확한 평수 환산과 예상 공급 평형을 즉시 확인하세요.</p>
{adsense_slot_fn(cfg, "conv-py-top")}
<section class="card" data-widget="pyeong-conv-calc">
  <h2>실시간 제곱미터(㎡) ↔ 평수 변환기</h2>
  <div class="field"><label>전용면적 (㎡)</label><input type="number" name="m2" value="{m}" step="1"></div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">전용 평수</div><div class="metric-value" data-out="py">{py:.2f}평</div></div>
    <div class="metric-box"><div class="metric-label">아파트 일반 평형</div><div class="metric-value" data-out="supply">약 {round(py * 1.32)}평형</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 아파트 면적 평수 변환</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "UtilitiesApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "convert"))

    # 2B. Global E-commerce Profit Margin & Markup (30 pages)
    margin_specs = [(c, s) for c in (10, 20, 35, 50, 75, 100) for s in (25, 49, 99, 149, 249, 399) if s > c][:30]
    mg_links = [(f"Cost ${c} -> Sell ${s} Margin", f"convert/margin-cost-{c}-sell-{s}.html") for c, s in margin_specs]
    hubs["convert"].extend(mg_links)
    for c, s in margin_specs:
        rel = f"convert/margin-cost-{c}-sell-{s}.html"
        url = f"{cfg.site_url}/{rel}"
        margin_pct = ((s - c) / s) * 100
        title = f"Profit Margin Calculator: Cost ${c} vs Selling Price ${s} ({margin_pct:.1f}% Margin)"
        desc = f"Buying at ${c} and selling at ${s} yields ${s - c} gross profit, {margin_pct:.1f}% profit margin, and {((s - c) / c) * 100:.1f}% markup."
        faq_html, faq_ld = faq_section_fn([
            ("What is the difference between margin and markup?", "Gross margin is profit divided by selling price, whereas markup is profit divided by cost."),
            ("What is a healthy e-commerce gross margin?", "Most profitable Shopify and Amazon FBA brands aim for 50%–70% gross margin before ad spend."),
        ])
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in mg_links[:14] if h != rel)
        body = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#convert-hub">Converters &amp; Margin</a> › Profit Margin</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">Instant e-commerce &amp; retail gross profit margin and markup calculator for ${c} COGS and ${s} retail price.</p>
{adsense_slot_fn(cfg, "conv-mg-top")}
<section class="card" data-widget="margin-calc">
  <h2>Profit Margin &amp; Markup Calculator (USD)</h2>
  <div class="calc-grid">
    <div class="field"><label>Product Cost / COGS ($)</label><input type="number" name="cost" value="{c}" step="1"></div>
    <div class="field"><label>Selling Price ($)</label><input type="number" name="sell" value="{s}" step="1"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">Gross Profit</div><div class="metric-value" data-out="profit">${s - c}</div></div>
    <div class="metric-box highlight"><div class="metric-label">Profit Margin</div><div class="metric-value" data-out="margin">{margin_pct:.1f}%</div></div>
    <div class="metric-box"><div class="metric-label">Markup</div><div class="metric-value" data-out="markup">{((s - c) / c) * 100:.1f}%</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>More Margin &amp; Pricing Scenarios</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "BusinessApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "convert"))

    # 2C. KR & EN BMI / TDEE Calorie Calculators (40 pages: 20 KR + 20 EN)
    body_specs = [(cm, kg) for cm in (158, 165, 172, 178, 183) for kg in (52, 62, 72, 85)]
    bmi_links_kr = [(f"키 {cm}cm {kg}kg BMI·기초대사량", f"convert/bmi-kr-{cm}cm-{kg}kg.html") for cm, kg in body_specs]
    bmi_links_en = [(f"BMI & TDEE {cm}cm {kg}kg", f"convert/bmi-en-{cm}cm-{kg}kg.html") for cm, kg in body_specs]
    hubs["convert"].extend(bmi_links_kr)
    hubs["convert"].extend(bmi_links_en)

    for cm, kg in body_specs:
        bmi = kg / ((cm / 100) ** 2)
        # KR
        rel_kr = f"convert/bmi-kr-{cm}cm-{kg}kg.html"
        url_kr = f"{cfg.site_url}/{rel_kr}"
        title_kr = f"키 {cm}cm 몸무게 {kg}kg BMI 비만도 · 기초대사량(TDEE) 칼로리 계산기"
        desc_kr = f"신장 {cm}cm, 체중 {kg}kg의 BMI 지수는 {bmi:.1f}입니다. 다이어트 권장 칼로리(TDEE)와 기초대사량(BMR)을 즉시 계산하세요."
        faq_html, faq_ld = faq_section_fn([
            (f"키 {cm}cm {kg}kg의 BMI {bmi:.1f}은 어느 구간인가요?", "대한비만학회 기준 18.5 미만 저체중, 18.5~22.9 정상, 23~24.9 과체중, 25 이상 비만으로 분류합니다."),
            ("체지방 감량을 위한 하루 섭취 칼로리는?", "위 계산기의 하루 유지 칼로리(TDEE)에서 300~500kcal 적게 섭취하는 것이 건강한 감량 속도입니다."),
        ])
        related_kr = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in bmi_links_kr[:12] if h != rel_kr)
        body_kr = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#convert-hub">건강·생활 계산기</a> › BMI·칼로리</nav>
<h1>{esc_fn(title_kr)}</h1>
<p class="lead">키 {cm}cm, 몸무게 {kg}kg 기준 BMI 비만도, 기초대사량(BMR), 하루 소비 칼로리(TDEE)를 실시간 계산합니다.</p>
{adsense_slot_fn(cfg, "conv-bmi-kr")}
<section class="card" data-widget="bmi-tdee-calc">
  <h2>실시간 BMI · 기초대사량 · TDEE 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>신장 (cm)</label><input type="number" name="cm" value="{cm}"></div>
    <div class="field"><label>체중 (kg)</label><input type="number" name="kg" value="{kg}"></div>
    <div class="field"><label>만 나이 (세)</label><input type="number" name="age" value="30"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">BMI 지수</div><div class="metric-value" data-out="bmi">{bmi:.1f}</div></div>
    <div class="metric-box"><div class="metric-label">기초대사량 (BMR)</div><div class="metric-value" data-out="bmr">-</div></div>
    <div class="metric-box"><div class="metric-label">유지 칼로리 (TDEE)</div><div class="metric-value" data-out="tdee">-</div></div>
  </div>
</section>
{faq_html}
<section class="card"><h2>다른 체형 BMI·칼로리 계산기</h2><div class="link-grid">{related_kr}</div></section>
"""
        (dist / rel_kr).write_text(
            base_layout_fn(cfg, title=title_kr, description=desc_kr, canonical_url=url_kr, body_html=body_kr,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title_kr, "url": url_kr, "applicationCategory": "HealthApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_kr, url_kr, title_kr, desc_kr, "convert"))

        # EN
        rel_en = f"convert/bmi-en-{cm}cm-{kg}kg.html"
        url_en = f"{cfg.site_url}/{rel_en}"
        title_en = f"BMI & TDEE Calorie Calculator for {cm} cm, {kg} kg (BMI {bmi:.1f})"
        desc_en = f"At {cm} cm and {kg} kg, your BMI is {bmi:.1f}. Calculate exact BMR and daily maintenance calories (TDEE) for fat loss or muscle gain."
        faq_html_en, faq_ld_en = faq_section_fn([
            (f"Is a BMI of {bmi:.1f} healthy?", "Standard WHO BMI ranges classify 18.5 to 24.9 as normal weight, though muscle mass should also be considered."),
            ("How many calories for safe weight loss?", "A 300–500 kcal daily deficit below your TDEE supports sustainable fat loss of ~0.5 kg per week."),
        ])
        related_en = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in bmi_links_en[:12] if h != rel_en)
        body_en = f"""
<nav class="breadcrumb"><a href="../index.html">Home</a> › <a href="../index.html#convert-hub">Health &amp; Converters</a> › BMI &amp; TDEE</nav>
<h1>{esc_fn(title_en)}</h1>
<p class="lead">Instant Mifflin-St Jeor BMR, TDEE daily calorie target, and BMI calculator for {cm} cm and {kg} kg.</p>
{adsense_slot_fn(cfg, "conv-bmi-en")}
<section class="card" data-widget="bmi-tdee-calc">
  <h2>Interactive BMI, BMR &amp; TDEE Calculator</h2>
  <div class="calc-grid">
    <div class="field"><label>Height (cm)</label><input type="number" name="cm" value="{cm}"></div>
    <div class="field"><label>Weight (kg)</label><input type="number" name="kg" value="{kg}"></div>
    <div class="field"><label>Age (years)</label><input type="number" name="age" value="30"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">BMI Score</div><div class="metric-value" data-out="bmi">{bmi:.1f}</div></div>
    <div class="metric-box"><div class="metric-label">Basal Metabolic Rate</div><div class="metric-value" data-out="bmr">-</div></div>
    <div class="metric-box"><div class="metric-label">Maintenance Calories</div><div class="metric-value" data-out="tdee">-</div></div>
  </div>
</section>
{faq_html_en}
<section class="card"><h2>More BMI &amp; Calorie Profiles</h2><div class="link-grid">{related_en}</div></section>
"""
        (dist / rel_en).write_text(
            base_layout_fn(cfg, title=title_en, description=desc_en, canonical_url=url_en, body_html=body_en,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title_en, "url": url_en, "applicationCategory": "HealthApplication"}, faq_ld_en],
                           asset_prefix="../", is_sample_data=is_sample_data),
            encoding="utf-8",
        )
        pages.append(page_cls(rel_en, url_en, title_en, desc_en, "convert"))

    return pages, hubs
