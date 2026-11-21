"""Financial calculation engines (KR tax rules) & pSEO revenue simulator."""

from __future__ import annotations

from dataclasses import dataclass


TAX_RATES: dict[str, float] = {
    "general": 0.154,  # 일반과세 15.4% (소득세 14% + 지방소득세 1.4%)
    "preferential": 0.095,  # 세금우대/저율과세 9.5% (또는 농특세 1.4% 조합상품 등)
    "exempt": 0.0,  # 비과세 0%
}


@dataclass(frozen=True)
class DepositResult:
    principal_krw: int
    months: int
    annual_rate_pct: float
    tax_type: str
    gross_interest_krw: int
    tax_krw: int
    net_interest_krw: int
    maturity_amount_krw: int


@dataclass(frozen=True)
class SavingResult:
    monthly_deposit_krw: int
    months: int
    annual_rate_pct: float
    tax_type: str
    total_principal_krw: int
    gross_interest_krw: int
    tax_krw: int
    net_interest_krw: int
    maturity_amount_krw: int


@dataclass(frozen=True)
class LoanResult:
    principal_krw: int
    months: int
    annual_rate_pct: float
    repayment_type: str
    first_month_payment_krw: int
    last_month_payment_krw: int
    total_interest_krw: int
    total_repayment_krw: int


def calculate_deposit(
    principal_krw: int,
    months: int,
    annual_rate_pct: float,
    tax_type: str = "general",
    compound: bool = False,
) -> DepositResult:
    """Calculate Korean fixed deposit maturity amount (simple or monthly compound)."""
    if principal_krw <= 0 or months <= 0 or annual_rate_pct < 0:
        raise ValueError("principal_krw, months must be > 0 and annual_rate_pct >= 0")
    tax_rate = TAX_RATES.get(tax_type, TAX_RATES["general"])
    r = annual_rate_pct / 100.0
    if compound:
        gross_float = principal_krw * ((1.0 + r / 12.0) ** months - 1.0)
    else:
        gross_float = principal_krw * r * (months / 12.0)
    gross = int(round(gross_float))
    tax = int(round(gross * tax_rate))
    net = gross - tax
    return DepositResult(
        principal_krw=principal_krw,
        months=months,
        annual_rate_pct=annual_rate_pct,
        tax_type=tax_type,
        gross_interest_krw=gross,
        tax_krw=tax,
        net_interest_krw=net,
        maturity_amount_krw=principal_krw + net,
    )


def calculate_saving(
    monthly_deposit_krw: int,
    months: int,
    annual_rate_pct: float,
    tax_type: str = "general",
) -> SavingResult:
    """Calculate Korean regular installment saving (단리 정액적립식 기준)."""
    if monthly_deposit_krw <= 0 or months <= 0 or annual_rate_pct < 0:
        raise ValueError("monthly_deposit_krw, months must be > 0 and annual_rate_pct >= 0")
    tax_rate = TAX_RATES.get(tax_type, TAX_RATES["general"])
    r = annual_rate_pct / 100.0
    total_principal = monthly_deposit_krw * months
    # 정액적립식 단리: 월납입액 * r/12 * n(n+1)/2
    gross = int(round(monthly_deposit_krw * (r / 12.0) * (months * (months + 1) / 2.0)))
    tax = int(round(gross * tax_rate))
    net = gross - tax
    return SavingResult(
        monthly_deposit_krw=monthly_deposit_krw,
        months=months,
        annual_rate_pct=annual_rate_pct,
        tax_type=tax_type,
        total_principal_krw=total_principal,
        gross_interest_krw=gross,
        tax_krw=tax,
        net_interest_krw=net,
        maturity_amount_krw=total_principal + net,
    )


def calculate_loan(
    principal_krw: int,
    months: int,
    annual_rate_pct: float,
    repayment_type: str = "equal_installment",
) -> LoanResult:
    """Calculate mortgage / jeonse loan repayment schedule summary."""
    if principal_krw <= 0 or months <= 0 or annual_rate_pct < 0:
        raise ValueError("principal_krw, months must be > 0 and annual_rate_pct >= 0")
    monthly_r = (annual_rate_pct / 100.0) / 12.0

    if repayment_type == "bullet":
        # 만기일시상환 (전세대출 대표 방식)
        monthly_interest = int(round(principal_krw * monthly_r))
        total_interest = monthly_interest * months
        return LoanResult(
            principal_krw=principal_krw,
            months=months,
            annual_rate_pct=annual_rate_pct,
            repayment_type="bullet",
            first_month_payment_krw=monthly_interest,
            last_month_payment_krw=monthly_interest + principal_krw,
            total_interest_krw=total_interest,
            total_repayment_krw=principal_krw + total_interest,
        )

    if repayment_type == "equal_principal":
        # 원금균등상환
        monthly_principal = principal_krw / months
        first_interest = principal_krw * monthly_r
        last_interest = monthly_principal * monthly_r
        total_interest = sum(
            (principal_krw - monthly_principal * i) * monthly_r for i in range(months)
        )
        total_interest_int = int(round(total_interest))
        return LoanResult(
            principal_krw=principal_krw,
            months=months,
            annual_rate_pct=annual_rate_pct,
            repayment_type="equal_principal",
            first_month_payment_krw=int(round(monthly_principal + first_interest)),
            last_month_payment_krw=int(round(monthly_principal + last_interest)),
            total_interest_krw=total_interest_int,
            total_repayment_krw=principal_krw + total_interest_int,
        )

    # 원리금균등상환 (기본)
    if monthly_r == 0:
        pmt = principal_krw / months
    else:
        factor = (1.0 + monthly_r) ** months
        pmt = principal_krw * (monthly_r * factor) / (factor - 1.0)
    pmt_int = int(round(pmt))
    total_repayment = pmt_int * months
    total_interest_int = max(0, total_repayment - principal_krw)
    return LoanResult(
        principal_krw=principal_krw,
        months=months,
        annual_rate_pct=annual_rate_pct,
        repayment_type="equal_installment",
        first_month_payment_krw=pmt_int,
        last_month_payment_krw=pmt_int,
        total_interest_krw=total_interest_int,
        total_repayment_krw=total_repayment,
    )


def simulate_pseo_monthly_revenue(
    monthly_pageviews: int,
    adsense_rpm_krw: int = 9000,
    affiliate_ctr_pct: float = 1.8,
    affiliate_cvr_pct: float = 3.5,
    affiliate_payout_krw: int = 25000,
) -> dict[str, int]:
    """Conservative monthly revenue simulation for KR Finance + Subsidy pSEO site."""
    adsense_rev = int(round((monthly_pageviews / 1000.0) * adsense_rpm_krw))
    affiliate_clicks = int(round(monthly_pageviews * (affiliate_ctr_pct / 100.0)))
    affiliate_conversions = int(round(affiliate_clicks * (affiliate_cvr_pct / 100.0)))
    affiliate_rev = affiliate_conversions * affiliate_payout_krw
    return {
        "monthly_pageviews": monthly_pageviews,
        "adsense_revenue_krw": adsense_rev,
        "affiliate_clicks": affiliate_clicks,
        "affiliate_conversions": affiliate_conversions,
        "affiliate_revenue_krw": affiliate_rev,
        "total_monthly_revenue_krw": adsense_rev + affiliate_rev,
    }
