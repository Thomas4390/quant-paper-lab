"""Screenshot the running app, so layout can be judged instead of guessed.

Figures can be checked with a static export, but vertical rhythm, line length and the
spacing between a control and the chart it drives only exist in the browser. This drives a
headless Chromium against a local server and writes full-page and element shots.

    uv run streamlit run streamlit_app.py --server.port 8511 --server.headless true &
    uv run --group dev python tools/shoot.py --out /tmp/shots
    uv run --group dev python tools/shoot.py --out /tmp/shots --animate momentum-1993

Not part of the test suite: it needs a live server and a browser. It is a development tool.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8511"
WIDTH = 1440
HEIGHT = 1000


def settle(page, *, charts: bool, timeout: int = 45_000) -> None:
    """Wait until Streamlit stops running and, where there are charts, until they paint.

    The library index has no figure, so waiting for a Plotly canvas there would hang.
    """
    page.wait_for_selector("[data-testid='stAppViewContainer']", timeout=timeout)
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')",
        timeout=timeout,
    )
    if charts:
        page.wait_for_selector(".js-plotly-plot", timeout=timeout)
    page.wait_for_timeout(2500)


PAGES = (("home", "/", False), ("momentum", "/momentum-1993", True))


def shoot(out: Path, animate: str | None) -> int:
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # Streamlit scrolls inside its own container, so full_page only ever returns the
        # viewport. A tall viewport is the way to see the whole page at once.
        tall = browser.new_page(viewport={"width": WIDTH, "height": 3600}, device_scale_factor=1)
        for name, path, charts in PAGES:
            tall.goto(f"{BASE}{path}", wait_until="domcontentloaded")
            settle(tall, charts=charts)
            tall.screenshot(path=out / f"{name}-tall.png")
            print(f"  {name}: whole page")
        tall.close()

        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
        for name, path, charts in PAGES:
            page.goto(f"{BASE}{path}", wait_until="domcontentloaded")
            settle(page, charts=charts)
            page.screenshot(path=out / f"{name}-fold.png")
            figures = page.query_selector_all(".js-plotly-plot")
            for index, figure in enumerate(figures):
                figure.screenshot(path=out / f"{name}-chart{index}.png")
            print(f"  {name}: above the fold, {len(figures)} chart(s)")

        if animate:
            page.goto(f"{BASE}/{animate}", wait_until="domcontentloaded")
            settle(page, charts=True)
            play = page.get_by_text("Play", exact=True).first
            play.click()
            for step, wait in ((1, 3000), (2, 4000), (3, 6000)):
                page.wait_for_timeout(wait)
                page.screenshot(path=out / f"animation-t{step}.png")
            print(f"  animation: 3 frames captured while playing")

        browser.close()
    print(f"wrote to {out}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("/tmp/shots"))
    parser.add_argument("--animate", metavar="URL_PATH", help="also capture a playing animation")
    args = parser.parse_args()
    sys.exit(shoot(args.out, args.animate))
