"""Automated SEO & YMYL quality audit gate for generated pSEO sites."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AuditReport:
    total_html_pages: int = 0
    duplicate_titles: list[str] = field(default_factory=list)
    duplicate_descriptions: list[str] = field(default_factory=list)
    broken_internal_links: list[str] = field(default_factory=list)
    invalid_json_ld: list[str] = field(default_factory=list)
    missing_ymyl_disclaimer: list[str] = field(default_factory=list)
    missing_interactive_widget: list[str] = field(default_factory=list)
    missing_core_files: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not (
            self.duplicate_titles
            or self.duplicate_descriptions
            or self.broken_internal_links
            or self.invalid_json_ld
            or self.missing_ymyl_disclaimer
            or self.missing_interactive_widget
            or self.missing_core_files
        )


_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
_DESC_RE = re.compile(
    r'<meta\s+name="description"\s+content="(.*?)"', re.DOTALL | re.IGNORECASE
)
_HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
_LD_RE = re.compile(
    r'<script\s+type="application/ld\+json">(.*?)</script>', re.DOTALL | re.IGNORECASE
)


def audit_dist(dist_dir: Path) -> AuditReport:
    """Audit generated static site for SEO hygiene, broken links, JSON-LD, and YMYL compliance."""
    report = AuditReport()
    for required in ("index.html", "sitemap.xml", "robots.txt", "ads.txt", "privacy.html", "disclaimer.html"):
        if not (dist_dir / required).exists():
            report.missing_core_files.append(required)

    html_files = sorted(dist_dir.rglob("*.html"))
    report.total_html_pages = len(html_files)

    seen_titles: dict[str, str] = {}
    seen_descs: dict[str, str] = {}

    for path in html_files:
        rel = str(path.relative_to(dist_dir))
        if path.parent == dist_dir and (
            path.name.startswith("google") or path.name.startswith("naver")
        ):
            continue
        content = path.read_text(encoding="utf-8")

        m_title = _TITLE_RE.search(content)
        title = m_title.group(1).strip() if m_title else ""
        if title in seen_titles:
            report.duplicate_titles.append(f"{rel} == {seen_titles[title]} ({title})")
        elif title:
            seen_titles[title] = rel

        m_desc = _DESC_RE.search(content)
        desc = m_desc.group(1).strip() if m_desc else ""
        if desc in seen_descs:
            report.duplicate_descriptions.append(f"{rel} == {seen_descs[desc]}")
        elif desc:
            seen_descs[desc] = rel

        # Check JSON-LD validity
        for raw_ld in _LD_RE.findall(content):
            try:
                json.loads(raw_ld)
            except json.JSONDecodeError as exc:
                report.invalid_json_ld.append(f"{rel}: {exc}")

        # Check YMYL official source disclaimer
        if "ymyl-disclaimer" not in content or "금융감독원" not in content:
            report.missing_ymyl_disclaimer.append(rel)

        # Tool pages must include interactive JS widget to avoid Thin Content penalty
        if rel.startswith(("deposit/", "saving/", "loan/", "subsidy/")):
            if "data-widget=" not in content:
                report.missing_interactive_widget.append(rel)

        # Check local relative links
        for href in _HREF_RE.findall(content):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                continue
            target_part = href.split("#", 1)[0].split("?", 1)[0]
            if not target_part:
                continue
            resolved = (path.parent / target_part).resolve()
            if not resolved.exists():
                report.broken_internal_links.append(f"{rel} -> {href}")

    return report
