"""4-Branch Real-Time Public Data Revenue Pipelines (MOLIT Apt, ApplyHome, K-Startup, HIRA Non-Payment)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from pseo_engine.config import SiteConfig


@dataclass
class AptTrade:
    region_slug: str
    region_name: str
    apt_name: str
    dong: str
    area_m2: float
    floor: str
    build_year: str
    deal_amount_man: int
    deal_date: str


@dataclass
class CheongyakNotice:
    house_name: str
    region: str
    builder: str
    supply_count: int
    receipt_period: str
    winner_date: str
    detail_url: str


@dataclass
class StartupNotice:
    title: str
    category: str
    region: str
    org_name: str
    target: str
    deadline: str
    detail_url: str


@dataclass
class MedicalItem:
    code: str
    category: str
    name: str
    description: str


APT_REGIONS: list[tuple[str, str, str]] = [
    ("gangnam", "서울 강남구", "11680"),
    ("seocho", "서울 서초구", "11650"),
    ("songpa", "서울 송파구", "11710"),
    ("mapo", "서울 마포구", "11440"),
    ("seongdong", "서울 성동구", "11200"),
    ("yeongdeungpo", "서울 영등포구", "11560"),
    ("bundang", "경기 성남 분당구", "41135"),
    ("yeongtong", "경기 수원 영통구", "41117"),
    ("yeonsu", "인천 연수구", "28185"),
    ("haeundae", "부산 해운대구", "26350"),
]


PUBLIC_HUBS_JS = """
(function () {
  function fmtKrw(n) { return Math.round(n).toLocaleString('ko-KR') + '원'; }

  // Apt Pyeong-price & Mortgage Estimator
  document.querySelectorAll('[data-widget="apt-pyeong-calc"]').forEach(function (root) {
    var pEl = root.querySelector('[name="price_eok"]');
    var aEl = root.querySelector('[name="area_m2"]');
    var ltvEl = root.querySelector('[name="ltv"]');
    function update() {
      var eok = Math.max(0.5, Number(pEl.value || 10));
      var area = Math.max(10, Number(aEl.value || 84));
      var ltv = Math.min(80, Math.max(0, Number(ltvEl.value || 60)));
      var krw = eok * 100000000;
      var pyeong = area / 3.3058;
      var perPyeong = krw / pyeong;
      var loan = krw * (ltv / 100);
      var mr = 0.04 / 12;
      var m = 360;
      var pmt = loan * (mr * Math.pow(1 + mr, m)) / (Math.pow(1 + mr, m) - 1);
      root.querySelector('[data-out="pyeong"]').textContent = pyeong.toFixed(1) + '평';
      root.querySelector('[data-out="per_pyeong"]').textContent = Math.round(perPyeong / 10000).toLocaleString('ko-KR') + '만 원/평';
      root.querySelector('[data-out="monthly"]').textContent = fmtKrw(pmt);
    }
    [pEl, aEl, ltvEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });

  // Cheongyak 84-point Score Calculator
  document.querySelectorAll('[data-widget="cheongyak-score-calc"]').forEach(function (root) {
    var hEl = root.querySelector('[name="homeless"]');
    var dEl = root.querySelector('[name="dependents"]');
    var tEl = root.querySelector('[name="account"]');
    function update() {
      var h = Number(hEl.value || 0);
      var d = Number(dEl.value || 0);
      var t = Number(tEl.value || 0);
      var total = h + d + t;
      root.querySelector('[data-out="total"]').textContent = total + '점 / 84점';
      var tier = total >= 65 ? '서울·수도권 인기 단지 당첨권' : (total >= 50 ? '수도권 외곽·지방 핵심지 경쟁권' : '추첨제·특별공급·무순위(줍줍) 병행 권장');
      root.querySelector('[data-out="tier"]').textContent = tier;
    }
    [hEl, dEl, tEl].forEach(function (e) { e.addEventListener('change', update); });
    update();
  });

  // K-Startup Keyword Filter
  document.querySelectorAll('[data-widget="startup-filter"]').forEach(function (root) {
    var qEl = root.querySelector('[name="query"]');
    var rows = root.querySelectorAll('[data-startup-row]');
    var out = root.querySelector('[data-out="count"]');
    function update() {
      var q = (qEl.value || '').trim().toLowerCase();
      var vis = 0;
      rows.forEach(function (r) {
        var match = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
        r.style.display = match ? '' : 'none';
        if (match) vis += 1;
      });
      out.textContent = vis + '건의 지원사업 공고가 검색되었습니다.';
    }
    qEl.addEventListener('input', update);
    update();
  });

  // 4th-gen Silson Insurance Co-pay Calculator
  document.querySelectorAll('[data-widget="silson-calc"]').forEach(function (root) {
    var cEl = root.querySelector('[name="covered"]');
    var ncEl = root.querySelector('[name="noncovered"]');
    function update() {
      var cov = Math.max(0, Number(cEl.value || 0));
      var ncov = Math.max(0, Number(ncEl.value || 0));
      var selfCov = Math.max(cov > 0 ? 10000 : 0, cov * 0.20);
      var selfNcov = Math.max(ncov > 0 ? 30000 : 0, ncov * 0.30);
      var totalCost = cov + ncov;
      var totalSelf = Math.min(totalCost, selfCov + selfNcov);
      var refund = Math.max(0, totalCost - totalSelf);
      root.querySelector('[data-out="self"]').textContent = fmtKrw(totalSelf);
      root.querySelector('[data-out="refund"]').textContent = fmtKrw(refund);
    }
    [cEl, ncEl].forEach(function (e) { e.addEventListener('input', update); });
    update();
  });
})();
"""


def _http_get_text(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; pSEO-Autopilot/2.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _default_deal_ymd() -> str:
    # 전월 기준 자동 계산 (당월 실거래 신고 지연 고려)
    first_of_month = datetime.now(timezone.utc).replace(day=1)
    prev_month = first_of_month - timedelta(days=1)
    return prev_month.strftime("%Y%m")


def fetch_apt_trades(cfg: SiteConfig) -> tuple[dict[str, list[AptTrade]], str]:
    """Fetch recent MOLIT apartment trades for 10 major Korean districts."""
    by_region: dict[str, list[AptTrade]] = {slug: [] for slug, _, _ in APT_REGIONS}
    if not cfg.dry_run and cfg.data_go_kr_api_key:
        key = urllib.parse.unquote(cfg.data_go_kr_api_key)
        deal_ymd = _default_deal_ymd()
        total_live = 0
        for slug, name, code in APT_REGIONS:
            qs = urllib.parse.urlencode(
                {
                    "serviceKey": key,
                    "LAWD_CD": code,
                    "DEAL_YMD": deal_ymd,
                    "pageNo": "1",
                    "numOfRows": "15",
                }
            )
            url = f"https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade?{qs}"
            try:
                xml_text = _http_get_text(url, timeout=8)
                root = ET.fromstring(xml_text)
                for item in root.findall(".//item"):
                    apt_nm = (item.findtext("aptNm") or "").strip()
                    amt_raw = (item.findtext("dealAmount") or "0").replace(",", "").strip()
                    if not apt_nm or not amt_raw.isdigit():
                        continue
                    y = (item.findtext("dealYear") or "").strip()
                    m = (item.findtext("dealMonth") or "").strip().zfill(2)
                    d = (item.findtext("dealDay") or "").strip().zfill(2)
                    by_region[slug].append(
                        AptTrade(
                            region_slug=slug,
                            region_name=name,
                            apt_name=apt_nm,
                            dong=(item.findtext("umdNm") or "").strip(),
                            area_m2=round(float(item.findtext("excluUseAr") or 84.0), 2),
                            floor=(item.findtext("floor") or "-").strip(),
                            build_year=(item.findtext("buildYear") or "-").strip(),
                            deal_amount_man=int(amt_raw),
                            deal_date=f"{y}-{m}-{d}",
                        )
                    )
                    total_live += 1
            except (urllib.error.URLError, TimeoutError, ET.ParseError, ValueError):
                continue
        if total_live > 0:
            return by_region, "live_molit_apt_api"

    # Fallback seed
    for slug, name, _ in APT_REGIONS:
        by_region[slug] = [
            AptTrade(slug, name, f"{name} 대표단지(샘플)", "중심동", 84.95, "15", "2018", 125000, "2026-10-20"),
            AptTrade(slug, name, f"{name} 역세권파크(샘플)", "중앙동", 59.92, "10", "2020", 92000, "2026-10-18"),
        ]
    return by_region, "seed_fallback_2026"


def fetch_cheongyak_notices(cfg: SiteConfig) -> tuple[list[CheongyakNotice], str]:
    """Fetch latest ApplyHome APT subscription notices."""
    if not cfg.dry_run and cfg.data_go_kr_api_key:
        key = urllib.parse.unquote(cfg.data_go_kr_api_key)
        qs = urllib.parse.urlencode({"page": "1", "perPage": "50", "serviceKey": key})
        url = f"https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail?{qs}"
        try:
            payload = json.loads(_http_get_text(url, timeout=10))
            items: list[CheongyakNotice] = []
            for row in payload.get("data", []):
                name = str(row.get("HOUSE_NM") or "").strip()
                if not name:
                    continue
                items.append(
                    CheongyakNotice(
                        house_name=name,
                        region=str(row.get("SUBSCRPT_AREA_CODE_NM") or "전국").strip(),
                        builder=str(row.get("CNSTRCT_ENTRPS_NM") or row.get("BSNS_MBY_NM") or "-").strip(),
                        supply_count=int(row.get("TOT_SUPLY_HSHLDCO") or 0),
                        receipt_period=f"{row.get('RCEPT_BGNDE') or '-'} ~ {row.get('RCEPT_ENDDE') or '-'}",
                        winner_date=str(row.get("PRZWNER_PRESNATN_DE") or "-").strip(),
                        detail_url=str(row.get("PBLANC_URL") or "https://www.applyhome.co.kr").strip(),
                    )
                )
            if items:
                return items, "live_applyhome_api"
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            pass

    return [
        CheongyakNotice("서울 역세권 공공분양(샘플)", "서울", "LH/SH", 420, "2026-11-25 ~ 2026-11-27", "2026-12-05", "https://www.applyhome.co.kr"),
        CheongyakNotice("경기 신도시 민간분양(샘플)", "경기", "시공사", 650, "2026-11-28 ~ 2026-11-30", "2026-12-08", "https://www.applyhome.co.kr"),
    ], "seed_fallback_2026"


def fetch_startup_notices(cfg: SiteConfig) -> tuple[list[StartupNotice], str]:
    """Fetch active K-Startup government grant & incubation announcements."""
    if not cfg.dry_run and cfg.data_go_kr_api_key:
        key = urllib.parse.unquote(cfg.data_go_kr_api_key)
        qs = urllib.parse.urlencode(
            {
                "serviceKey": key,
                "pageNo": "1",
                "numOfRows": "40",
                "rcrtPrgsYn": "Y",
                "returnType": "json",
            }
        )
        url = f"https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01?{qs}"
        try:
            payload = json.loads(_http_get_text(url, timeout=10))
            items: list[StartupNotice] = []
            for row in payload.get("data", []):
                title = str(row.get("biz_pbanc_nm") or "").strip()
                if not title:
                    continue
                end_dt = str(row.get("pbanc_rcpt_end_dt") or "-")
                if len(end_dt) == 8 and end_dt.isdigit():
                    end_dt = f"{end_dt[:4]}-{end_dt[4:6]}-{end_dt[6:]}"
                items.append(
                    StartupNotice(
                        title=title,
                        category=str(row.get("supt_biz_clsfc") or "사업화").strip(),
                        region=str(row.get("supt_regin") or "전국").strip(),
                        org_name=str(row.get("pbanc_ntrp_nm") or "창업진흥원").strip(),
                        target=str(row.get("aply_trgt") or "예비·초기창업자").strip(),
                        deadline=end_dt,
                        detail_url=str(row.get("detl_pg_url") or "https://www.k-startup.go.kr").strip(),
                    )
                )
            if items:
                return items, "live_kstartup_api"
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            pass

    return [
        StartupNotice("2026 예비창업패키지 지원사업(샘플)", "사업화", "전국", "창업진흥원", "예비창업자", "2026-12-15", "https://www.k-startup.go.kr"),
        StartupNotice("초기창업기업 공간·보육 입주 모집(샘플)", "시설ㆍ공간ㆍ보육", "서울", "서울창업허브", "3년 미만 기업", "2026-12-20", "https://www.k-startup.go.kr"),
    ], "seed_fallback_2026"


def fetch_medical_items(cfg: SiteConfig) -> tuple[list[MedicalItem], str]:
    """Fetch HIRA non-payment medical item codes and official descriptions."""
    if not cfg.dry_run and cfg.data_go_kr_api_key:
        key = urllib.parse.unquote(cfg.data_go_kr_api_key)
        qs = urllib.parse.urlencode({"serviceKey": key, "pageNo": "1", "numOfRows": "40"})
        url = f"https://apis.data.go.kr/B551182/nonPaymentDamtInfoService/getNonPaymentItemCodeList?{qs}"
        try:
            root = ET.fromstring(_http_get_text(url, timeout=10))
            items: list[MedicalItem] = []
            for item in root.findall(".//item"):
                cat = (item.findtext("divCd1Nm") or "비급여 항목").strip()
                name = (item.findtext("npayKorNm") or item.findtext("divCd2Nm") or "").strip()
                desc = (item.findtext("divCd2Dsc") or item.findtext("divCd1Dsc") or "건강보험심사평가원 고시 비급여 항목").strip()
                code = (item.findtext("npayCd") or item.findtext("divCd2") or "NPAY").strip()
                if not name:
                    continue
                items.append(MedicalItem(code=code, category=cat, name=name, description=desc[:160]))
            if items:
                return items, "live_hira_medical_api"
        except (urllib.error.URLError, TimeoutError, ET.ParseError):
            pass

    return [
        MedicalItem("A1100", "상급병실료차액", "1인실 입원료 차액", "건강보험 적용 병실 외 1인실 이용 시 발생하는 비급여 차액"),
        MedicalItem("C1000", "도수치료·재활", "도수치료 (물리치료)", "근골격계 통증·체형 교정 등을 위한 비급여 수기 치료"),
        MedicalItem("D1000", "MRI·초음파", "척추·관절 MRI 검사", "건강보험 급여 기준 외 진단 목적의 자기공명영상 검사"),
        MedicalItem("E1000", "치과·임플란트", "치과 임플란트 (비급여)", "만 65세 미만 또는 급여 개수 초과 시 적용되는 비급여 임플란트"),
    ], "seed_fallback_2026"


def generate_public_hub_pages(
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
) -> tuple[list[Any], dict[str, list[tuple[str, str]]], dict[str, str]]:
    """Generate 30 real-time public-data hub pages across 4 high-CPC verticals."""
    apt_by_reg, apt_src = fetch_apt_trades(cfg)
    cheongyak_list, ch_src = fetch_cheongyak_notices(cfg)
    startup_list, ks_src = fetch_startup_notices(cfg)
    med_list, med_src = fetch_medical_items(cfg)

    sources = {"apt": apt_src, "cheongyak": ch_src, "startup": ks_src, "medical": med_src}
    pages: list[Any] = []
    hub_links: dict[str, list[tuple[str, str]]] = {
        "apt": [],
        "cheongyak": [],
        "startup": [],
        "medical": [],
    }

    # --- 갈래 2: 지역별 아파트 매매 실거래가 허브 (10페이지) ---
    apt_dir = dist / "apt"
    apt_dir.mkdir(parents=True, exist_ok=True)
    for slug, rname, _ in APT_REGIONS:
        hub_links["apt"].append((f"{rname} 아파트 실거래가", f"apt/{slug}.html"))

    for slug, rname, _ in APT_REGIONS:
        rel = f"apt/{slug}.html"
        url = f"{cfg.site_url}/{rel}"
        trades = apt_by_reg.get(slug, [])
        avg_eok = round(sum(t.deal_amount_man for t in trades) / max(1, len(trades)) / 10000, 1) if trades else 10.0
        rows_html = "".join(
            f"<tr><td><strong>{esc_fn(t.apt_name)}</strong><br><small>{esc_fn(t.dong)} ({esc_fn(t.build_year)}년)</small></td>"
            f"<td>{t.area_m2:.1f}㎡ ({t.area_m2 / 3.3058:.1f}평)</td>"
            f"<td>{esc_fn(t.floor)}층</td>"
            f"<td><strong>{t.deal_amount_man / 10000:.2f}억 원</strong></td>"
            f"<td>{esc_fn(t.deal_date)}</td></tr>"
            for t in trades[:12]
        ) or "<tr><td colspan='5'>최근 신고된 거래가 집계 중입니다.</td></tr>"
        title = f"2026 {rname} 아파트 매매 실거래가 조회 & 평당가·주담대 계산기"
        desc = f"국토교통부 공식 실거래가 API 기반 {rname} 최신 아파트 매매 거래 {len(trades)}건, 평당가 및 주택담보대출 월 상환액 실시간 계산."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hub_links["apt"] if h != rel)
        faq_html, faq_ld = faq_section_fn([
            (f"{rname} 아파트 실거래가는 얼마나 자주 갱신되나요?", "국토교통부 실거래가 공개시스템 오픈 API를 통해 매일 새벽 자동으로 최신 신고 거래가 반영됩니다."),
            ("전용면적 84㎡는 몇 평인가요?", "전용 84㎡는 약 25.4평이며, 공용면적을 포함한 공급면적 기준으로는 흔히 말하는 32~34평형(국민평형)에 해당합니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#apt-hub">아파트 실거래가</a> › {esc_fn(rname)}</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">국토교통부 아파트 매매 실거래가 공공 API 데이터를 매일 자동 반영합니다. {esc_fn(rname)} 최신 신고 거래와 평당가·주담대 월 부담액을 바로 확인하세요.</p>
{adsense_slot_fn(cfg, f"apt-{slug}-top")}
<section class="card" data-widget="apt-pyeong-calc">
  <h2>{esc_fn(rname)} 평당가 · 주담대 월 상환액 즉시 계산</h2>
  <div class="calc-grid">
    <div class="field"><label>매매가 (억 원)</label><input type="number" name="price_eok" value="{avg_eok}" step="0.5"></div>
    <div class="field"><label>전용면적 (㎡)</label><input type="number" name="area_m2" value="84" step="1"></div>
    <div class="field"><label>주담대 LTV 비율 (%)</label><input type="number" name="ltv" value="60" min="0" max="80"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">전용 평수</div><div class="metric-value" data-out="pyeong">25.4평</div></div>
    <div class="metric-box"><div class="metric-label">전용 평당가</div><div class="metric-value" data-out="per_pyeong">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">30년 주담대 월 상환액 (연 4%)</div><div class="metric-value" data-out="monthly">-</div></div>
  </div>
</section>
<section class="card">
  <h2>{esc_fn(rname)} 최근 아파트 매매 실거래 내역</h2>
  <table><thead><tr><th>단지명 (동/연식)</th><th>전용면적</th><th>층</th><th>실거래가</th><th>계약일</th></tr></thead><tbody>{rows_html}</tbody></table>
</section>
{affiliate_box_fn(f"{rname} 아파트 매수·갈아타기 — 1금융권 주담대 최저금리 비교", "잔금 전 주택담보대출 최저금리와 이사·인테리어 견적을 한 번에 비교해 수백만 원을 아끼세요.", "주담대 최저금리 비교하기", cfg.affiliate_loan_url)}
{faq_html}
<section class="card"><h2>다른 지역 아파트 실거래가</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data or apt_src.startswith("seed_")),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "apt"))

    # --- 갈래 3: 청약홈 분양 일정 & 84점 청약가점 계산기 (8페이지) ---
    ch_dir = dist / "cheongyak"
    ch_dir.mkdir(parents=True, exist_ok=True)
    ch_regions = [
        ("all", "전국"), ("seoul", "서울"), ("gyeonggi", "경기"), ("incheon", "인천"),
        ("busan", "부산"), ("daegu", "대구"), ("daejeon", "대전"), ("gwangju", "광주"),
    ]
    for rslug, rname in ch_regions:
        hub_links["cheongyak"].append((f"{rname} 아파트 청약 일정", f"cheongyak/{rslug}.html"))

    for rslug, rname in ch_regions:
        rel = f"cheongyak/{rslug}.html"
        url = f"{cfg.site_url}/{rel}"
        filtered = cheongyak_list if rslug == "all" else [c for c in cheongyak_list if rname in c.region]
        if not filtered:
            filtered = cheongyak_list[:10]
        rows_html = "".join(
            f"<tr><td><strong>{esc_fn(c.house_name)}</strong><br><small>{esc_fn(c.region)} · {esc_fn(c.builder)}</small></td>"
            f"<td>{c.supply_count:,}세대</td><td>{esc_fn(c.receipt_period)}</td><td>{esc_fn(c.winner_date)}</td>"
            f"<td><a href='{esc_fn(c.detail_url)}' rel='noopener noreferrer' target='_blank'>공고 보기 ↗</a></td></tr>"
            for c in filtered[:15]
        )
        title = f"2026 {rname} 아파트 청약홈 분양 일정 & 84점 청약가점 계산기"
        desc = f"한국부동산원 청약홈 공식 API 기반 {rname} 최신 아파트 분양 공고 {len(filtered)}건 접수일정 및 84점 만점 청약가점 실시간 계산기."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hub_links["cheongyak"] if h != rel)
        faq_html, faq_ld = faq_section_fn([
            ("청약가점 84점은 어떻게 구성되나요?", "무주택기간(최대 32점) + 부양가족수(최대 35점) + 청약통장 가입기간(최대 17점)으로 합계 84점 만점입니다."),
            ("가점이 낮아도 당첨될 수 있는 방법이 있나요?", "전용 85㎡ 초과 추첨제 물량, 신혼부부·생애최초 특별공급, 그리고 청약통장이 필요 없는 무순위(줍줍) 청약을 노려볼 수 있습니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#cheongyak-hub">청약홈 분양 일정</a> › {esc_fn(rname)}</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">한국부동산원 청약홈 공식 오픈 API 데이터를 매일 자동 반영하여 {esc_fn(rname)} 최신 분양 공고와 내 청약가점을 즉시 계산합니다.</p>
{adsense_slot_fn(cfg, f"ch-{rslug}-top")}
<section class="card" data-widget="cheongyak-score-calc">
  <h2>84점 만점 청약가점 실시간 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>무주택기간 (최대 32점)</label>
      <select name="homeless"><option value="2">1년 미만 (2점)</option><option value="10">4~5년 (10점)</option><option value="16" selected>7~8년 (16점)</option><option value="22">10~11년 (22점)</option><option value="32">15년 이상 (32점)</option></select>
    </div>
    <div class="field"><label>부양가족 수 (최대 35점)</label>
      <select name="dependents"><option value="5">0명 (5점)</option><option value="10">1명 (10점)</option><option value="15" selected>2명 (15점)</option><option value="20">3명 (20점)</option><option value="25">4명 (25점)</option><option value="35">6명 이상 (35점)</option></select>
    </div>
    <div class="field"><label>청약통장 가입기간 (최대 17점)</label>
      <select name="account"><option value="4">2~3년 (4점)</option><option value="8">6~7년 (8점)</option><option value="12" selected>10~11년 (12점)</option><option value="17">15년 이상 (17점)</option></select>
    </div>
  </div>
  <div class="result-strip">
    <div class="metric-box highlight"><div class="metric-label">내 청약가점</div><div class="metric-value" data-out="total">43점 / 84점</div></div>
    <div class="metric-box"><div class="metric-label">당첨 전략 진단</div><div class="metric-value" style="font-size:0.98rem;" data-out="tier">계산 중...</div></div>
  </div>
</section>
<section class="card">
  <h2>{esc_fn(rname)} 최신 청약홈 분양 공고 목록</h2>
  <table><thead><tr><th>단지명 (지역/시공사)</th><th>공급세대</th><th>접수기간</th><th>당첨발표</th><th>공식공고</th></tr></thead><tbody>{rows_html}</tbody></table>
</section>
{affiliate_box_fn("청약 당첨 후 중도금·잔금 대출 최저금리 미리 비교", "신혼부부·생애최초 디딤돌 대출과 1금융권 주담대 한도를 미리 계산해 두세요.", "내 대출 한도·금리 비교하기", cfg.affiliate_loan_url)}
{faq_html}
<section class="card"><h2>다른 지역 청약홈 분양 일정</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "FinanceApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data or ch_src.startswith("seed_")),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "cheongyak"))

    # --- 갈래 4: K-Startup 정부 창업·소상공인 지원사업 실시간 공고 허브 (6페이지) ---
    st_dir = dist / "startup"
    st_dir.mkdir(parents=True, exist_ok=True)
    st_cats = [
        ("all", "전체 모집중"), ("business", "사업화"), ("space", "시설·공간·보육"),
        ("rnd", "기술개발(R&D)"), ("global", "글로벌·판로"), ("edu", "멘토링·교육"),
    ]
    for cslug, cname in st_cats:
        hub_links["startup"].append((f"2026 {cname} 창업지원", f"startup/{cslug}.html"))

    for cslug, cname in st_cats:
        rel = f"startup/{cslug}.html"
        url = f"{cfg.site_url}/{rel}"
        if cslug == "all":
            filtered = startup_list
        else:
            kw = cname.split("·")[0].split("(")[0]
            filtered = [s for s in startup_list if kw in s.category or kw in s.title] or startup_list[:10]
        rows_html = "".join(
            f"<tr data-startup-row='1'><td><strong>{esc_fn(s.title)}</strong><br><small>{esc_fn(s.org_name)}</small></td>"
            f"<td><span class='tag'>{esc_fn(s.category)}</span></td><td>{esc_fn(s.region)}</td><td>{esc_fn(s.deadline)}</td>"
            f"<td><a href='{esc_fn(s.detail_url)}' rel='noopener noreferrer' target='_blank'>상세 ↗</a></td></tr>"
            for s in filtered[:20]
        )
        title = f"2026 K-Startup {cname} 정부 창업지원사업 실시간 공고 모음"
        desc = f"창업진흥원 K-Startup 공식 API 기반 2026년 {cname} 분야 정부 지원사업·보조금·입주 공고 {len(filtered)}건 실시간 조회."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hub_links["startup"] if h != rel)
        faq_html, faq_ld = faq_section_fn([
            ("예비창업자도 정부 창업지원금을 받을 수 있나요?", "네, 사업자등록 전 단계에서도 예비창업패키지·보육센터 입주·지자체 창업지원 공고에 신청할 수 있습니다."),
            ("지원사업 공고는 얼마나 자주 업데이트되나요?", "창업진흥원 K-Startup 오픈 API를 통해 매일 새벽 모집 진행 중인 최신 공고가 자동 갱신됩니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#startup-hub">K-Startup 창업지원</a> › {esc_fn(cname)}</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">창업진흥원 K-Startup 공식 API에서 현재 모집 중인 {esc_fn(cname)} 정부 지원사업 공고를 매일 자동 수집해 정리합니다.</p>
{adsense_slot_fn(cfg, f"st-{cslug}-top")}
<section class="card" data-widget="startup-filter">
  <h2>모집 공고 키워드 실시간 필터</h2>
  <div class="field"><label>지역·키워드 검색 (예: 서울, 경기, AI, 여성, 입주, 사업화)</label><input type="search" name="query" placeholder="키워드를 입력하면 아래 표가 즉시 필터링됩니다..."></div>
  <p data-out="count" style="font-weight:700;margin-top:10px;"></p>
  <table><thead><tr><th>지원사업 공고명 (주관기관)</th><th>분야</th><th>지역</th><th>마감일</th><th>신청</th></tr></thead><tbody>{rows_html}</tbody></table>
</section>
{affiliate_box_fn("창업자·개인사업자 정책자금 대출 & 세무기장 비용 비교", "정부 지원사업과 함께 저금리 소상공인 정책자금·법인카드·세무 자동화 혜택을 비교하세요.", "사업자 금융·세무 혜택 보기", cfg.affiliate_subsidy_url)}
{faq_html}
<section class="card"><h2>다른 분야 K-Startup 지원사업</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "BusinessApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data or ks_src.startswith("seed_")),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "startup"))

    # --- 갈래 5: 건강보험심사평가원 비급여 진료비 안내 & 4세대 실손보험 계산기 (6페이지) ---
    med_dir = dist / "medical"
    med_dir.mkdir(parents=True, exist_ok=True)
    med_cats = [
        ("all", "전체 주요 비급여"), ("room", "상급병실료(1인실)"), ("mri", "MRI·초음파 검사"),
        ("manual", "도수치료·재활"), ("dental", "치과·임플란트"), ("eye", "백내장·안과"),
    ]
    for mslug, mname in med_cats:
        hub_links["medical"].append((f"{mname} 비급여·실손 계산", f"medical/{mslug}.html"))

    for mslug, mname in med_cats:
        rel = f"medical/{mslug}.html"
        url = f"{cfg.site_url}/{rel}"
        kw = mname.split("·")[0].split("(")[0]
        filtered = med_list if mslug == "all" else ([m for m in med_list if kw in m.category or kw in m.name] or med_list[:12])
        rows_html = "".join(
            f"<tr><td><code>{esc_fn(m.code)}</code></td><td><span class='tag'>{esc_fn(m.category)}</span></td>"
            f"<td><strong>{esc_fn(m.name)}</strong></td><td>{esc_fn(m.description)}</td></tr>"
            for m in filtered[:15]
        )
        title = f"2026 {mname} 비급여 진료비 기준 & 4세대 실손보험 자기부담금 계산기"
        desc = f"건강보험심사평가원 공식 비급여 진료비 코드 정보 기반 {mname} 안내 및 4세대 실손의료보험 급여(20%)·비급여(30%) 환급액 실시간 계산기."
        related = "".join(f'<a class="link-pill" href="../{esc_fn(h)}">{esc_fn(l)}</a>' for l, h in hub_links["medical"] if h != rel)
        faq_html, faq_ld = faq_section_fn([
            ("4세대 실손보험의 급여와 비급여 자기부담률은 얼마인가요?", "4세대 실손보험은 급여 항목 20%(최소 1~2만 원), 비급여 항목 30%(최소 3만 원)를 본인이 부담하고 나머지를 보장받습니다."),
            ("병원마다 비급여 진료비가 다른 이유는 무엇인가요?", "비급여 항목은 건강보험이 적용되지 않아 의료기관이 자체적으로 가격을 책정하기 때문에, 방문 전 심평원 공시 가격 비교가 필수입니다."),
        ])
        body = f"""
<nav class="breadcrumb"><a href="../index.html">홈</a> › <a href="../index.html#medical-hub">비급여·실손보험</a> › {esc_fn(mname)}</nav>
<h1>{esc_fn(title)}</h1>
<p class="lead">건강보험심사평가원 공식 비급여 진료비 정보 API 데이터를 기반으로 {esc_fn(mname)} 항목과 4세대 실손보험 예상 환급액을 즉시 계산합니다.</p>
{adsense_slot_fn(cfg, f"med-{mslug}-top")}
<section class="card" data-widget="silson-calc">
  <h2>4세대 실손보험 자기부담금 · 예상 환급액 계산기</h2>
  <div class="calc-grid">
    <div class="field"><label>급여 진료비 본인부담금 (원)</label><input type="number" name="covered" value="100000" step="10000"></div>
    <div class="field"><label>비급여 진료비 (도수·MRI 등, 원)</label><input type="number" name="noncovered" value="300000" step="10000"></div>
  </div>
  <div class="result-strip">
    <div class="metric-box"><div class="metric-label">예상 최종 본인부담금</div><div class="metric-value" data-out="self">-</div></div>
    <div class="metric-box highlight"><div class="metric-label">예상 실손보험 환급액</div><div class="metric-value" data-out="refund">-</div></div>
  </div>
</section>
<section class="card">
  <h2>건강보험심사평가원 공식 비급여 항목 안내 ({esc_fn(mname)})</h2>
  <table><thead><tr><th>항목코드</th><th>분류</th><th>비급여 항목명</th><th>공식 설명</th></tr></thead><tbody>{rows_html}</tbody></table>
</section>
{affiliate_box_fn("실손의료보험 · 치아보험 · 암보험 보험료 한눈에 비교", "비급여 진료비(MRI·도수·임플란트) 보장을 꼼꼼히 비교하고 내 연령대 최저 보험료를 확인하세요.", "실손·건강보험 무료 비교하기", cfg.affiliate_subsidy_url)}
{faq_html}
<section class="card"><h2>다른 비급여 항목·실손 계산기</h2><div class="link-grid">{related}</div></section>
"""
        (dist / rel).write_text(
            base_layout_fn(cfg, title=title, description=desc, canonical_url=url, body_html=body,
                           json_ld_objects=[{"@context": "https://schema.org", "@type": "WebApplication", "name": title, "url": url, "applicationCategory": "HealthApplication"}, faq_ld],
                           asset_prefix="../", is_sample_data=is_sample_data or med_src.startswith("seed_")),
            encoding="utf-8",
        )
        pages.append(page_cls(rel, url, title, desc, "medical"))

    return pages, hub_links, sources
