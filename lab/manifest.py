"""Publish what has shipped, so linkedin-connector can cite it.

This is the only coupling between the two repos, and it goes one way. The connector reads
published/manifest.json to reference the most recent publication in a message. It never
writes here, and this repo never reads the connector's database.

    uv run python -m lab.manifest

Set QPL_APP_BASE once the app is deployed, otherwise the default placeholder is used and
tests will say so.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from lab import registry

SCHEMA_VERSION = 1
APP_BASE = os.environ.get("QPL_APP_BASE", "https://quant-paper-lab.streamlit.app").rstrip("/")
OUT_PATH = registry.ROOT / "published" / "manifest.json"


def entry(paper: dict) -> dict:
    """One published item, in the shape the connector consumes."""
    return {
        "slug": paper["slug"],
        "published": str(paper["published"]),
        "title": paper["title"],
        "authors": paper["authors"],
        "year": paper["year"],
        "paper_url": paper["url"],
        "app_url": f"{APP_BASE}/{paper['url_path']}",
        "one_liner": " ".join(paper.get("one_liner", "").split()),
        "quotable": " ".join(paper.get("quotable", "").split()),
    }


def build() -> dict:
    """Manifest of every paper that has a publication date. Newest first."""
    published = [p for p in registry.papers() if p.get("published")]
    return {
        "schema_version": SCHEMA_VERSION,
        "app_base": APP_BASE,
        "count": len(published),
        "items": [entry(p) for p in published],
    }


def write(path: Path = OUT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    written = write()
    print(f"wrote {written.relative_to(registry.ROOT)} with {build()['count']} item(s)")
    if "streamlit.app" in APP_BASE and not os.environ.get("QPL_APP_BASE"):
        print("note: QPL_APP_BASE is not set, so app_url is a placeholder")
    sys.exit(0)
