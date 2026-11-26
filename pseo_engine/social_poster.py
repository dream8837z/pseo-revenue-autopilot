"""Automated X (Twitter) OAuth 1.0a & Telegram briefing poster for FinToolLab."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _pct_encode(val: str) -> str:
    return urllib.parse.quote(str(val), safe="~-._")


def build_oauth1_header(
    method: str,
    url: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
) -> str:
    """Build OAuth 1.0a Authorization header for X API v2 POST /2/tweets."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    param_str = "&".join(f"{_pct_encode(k)}={_pct_encode(v)}" for k, v in sorted(oauth_params.items()))
    base_str = f"{method.upper()}&{_pct_encode(url)}&{_pct_encode(param_str)}"
    signing_key = f"{_pct_encode(api_secret)}&{_pct_encode(access_secret)}"
    sig = base64.b64encode(hmac.new(signing_key.encode(), base_str.encode(), hashlib.sha1).digest()).decode()
    oauth_params["oauth_signature"] = sig
    header_items = ", ".join(f'{_pct_encode(k)}="{_pct_encode(v)}"' for k, v in sorted(oauth_params.items()))
    return f"OAuth {header_items}"


def post_to_x(text: str, *, dry_run: bool = False) -> dict[str, Any]:
    """Post a daily finance/tool briefing to X (Twitter) API v2."""
    api_key = os.environ.get("X_API_KEY", "").strip()
    api_secret = os.environ.get("X_API_SECRET", "").strip()
    access_token = os.environ.get("X_ACCESS_TOKEN", "").strip()
    access_secret = os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()

    if not (api_key and api_secret and access_token and access_secret):
        missing = [
            k
            for k, v in (
                ("X_API_KEY", api_key),
                ("X_API_SECRET", api_secret),
                ("X_ACCESS_TOKEN", access_token),
                ("X_ACCESS_TOKEN_SECRET", access_secret),
            )
            if not v
        ]
        return {"posted": False, "mode": "missing_credentials", "missing": missing}

    if dry_run:
        return {"posted": False, "mode": "dry_run", "preview": text[:280]}

    url = "https://api.twitter.com/2/tweets"
    auth = build_oauth1_header("POST", url, api_key, api_secret, access_token, access_secret)
    req = urllib.request.Request(
        url,
        data=json.dumps({"text": text[:280]}).encode("utf-8"),
        headers={"Authorization": auth, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return {"posted": True, "mode": "live", "status": resp.status, "body": json.loads(resp.read().decode())}
    except urllib.error.HTTPError as exc:
        return {"posted": False, "mode": "error", "status": exc.code, "error": exc.read().decode(errors="replace")[:300]}
    except urllib.error.URLError as exc:
        return {"posted": False, "mode": "error", "error": str(exc)}


def compose_daily_briefing(site_url: str, top_rate_line: str, top_subsidy_line: str) -> str:
    base = site_url.rstrip("/")
    return (
        f"📊 [오늘의 핀툴랩 자동 브리핑]\n"
        f"• {top_rate_line}\n"
        f"• {top_subsidy_line}\n\n"
        f"👉 505종 무료 금융·세금·웹도구 바로가기:\n{base}/index.html\n"
        f"#재테크 #금리비교 #청약 #보조금24 #무료계산기"
    )[:280]
