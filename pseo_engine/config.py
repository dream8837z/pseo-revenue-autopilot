"""Configuration loader for pSEO Revenue Autopilot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(env_path: Path) -> None:
    """Load simple KEY=VALUE pairs from .env without overriding existing env vars."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SiteConfig:
    site_name: str
    site_url: str
    site_description: str
    contact_email: str
    finlife_api_key: str
    data_go_kr_api_key: str
    adsense_client_id: str
    ga4_measurement_id: str
    affiliate_deposit_url: str
    affiliate_loan_url: str
    affiliate_subsidy_url: str
    indexnow_key: str
    enable_indexnow: bool
    data_dir: Path
    dist_dir: Path
    dry_run: bool

    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "SiteConfig":
        root = base_dir or Path.cwd()
        _load_dotenv(root / ".env")
        site_url = os.environ.get("SITE_URL", "https://example.com").rstrip("/")
        data_dir = Path(os.environ.get("DATA_DIR", "data"))
        dist_dir = Path(os.environ.get("DIST_DIR", "dist"))
        if not data_dir.is_absolute():
            data_dir = root / data_dir
        if not dist_dir.is_absolute():
            dist_dir = root / dist_dir
        return cls(
            site_name=os.environ.get("SITE_NAME", "핀툴랩(FinToolLab) - 금융·부동산·세금·웹도구 올인원 허브"),
            site_url=site_url,
            site_description=os.environ.get(
                "SITE_DESCRIPTION",
                "6대 공공데이터 실시간 연동 예적금·대출·실거래가·청약·세금·보조금24 및 무료 웹 유틸리티 505종 올인원 허브",
            ),
            contact_email=os.environ.get("CONTACT_EMAIL", "contact@example.com"),
            finlife_api_key=os.environ.get("FINLIFE_API_KEY", "").strip(),
            data_go_kr_api_key=os.environ.get("DATA_GO_KR_API_KEY", "").strip(),
            adsense_client_id=os.environ.get("ADSENSE_CLIENT_ID", "").strip(),
            ga4_measurement_id=os.environ.get("GA4_MEASUREMENT_ID", "").strip(),
            affiliate_deposit_url=os.environ.get(
                "AFFILIATE_DEPOSIT_URL", f"{site_url}/#deposit-hub"
            ).strip(),
            affiliate_loan_url=os.environ.get(
                "AFFILIATE_LOAN_URL", f"{site_url}/#loan-hub"
            ).strip(),
            affiliate_subsidy_url=os.environ.get(
                "AFFILIATE_SUBSIDY_URL", f"{site_url}/#subsidy-hub"
            ).strip(),
            indexnow_key=os.environ.get("INDEXNOW_KEY", "fintoollab8837indexnow2026key99").strip(),
            enable_indexnow=_env_bool("ENABLE_INDEXNOW", True),
            data_dir=data_dir,
            dist_dir=dist_dir,
            dry_run=_env_bool("DRY_RUN", True),
        )
