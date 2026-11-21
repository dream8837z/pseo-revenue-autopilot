"""Unit and end-to-end tests for pSEO Revenue Autopilot."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pseo_engine.calculators import (
    calculate_deposit,
    calculate_loan,
    calculate_saving,
    simulate_pseo_monthly_revenue,
)
from pseo_engine.config import SiteConfig
from pseo_engine.fetchers import fetch_financial_products, fetch_subsidy_programs
from pseo_engine.generator import generate_site
from pseo_engine.indexer import submit_indexnow
from pseo_engine.seo_audit import audit_dist


class TestCalculators(unittest.TestCase):
    def test_deposit_general_and_exempt_tax(self) -> None:
        gen = calculate_deposit(10_000_000, 12, 3.30, "general")
        self.assertEqual(gen.gross_interest_krw, 330_000)
        self.assertEqual(gen.tax_krw, 50_820)
        self.assertEqual(gen.net_interest_krw, 279_180)
        self.assertEqual(gen.maturity_amount_krw, 10_279_180)

        exempt = calculate_deposit(10_000_000, 12, 3.30, "exempt")
        self.assertEqual(exempt.tax_krw, 0)
        self.assertEqual(exempt.net_interest_krw, 330_000)

    def test_saving_installment_formula(self) -> None:
        res = calculate_saving(1_000_000, 12, 4.0, "general")
        self.assertEqual(res.total_principal_krw, 12_000_000)
        # 1,000,000 * (0.04/12) * (12*13/2) = 260,000
        self.assertEqual(res.gross_interest_krw, 260_000)
        self.assertEqual(res.net_interest_krw, 260_000 - round(260_000 * 0.154))

    def test_loan_repayment_modes(self) -> None:
        bullet = calculate_loan(200_000_000, 24, 3.6, "bullet")
        self.assertEqual(bullet.first_month_payment_krw, 600_000)
        self.assertEqual(bullet.total_interest_krw, 14_400_000)

        ei = calculate_loan(300_000_000, 360, 4.0, "equal_installment")
        ep = calculate_loan(300_000_000, 360, 4.0, "equal_principal")
        self.assertGreater(ei.total_interest_krw, ep.total_interest_krw)
        self.assertGreater(ep.first_month_payment_krw, ei.first_month_payment_krw)

    def test_revenue_simulator(self) -> None:
        sim = simulate_pseo_monthly_revenue(50_000)
        self.assertEqual(sim["adsense_revenue_krw"], 450_000)
        self.assertGreater(sim["affiliate_revenue_krw"], 0)
        self.assertEqual(
            sim["total_monthly_revenue_krw"],
            sim["adsense_revenue_krw"] + sim["affiliate_revenue_krw"],
        )


class TestEndToEndBuildAndAudit(unittest.TestCase):
    def test_full_pipeline_generates_and_passes_seo_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = SiteConfig(
                site_name="테스트 금융·보조금 허브",
                site_url="https://test-finhub.example.com",
                site_description="테스트 설명",
                contact_email="ops@example.com",
                finlife_api_key="",
                data_go_kr_api_key="",
                adsense_client_id="ca-pub-1234567890123456",
                ga4_measurement_id="",
                affiliate_deposit_url="https://example.com/deposit",
                affiliate_loan_url="https://example.com/loan",
                affiliate_subsidy_url="https://example.com/subsidy",
                indexnow_key="testkey123456",
                enable_indexnow=True,
                data_dir=root / "data",
                dist_dir=root / "dist",
                dry_run=True,
            )
            products, fin_src = fetch_financial_products(cfg)
            subsidies, sub_src = fetch_subsidy_programs(cfg)
            self.assertEqual(fin_src, "seed_fallback_2026")
            self.assertEqual(sub_src, "seed_fallback_2026")
            self.assertGreaterEqual(len(products), 20)
            self.assertGreaterEqual(len(subsidies), 15)

            pages = generate_site(cfg, products, subsidies, is_sample_data=True)
            self.assertGreaterEqual(len(pages), 60)

            report = audit_dist(cfg.dist_dir)
            self.assertTrue(report.passed, msg=f"SEO Audit failed: {report}")
            self.assertEqual(report.broken_internal_links, [])
            self.assertEqual(report.duplicate_titles, [])
            self.assertEqual(report.invalid_json_ld, [])
            self.assertEqual(report.missing_interactive_widget, [])

            # Verify sample transparency banner appears in sample mode and disappears in live mode
            sample_index = (cfg.dist_dir / "index.html").read_text(encoding="utf-8")
            self.assertIn('data-mode="sample"', sample_index)
            generate_site(cfg, products, subsidies, is_sample_data=False)
            live_index = (cfg.dist_dir / "index.html").read_text(encoding="utf-8")
            self.assertNotIn('data-mode="sample"', live_index)

            # Verify ads.txt & IndexNow key file
            ads_txt = (cfg.dist_dir / "ads.txt").read_text(encoding="utf-8")
            self.assertIn("pub-1234567890123456", ads_txt)
            self.assertTrue((cfg.dist_dir / "testkey123456.txt").exists())

            idx = submit_indexnow(cfg, [p.url for p in pages])
            self.assertEqual(idx["mode"], "dry_run")
            self.assertEqual(idx["count"], len(pages))


if __name__ == "__main__":
    unittest.main()
