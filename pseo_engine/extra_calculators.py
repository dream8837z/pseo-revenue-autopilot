"""Additional Korean (Salary, Severance, Real Estate, Auto) & Global USD calculators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SalaryResult:
    annual_salary_krw: int
    monthly_gross_krw: int
    national_pension_krw: int
    health_insurance_krw: int
    long_term_care_krw: int
    employment_insurance_krw: int
    income_tax_krw: int
    local_income_tax_krw: int
    total_deduction_krw: int
    monthly_net_krw: int


def calculate_kr_salary(annual_salary_krw: int, non_taxable_monthly_krw: int = 200_000) -> SalaryResult:
    """Calculate Korean monthly take-home pay (2026 4대보험 + 근로소득세 간이 근사)."""
    if annual_salary_krw <= 0:
        raise ValueError("annual_salary_krw must be > 0")
    monthly_gross = int(round(annual_salary_krw / 12))
    taxable_monthly = max(0, monthly_gross - non_taxable_monthly_krw)

    # 국민연금 4.5% (기준소득월액 상한 6,170,000원 기준)
    pension_base = min(taxable_monthly, 6_170_000)
    national_pension = int(round(pension_base * 0.045))
    # 건강보험 3.545% + 장기요양보험(건강보험료의 12.95%)
    health_ins = int(round(taxable_monthly * 0.03545))
    long_term_care = int(round(health_ins * 0.1295))
    # 고용보험 0.9%
    employment_ins = int(round(taxable_monthly * 0.009))

    # 근로소득세 간이 근사 (연봉 구간 누진 적용)
    annual_taxable = taxable_monthly * 12
    # 근로소득공제 및 기본공제 근사 반영 후 과세표준
    if annual_taxable <= 15_000_000:
        est_annual_tax = annual_taxable * 0.015
    elif annual_taxable <= 45_000_000:
        est_annual_tax = 225_000 + (annual_taxable - 15_000_000) * 0.06
    elif annual_taxable <= 88_000_000:
        est_annual_tax = 2_025_000 + (annual_taxable - 45_000_000) * 0.145
    elif annual_taxable <= 150_000_000:
        est_annual_tax = 8_260_000 + (annual_taxable - 88_000_000) * 0.24
    else:
        est_annual_tax = 23_140_000 + (annual_taxable - 150_000_000) * 0.33

    income_tax = int(round(est_annual_tax / 12))
    local_tax = int(round(income_tax * 0.10))
    total_ded = national_pension + health_ins + long_term_care + employment_ins + income_tax + local_tax
    monthly_net = max(0, monthly_gross - total_ded)
    return SalaryResult(
        annual_salary_krw=annual_salary_krw,
        monthly_gross_krw=monthly_gross,
        national_pension_krw=national_pension,
        health_insurance_krw=health_ins,
        long_term_care_krw=long_term_care,
        employment_insurance_krw=employment_ins,
        income_tax_krw=income_tax,
        local_income_tax_krw=local_tax,
        total_deduction_krw=total_ded,
        monthly_net_krw=monthly_net,
    )


def calculate_kr_severance(monthly_salary_krw: int, years: int) -> dict[str, int]:
    """Calculate statutory Korean severance pay & estimated unemployment benefit."""
    if monthly_salary_krw <= 0 or years <= 0:
        raise ValueError("monthly_salary_krw and years must be > 0")
    days = years * 365
    daily_avg = (monthly_salary_krw * 3) / 91.0
    severance_gross = int(round(daily_avg * 30 * (days / 365.0)))
    # 실업급여 일액 (평균임금 60%, 상한 66,000원 / 하한 64,192원 기준 근사)
    daily_unemp = min(66_000, max(64_192, int(round(daily_avg * 0.6))))
    benefit_days = 120 if years < 1 else (150 if years < 3 else (180 if years < 5 else (210 if years < 10 else 240)))
    return {
        "severance_gross_krw": severance_gross,
        "daily_unemployment_krw": daily_unemp,
        "unemployment_days": benefit_days,
        "total_unemployment_krw": daily_unemp * benefit_days,
    }


def calculate_kr_realestate_cost(price_krw: int, houses_owned: int = 1) -> dict[str, float | int]:
    """Calculate Korean residential acquisition tax + brokerage fee cap."""
    if price_krw <= 0:
        raise ValueError("price_krw must be > 0")
    # 취득세율 (1주택: 6억 이하 1%, 6~9억 선형 1~3%, 9억 초과 3% / 2주택 8% / 3주택+ 12% 조정기준 참고)
    if houses_owned == 1:
        if price_krw <= 600_000_000:
            acq_rate = 0.01
        elif price_krw <= 900_000_000:
            acq_rate = ((price_krw / 100_000_000) * (2 / 3) - 3) / 100.0
        else:
            acq_rate = 0.03
    elif houses_owned == 2:
        acq_rate = 0.08
    else:
        acq_rate = 0.12

    acq_tax = int(round(price_krw * acq_rate))
    local_edu_tax = int(round(acq_tax * 0.10))
    total_tax = acq_tax + local_edu_tax

    # 주택 매매 중개보수 상한요율
    if price_krw < 200_000_000:
        broker_rate = 0.005
    elif price_krw < 900_000_000:
        broker_rate = 0.004
    elif price_krw < 1_200_000_000:
        broker_rate = 0.005
    elif price_krw < 1_500_000_000:
        broker_rate = 0.006
    else:
        broker_rate = 0.007
    brokerage_fee = int(round(price_krw * broker_rate))
    return {
        "acq_rate_pct": round(acq_rate * 100, 2),
        "acq_tax_krw": acq_tax,
        "local_edu_tax_krw": local_edu_tax,
        "total_tax_krw": total_tax,
        "broker_rate_pct": round(broker_rate * 100, 2),
        "brokerage_fee_krw": brokerage_fee,
        "total_closing_cost_krw": total_tax + brokerage_fee,
    }


def calculate_kr_auto_finance(
    car_price_krw: int,
    months: int,
    annual_rate_pct: float = 5.5,
    down_payment_pct: float = 20.0,
) -> dict[str, int]:
    """Calculate Korean car acquisition tax (7% passenger) + monthly installment."""
    if car_price_krw <= 0 or months <= 0:
        raise ValueError("car_price_krw and months must be > 0")
    # 비영업용 승용차 취득세 7% (공급가액 기준 = 차량가 / 1.1 * 0.07)
    acq_tax = int(round((car_price_krw / 1.1) * 0.07))
    down_payment = int(round(car_price_krw * (down_payment_pct / 100.0)))
    loan_principal = max(0, car_price_krw - down_payment)
    mr = (annual_rate_pct / 100.0) / 12.0
    if mr == 0 or loan_principal == 0:
        monthly = int(round(loan_principal / months))
    else:
        factor = (1.0 + mr) ** months
        monthly = int(round(loan_principal * (mr * factor) / (factor - 1.0)))
    total_interest = max(0, monthly * months - loan_principal)
    return {
        "acq_tax_krw": acq_tax,
        "down_payment_krw": down_payment,
        "loan_principal_krw": loan_principal,
        "monthly_payment_krw": monthly,
        "total_interest_krw": total_interest,
    }


def calculate_usd_mortgage(principal_usd: int, years: int, annual_rate_pct: float = 6.25) -> dict[str, int]:
    """Calculate US fixed-rate mortgage monthly P&I payment and total interest."""
    months = years * 12
    mr = (annual_rate_pct / 100.0) / 12.0
    factor = (1.0 + mr) ** months
    pmt = int(round(principal_usd * (mr * factor) / (factor - 1.0)))
    total_paid = pmt * months
    return {
        "monthly_payment_usd": pmt,
        "total_interest_usd": max(0, total_paid - principal_usd),
        "total_payment_usd": total_paid,
    }


def calculate_usd_compound(
    initial_usd: int,
    monthly_contrib_usd: int,
    years: int,
    annual_return_pct: float = 8.0,
) -> dict[str, int]:
    """Calculate US compound interest / 401(k) future value."""
    months = years * 12
    mr = (annual_return_pct / 100.0) / 12.0
    fv_initial = initial_usd * ((1.0 + mr) ** months)
    fv_contrib = monthly_contrib_usd * (((1.0 + mr) ** months - 1.0) / mr)
    total_val = int(round(fv_initial + fv_contrib))
    total_contrib = initial_usd + monthly_contrib_usd * months
    return {
        "future_value_usd": total_val,
        "total_contributions_usd": total_contrib,
        "total_growth_usd": max(0, total_val - total_contrib),
    }
