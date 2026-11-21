"""Public API data fetchers (FSS Finlife & MOIS Subsidy24) with resilient seed fallback."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pseo_engine.config import SiteConfig


@dataclass
class FinancialProduct:
    product_type: str  # deposit | saving | mortgage | jeonse
    bank_name: str
    product_name: str
    base_rate_pct: float
    max_rate_pct: float
    term_months: int
    join_way: str
    special_condition: str
    source: str = "금융감독원 금융상품한눈에"


@dataclass
class SubsidyProgram:
    service_id: str
    title: str
    agency: str
    region: str  # 전국 | 서울 | 경기 | 인천 | 부산
    target_group: str  # 청년 | 신혼부부·출산 | 소상공인 | 주거·생활
    support_summary: str
    eligibility: str
    apply_method: str
    apply_url: str
    max_benefit_krw: int
    source: str = "행정안전부 보조금24"


def _seed_financial_products() -> list[FinancialProduct]:
    """Realistic KR bank rate dataset used when FINLIFE_API_KEY is unset or in dry-run."""
    return [
        # 정기예금
        FinancialProduct("deposit", "케이뱅크", "코드K 정기예금", 3.10, 3.30, 12, "스마트폰", "복잡한 우대조건 없이 기본금리 적용"),
        FinancialProduct("deposit", "카카오뱅크", "카카오뱅크 정기예금", 3.05, 3.15, 12, "스마트폰", "만기 자동연장 및 긴급출금 지원"),
        FinancialProduct("deposit", "토스뱅크", "먼저 이자 받는 정기예금", 3.15, 3.20, 6, "스마트폰", "가입 즉시 이자 선지급"),
        FinancialProduct("deposit", "KB국민은행", "KB Star 정기예금", 2.95, 3.25, 12, "인터넷,스마트폰", "비대면 가입 우대금리"),
        FinancialProduct("deposit", "신한은행", "쏠편한 정기예금", 2.90, 3.20, 12, "인터넷,스마트폰", "비대면 신규 고객 우대"),
        FinancialProduct("deposit", "하나은행", "하나의 정기예금", 2.95, 3.25, 12, "인터넷,스마트폰", "만기일 자유 지정 가능"),
        FinancialProduct("deposit", "우리은행", "WON플러스 예금", 3.00, 3.22, 12, "스마트폰", "비대면 전용 고금리 예금"),
        FinancialProduct("deposit", "NH농협은행", "NH올원e예금", 3.00, 3.20, 12, "인터넷,스마트폰", "우대조건 없는 단일금리"),
        # 적금
        FinancialProduct("saving", "토스뱅크", "굴비 적금", 2.50, 4.50, 6, "스마트폰", "만기 해지 시 우대금리 +2.0%p"),
        FinancialProduct("saving", "카카오뱅크", "26주적금", 3.00, 5.50, 6, "스마트폰", "26주 연속 자동이체 성공 시 우대"),
        FinancialProduct("saving", "케이뱅크", "주거래우대 자유적금", 3.40, 4.30, 12, "스마트폰", "급여이체 및 체크카드 실적 우대"),
        FinancialProduct("saving", "KB국민은행", "KB내맘대로적금", 3.15, 3.95, 12, "인터넷,스마트폰", "급여이체·카드결제·자동이체 우대"),
        FinancialProduct("saving", "신한은행", "신한 알쏠적금", 3.20, 4.10, 12, "스마트폰", "오픈뱅킹 및 카드 실적 우대"),
        FinancialProduct("saving", "하나은행", "내맘적금", 3.10, 4.00, 12, "인터넷,스마트폰", "자동이체 6회 이상 우대"),
        # 주택담보대출
        FinancialProduct("mortgage", "카카오뱅크", "주택담보대출 (혼합/변동)", 3.72, 4.45, 360, "스마트폰", "갈아타기(대환) 우대금리 적용 가능"),
        FinancialProduct("mortgage", "케이뱅크", "아파트담보대출", 3.78, 4.52, 360, "스마트폰", "구입자금/대환 비대면 서류 자동화"),
        FinancialProduct("mortgage", "KB국민은행", "KB주택담보대출 (주기형)", 3.85, 4.65, 360, "영업점,스마트폰", "급여이체·카드·청약 우대 최대 0.9%p"),
        FinancialProduct("mortgage", "신한은행", "신한주택대출 (금융채 5년)", 3.88, 4.70, 360, "영업점,스마트폰", "서울시/국토부 정책모기지 연계"),
        FinancialProduct("mortgage", "하나은행", "하나원큐 아파트론", 3.82, 4.60, 360, "스마트폰", "비대면 신청 시 0.1%p 감면"),
        # 전세자금대출
        FinancialProduct("jeonse", "카카오뱅크", "전월세보증금 대출 (HF/청년)", 3.45, 4.15, 24, "스마트폰", "청년 전월세 최대 2억, 중도상환해약금 면제"),
        FinancialProduct("jeonse", "케이뱅크", "전세대출 (HF 일반/청년)", 3.48, 4.20, 24, "스마트폰", "휴일·주말 실행 및 비대면 심사"),
        FinancialProduct("jeonse", "토스뱅크", "전월세보증금대출", 3.52, 4.25, 24, "스마트폰", "전세지킴보증 연계"),
        FinancialProduct("jeonse", "우리은행", "우리전세론 (버팀목 연계)", 3.60, 4.35, 24, "영업점,스마트폰", "신혼부부·청년 버팀목 우대"),
        FinancialProduct("jeonse", "KB국민은행", "KB주택전세자금대출", 3.65, 4.40, 24, "영업점,스마트폰", "주거래 실적 우대금리"),
    ]


def _seed_subsidies() -> list[SubsidyProgram]:
    """Representative 2026 KR public benefit programs across regions & target groups."""
    return [
        SubsidyProgram(
            "GOV24_YOUTH_001", "청년월세 한시 특별지원", "국토교통부", "전국", "청년",
            "무주택 독립 청년에게 월 최대 20만 원(최대 24개월) 임차료 현금 지원",
            "만 19~34세 무주택 청년, 청년가구 중위소득 60% 이하 및 원가구 100% 이하",
            "복지로 온라인 신청 또는 관할 주민센터 방문", "https://www.bokjiro.go.kr", 4800000
        ),
        SubsidyProgram(
            "GOV24_YOUTH_002", "청년내일저축계좌", "보건복지부", "전국", "청년",
            "매월 10만 원 저축 시 정부가 월 10~30만 원 매칭 적립 (3년 만기 최대 1,440만 원)",
            "근로·사업소득이 있는 만 19~34세 청년 (기준 중위소득 100% 이하)",
            "복지로 온라인 또는 읍면동 행정복지센터", "https://www.bokjiro.go.kr", 10800000
        ),
        SubsidyProgram(
            "GOV24_YOUTH_SEOUL", "서울시 청년수당 및 희망두배 청년통장", "서울특별시", "서울", "청년",
            "구직활동 청년 월 50만 원(최대 6개월) 및 저축액 100% 매칭 지원",
            "서울 거주 만 19~34세 미취업/근로 청년 (소득 기준 충족 시)",
            "청년몽땅정보통 온라인 신청", "https://youth.seoul.go.kr", 3600000
        ),
        SubsidyProgram(
            "GOV24_YOUTH_GG", "경기도 청년기본소득 및 주거비 지원", "경기도", "경기", "청년",
            "경기도 거주 청년 분기별 지역화폐 지급 및 월세·이사비 지원",
            "경기도 3년 이상 연속 거주 만 24세 청년 등",
            "잡아바 어플라이 온라인 신청", "https://apply.jobaba.net", 1000000
        ),
        SubsidyProgram(
            "GOV24_YOUTH_ICN", "인천 드림For청년통장", "인천광역시", "인천", "청년",
            "월 15만 원 3년 저축 시 인천시 540만 원 매칭 적립 (총 1,080만 원)",
            "인천 거주 만 18~39세 재직 청년 (기준 중위소득 150% 이하)",
            "인천청년포털 온라인 신청", "https://youth.incheon.go.kr", 5400000
        ),
        SubsidyProgram(
            "GOV24_YOUTH_BSN", "부산 청년 기쁨두배통장", "부산광역시", "부산", "청년",
            "월 10~30만 원 저축 시 부산시 동일 금액 매칭 지원",
            "부산 거주 만 18~39세 근로 청년 (기준 중위소득 150% 이하)",
            "부산청년플랫폼 온라인 신청", "https://young.busan.go.kr", 5400000
        ),
        SubsidyProgram(
            "GOV24_FAM_001", "부모급여 (영아수당 통합)", "보건복지부", "전국", "신혼부부·출산",
            "만 0세 월 100만 원, 만 1세 월 50만 원 현금 지급 (소득 무관)",
            "만 0~1세 아동을 양육하는 모든 대한민국 가정",
            "정부24·복지로 온라인 신청 (행복출산 원스톱)", "https://www.gov.kr", 18000000
        ),
        SubsidyProgram(
            "GOV24_FAM_002", "첫만남이용권 바우처", "보건복지부", "전국", "신혼부부·출산",
            "첫째아 200만 원, 둘째아 이상 300만 원 국민행복카드 바우처 지급",
            "출생신고 후 주민등록번호를 부여받은 모든 출생아",
            "복지로·정부24 온라인 또는 주민센터", "https://www.gov.kr", 3000000
        ),
        SubsidyProgram(
            "GOV24_FAM_SEOUL", "서울형 산후조리경비 & 신혼부부 임차보증금 이자지원", "서울특별시", "서울", "신혼부부·출산",
            "출산 산모 100만 원 바우처 + 신혼부부 전세대출 이자 최대 연 4.5%p 지원",
            "서울 거주 출산 가정 및 혼인 7년 이내 무주택 신혼부부",
            "서울맘케어 및 서울주거포털 온라인 신청", "https://housing.seoul.go.kr", 4500000
        ),
        SubsidyProgram(
            "GOV24_FAM_GG", "경기도 산후조리비 & 신혼부부 전세자금 이자지원", "경기도", "경기", "신혼부부·출산",
            "출생아 1인당 50만 원 지역화폐 + 전세대출 잔액 일부 이자 지원",
            "경기도 주민등록 출산 가정 및 기준 충족 신혼부부",
            "경기민원24 온라인 신청", "https://gg24.gg.go.kr", 1500000
        ),
        SubsidyProgram(
            "GOV24_BIZ_001", "소상공인 정책자금 & 전기요금 특별지원", "중소벤처기업부", "전국", "소상공인",
            "영세 소상공인 전기요금 감면(최대 20만 원+) 및 저금리 경영안정자금 대출",
            "연 매출 기준 충족 영세 소상공인 및 개인사업자",
            "소상공인24·소상공인시장진흥공단 온라인 신청", "https://www.sbiz24.kr", 2000000
        ),
        SubsidyProgram(
            "GOV24_BIZ_002", "소상공인 배달·택배비 및 스마트상점 기술보급 지원", "중소벤처기업부", "전국", "소상공인",
            "연간 배달·택배비 최대 30만 원 지원 및 키오스크·테이블오더 도입비 최대 70% 보조",
            "상시근로자 5인 미만(제조업 10인 미만) 소상공인",
            "소상공인24 온라인 신청", "https://www.sbiz24.kr", 5000000
        ),
        SubsidyProgram(
            "GOV24_BIZ_SEOUL", "서울시 자영업자 고용보험료 & 노란우산 희망장려금", "서울특별시", "서울", "소상공인",
            "자영업자 고용보험료 최대 80% 환급 + 노란우산 공제 월 2만 원 추가 적립",
            "서울 소재 사업장 운영 소상공인",
            "서울시 자영업지원센터 온라인 신청", "https://www.seoulsbdc.or.kr", 1200000
        ),
        SubsidyProgram(
            "GOV24_BIZ_BSN", "부산 소상공인 경영안정 육성자금 이차보전", "부산광역시", "부산", "소상공인",
            "부산신용보증재단 연계 대출 이자 연 1.5~2.0%p 보전 지원",
            "부산시 소재 사업자등록 소상공인",
            "부산신용보증재단 온라인 신청", "https://www.busansinbo.or.kr", 2000000
        ),
        SubsidyProgram(
            "GOV24_LIFE_001", "K-패스 대중교통비 환급 지원", "국토교통부", "전국", "주거·생활",
            "월 15회 이상 대중교통 이용 시 일반 20%·청년 30%·저소득층 53% 익월 환급",
            "만 19세 이상 K-패스 참여 지자체 거주 국민",
            "K-패스 카드 발급 후 앱/홈페이지 회원가입", "https://korea-pass.kr", 600000
        ),
        SubsidyProgram(
            "GOV24_LIFE_002", "에너지바우처 (냉·난방비 지원)", "산업통상자원부", "전국", "주거·생활",
            "하절기·동절기 전기·도시가스·지역난방 요금 가구원 수별 최대 70만 원+ 차감",
            "국민기초생활보장 수급가구 중 노인·영유아·장애인·임산부 등 포함 가구",
            "복지로 온라인 또는 주민센터 방문 신청", "https://www.energyv.or.kr", 701300
        ),
        SubsidyProgram(
            "GOV24_LIFE_ICN", "인천 아이(i)-패스 대중교통 무제한 환급", "인천광역시", "인천", "주거·생활",
            "K-패스 혜택 확대 적용 (월 60회 상한 폐지, 청년 만 39세까지 30% 환급)",
            "인천광역시 주민등록 시민",
            "K-패스 카드 등록 시 인천 시민 자동 적용", "https://korea-pass.kr", 900000
        ),
    ]


def _http_get_json(url: str, timeout: int = 12) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; pSEO-Revenue-Autopilot/1.0)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_financial_products(cfg: SiteConfig) -> tuple[list[FinancialProduct], str]:
    """Fetch live FSS Finlife products if key is configured and not dry-run, else fallback."""
    cache_path = cfg.data_dir / "cache" / "financial_products.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cfg.dry_run and cfg.finlife_api_key:
        endpoints = [
            ("deposit", "https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"),
            ("saving", "https://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json"),
            ("mortgage", "https://finlife.fss.or.kr/finlifeapi/mortgageLoanProductsSearch.json"),
            ("jeonse", "https://finlife.fss.or.kr/finlifeapi/rentHouseLoanProductsSearch.json"),
        ]
        collected: list[FinancialProduct] = []
        for ptype, base_url in endpoints:
            qs = urllib.parse.urlencode(
                {"auth": cfg.finlife_api_key, "topFinGrpNo": "020000", "pageNo": "1"}
            )
            try:
                payload = _http_get_json(f"{base_url}?{qs}")
                result = payload.get("result", {})
                base_list = {
                    item.get("fin_prdt_cd"): item for item in result.get("baseList", [])
                }
                best_by_product: dict[str, FinancialProduct] = {}
                for opt in result.get("optionList", []):
                    prdt_cd = str(opt.get("fin_prdt_cd") or "")
                    if not prdt_cd:
                        continue
                    base = base_list.get(prdt_cd, {})
                    bank = str(base.get("kor_co_nm") or "시중은행").strip()
                    name = str(base.get("fin_prdt_nm") or f"{ptype} 상품").strip()
                    if ptype in {"deposit", "saving"}:
                        raw_base = opt.get("intr_rate")
                        raw_max = opt.get("intr_rate2")
                        base_r = float(raw_base) if raw_base not in (None, "") else 3.0
                        max_r = float(raw_max) if raw_max not in (None, "") else base_r
                        term = int(opt.get("save_trm") or 12)
                    else:
                        raw_min = opt.get("lend_rate_min")
                        raw_max = opt.get("lend_rate_max")
                        base_r = float(raw_min) if raw_min not in (None, "") else 3.8
                        max_r = float(raw_max) if raw_max not in (None, "") else base_r + 0.7
                        term = 360 if ptype == "mortgage" else 24
                    candidate = FinancialProduct(
                        product_type=ptype,
                        bank_name=bank,
                        product_name=name,
                        base_rate_pct=round(base_r, 2),
                        max_rate_pct=round(max_r, 2),
                        term_months=term,
                        join_way=str(base.get("join_way") or "비대면/영업점"),
                        special_condition=str(base.get("spcl_cnd") or "공시 기준 참고")[:90],
                    )
                    prev = best_by_product.get(prdt_cd)
                    if prev is None:
                        best_by_product[prdt_cd] = candidate
                    elif ptype in {"deposit", "saving"} and candidate.max_rate_pct > prev.max_rate_pct:
                        best_by_product[prdt_cd] = candidate
                    elif ptype in {"mortgage", "jeonse"} and candidate.base_rate_pct < prev.base_rate_pct:
                        best_by_product[prdt_cd] = candidate
                collected.extend(list(best_by_product.values())[:12])
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
                continue
        if collected:
            cache_path.write_text(
                json.dumps(
                    {
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "source": "live_fss_finlife_api",
                        "items": [asdict(p) for p in collected],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return collected, "live_fss_finlife_api"

    seed = _seed_financial_products()
    cache_path.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": "seed_fallback_2026",
                "items": [asdict(p) for p in seed],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return seed, "seed_fallback_2026"


def fetch_subsidy_programs(cfg: SiteConfig) -> tuple[list[SubsidyProgram], str]:
    """Fetch live MOIS Subsidy24 API if key is configured and not dry-run, else fallback."""
    cache_path = cfg.data_dir / "cache" / "subsidy_programs.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cfg.dry_run and cfg.data_go_kr_api_key:
        # 공공데이터포털 Encoding/Decoding 키 모두 안전하게 처리 (이중 인코딩 방지)
        decoded_key = urllib.parse.unquote(cfg.data_go_kr_api_key)
        qs = urllib.parse.urlencode(
            {
                "page": "1",
                "perPage": "50",
                "serviceKey": decoded_key,
            }
        )
        url = f"https://api.odcloud.kr/api/gov24/v3/serviceList?{qs}"
        try:
            payload = _http_get_json(url)
            rows = payload.get("data", [])
            parsed: list[SubsidyProgram] = []
            for row in rows:
                title = str(row.get("서비스명") or "").strip()
                if not title:
                    continue
                agency = str(row.get("소관기관명") or "대한민국 정부").strip()
                region = "전국"
                for candidate in ("서울", "경기", "인천", "부산"):
                    if candidate in agency or candidate in title:
                        region = candidate
                        break
                summary = str(row.get("서비스목적요약") or row.get("지원내용") or "정부 공공서비스 혜택").strip()
                combined_text = f"{title} {summary}"
                if any(k in combined_text for k in ("청년", "대학생", "취업")):
                    group = "청년"
                elif any(k in combined_text for k in ("출산", "육아", "신혼", "아동", "임신")):
                    group = "신혼부부·출산"
                elif any(k in combined_text for k in ("소상공인", "자영업", "사업자", "창업")):
                    group = "소상공인"
                else:
                    group = "주거·생활"
                parsed.append(
                    SubsidyProgram(
                        service_id=str(row.get("서비스ID") or f"GOV24_{len(parsed)+1}"),
                        title=title,
                        agency=agency,
                        region=region,
                        target_group=group,
                        support_summary=summary[:140],
                        eligibility=str(row.get("지원대상") or "상세 요건은 정부24 공식 안내 참조")[:140],
                        apply_method=str(row.get("신청방법") or "정부24 온라인 또는 관할 주민센터")[:100],
                        apply_url=str(row.get("상세조회URL") or "https://www.gov.kr"),
                        max_benefit_krw=0,
                    )
                )
            if parsed:
                cache_path.write_text(
                    json.dumps(
                        {
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                            "source": "live_mois_subsidy24_api",
                            "items": [asdict(s) for s in parsed],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                return parsed, "live_mois_subsidy24_api"
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            pass

    seed = _seed_subsidies()
    cache_path.write_text(
        json.dumps(
            {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "source": "seed_fallback_2026",
                "items": [asdict(s) for s in seed],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return seed, "seed_fallback_2026"
