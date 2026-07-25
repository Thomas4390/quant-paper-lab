"""The manifest is a contract with linkedin-connector. Keep it honest."""

from __future__ import annotations

import json
from datetime import date

from lab import manifest, registry

REQUIRED = {
    "slug",
    "published",
    "title",
    "authors",
    "year",
    "paper_url",
    "app_url",
    "one_liner",
    "quotable",
}


def test_every_paper_declares_what_the_pipeline_needs() -> None:
    for paper in registry.papers():
        for key in ("slug", "url_path", "nav_title", "quotable", "claims", "method_notes"):
            assert paper.get(key), f"{paper['slug']} is missing {key}"
        assert paper["claims"], "a paper with no checkable claims should not ship"
        for claim in paper["claims"]:
            assert claim.get("claim") and claim.get("evidence")


def test_manifest_shape() -> None:
    built = manifest.build()
    assert built["schema_version"] == manifest.SCHEMA_VERSION
    assert built["count"] == len(built["items"])
    for item in built["items"]:
        assert REQUIRED <= item.keys(), f"missing {REQUIRED - item.keys()}"
        assert item["app_url"].startswith("https://")
        assert item["paper_url"].startswith("https://")
        date.fromisoformat(item["published"])
        assert "\n" not in item["quotable"], "quotable has to survive being pasted into a message"


def test_manifest_on_disk_matches_the_code(tmp_path) -> None:
    """published/manifest.json is committed, so it must not drift from the papers."""
    written = json.loads(manifest.write(tmp_path / "manifest.json").read_text())
    committed_path = manifest.OUT_PATH
    assert committed_path.exists(), "run: uv run python -m lab.manifest"
    committed = json.loads(committed_path.read_text())
    assert [i["slug"] for i in committed["items"]] == [i["slug"] for i in written["items"]]
