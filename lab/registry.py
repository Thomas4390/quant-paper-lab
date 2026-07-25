"""Discover the papers in the library.

A paper is a directory under papers/ holding a paper.yaml and a page.py. Adding one is
therefore a matter of adding a folder: navigation, the home index and the manifest all read
from here, so nothing has to be registered twice.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"


def papers() -> list[dict]:
    """Every paper, newest publication first. Each entry is paper.yaml plus its paths."""
    found = []
    for meta_path in sorted(PAPERS.glob("*/paper.yaml")):
        paper = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        page = meta_path.parent / "page.py"
        if not page.exists():
            raise FileNotFoundError(f"{meta_path.parent.name} has no page.py")
        paper["dir"] = meta_path.parent
        paper["page"] = page.relative_to(ROOT).as_posix()
        found.append(paper)
    return sorted(found, key=lambda p: str(p.get("published") or ""), reverse=True)
