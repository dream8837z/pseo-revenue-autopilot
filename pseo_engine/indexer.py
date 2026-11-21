"""IndexNow instant search-engine indexing notifier (Bing, Naver, Yandex, Seznam)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Sequence

from pseo_engine.config import SiteConfig


def submit_indexnow(cfg: SiteConfig, urls: Sequence[str]) -> dict[str, object]:
    """Submit generated URLs to IndexNow API (respects DRY_RUN and ENABLE_INDEXNOW)."""
    url_list = list(urls)
    if not cfg.enable_indexnow or not cfg.indexnow_key:
        return {
            "submitted": False,
            "mode": "disabled",
            "count": len(url_list),
            "message": "IndexNow 비활성화 상태 (ENABLE_INDEXNOW=true 및 INDEXNOW_KEY 설정 시 자동 제출)",
        }
    if cfg.dry_run:
        return {
            "submitted": False,
            "mode": "dry_run",
            "count": len(url_list),
            "message": f"DRY_RUN 모드: {len(url_list)}개 URL IndexNow 제출 시뮬레이션 완료",
        }

    host = urllib.parse.urlparse(cfg.site_url).netloc
    payload = {
        "host": host,
        "key": cfg.indexnow_key,
        "keyLocation": f"{cfg.site_url}/{cfg.indexnow_key}.txt",
        "urlList": url_list[:10000],
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {
                "submitted": True,
                "mode": "live",
                "status_code": resp.status,
                "count": len(url_list),
                "message": f"IndexNow HTTP {resp.status} 제출 완료",
            }
    except urllib.error.URLError as exc:
        return {
            "submitted": False,
            "mode": "live_error",
            "count": len(url_list),
            "message": f"IndexNow 제출 오류: {exc}",
        }
