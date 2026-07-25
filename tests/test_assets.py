"""What LinkedIn will actually receive.

Skipped when out/ is empty, so a clone can run the suite without rendering first. Run
`uv run --group render python -m papers.jegadeesh_titman_1993.animate` to populate it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lab import render

ROOT = Path(__file__).resolve().parents[1]
MP4 = ROOT / "out" / "momentum-1993.mp4"
GIF = ROOT / "assets" / "previews" / "momentum-1993.gif"

needs_render = pytest.mark.skipif(not MP4.exists(), reason="out/ not rendered")


@needs_render
def test_video_is_feed_ready() -> None:
    info = render.probe(MP4)
    assert (int(info["width"]), int(info["height"])) == (render.SIZE, render.SIZE), "square, 1200 px"
    assert info["codec_name"] == "h264" if "codec_name" in info else True
    assert "audio" not in info.get("codec_types", ""), "a feed video has no audio track"
    duration = float(info["duration"])
    assert 8.0 <= duration <= 20.0, f"clip is {duration:.1f}s, aim for 10 to 15"
    assert MP4.stat().st_size < 200 * 1_048_576


@needs_render
def test_derived_gif_stays_small() -> None:
    """The GIF is for the README and other networks. LinkedIn caps images at 5 MB."""
    size_mb = GIF.stat().st_size / 1_048_576
    assert size_mb < 5.0, f"gif is {size_mb:.1f} MB"
