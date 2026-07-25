"""Render the post's visual: one dollar splitting into ten deciles, 1927 to today.

Why this figure and not the 3D surface. The video has one job, which is to make a single
point legible on a phone in ten seconds. A fan of curves growing left to right does that.
A deforming surface needs a viewer who is already paying attention, so it stays in the app
where it can be rotated. The feed gets the hook, the app gets the toy.

The axes are fixed from the first frame and the compounding runs once over the full history,
so the curves grow into a stationary frame rather than the frame rescaling around them.

    uv run --group render python -m papers.jegadeesh_titman_1993.animate
    uv run --group render python -m papers.jegadeesh_titman_1993.animate --preview 1975

Writes out/momentum-1993.mp4, the asset to upload, which git ignores because it is rebuilt
per post. The derived GIF lands in assets/previews/ and is committed, because the README and
the other networks depend on it. Reads parquet directly, so nothing here imports streamlit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from lab import render, theme
from papers.jegadeesh_titman_1993 import figures

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
SLUG = "momentum-1993"

HORIZON = "prior_12_2"
# The clip shows value weighted deciles, the modern convention, which is also where the
# compounded figure quoted in the post comes from. The footer says so.
WEIGHTING = "vw"
# The clock starts where the paper's own sample starts. Running from 1927 instead adds three
# more decades of log axis and turns the headline into one dollar becoming 5.8 million, which
# is true, gross of everything, and reads as a sales pitch. 1965 keeps the same 17 percent a
# year and lets the reader see what happened after the result was published.
FIRST_YEAR = 1965
FIRST_FRAME_YEAR = 1967  # a couple of years of curve, so frame one is not a single dot
PUBLISHED_YEAR = 1993
TITLE = "One dollar, sorted on last year's return"
FOOTER = "Ken French value weighted deciles, gross of costs · Jegadeesh and Titman (1993) · synerqo.com"


def load() -> pd.DataFrame:
    tidy = pd.read_parquet(ROOT / "data" / "deciles.parquet")
    picked = tidy[(tidy.horizon == HORIZON) & (tidy.weighting == WEIGHTING)]
    wide = picked.pivot(index="date", columns="decile", values="ret").sort_index()
    return wide.loc[f"{FIRST_YEAR}":]


def frame(wide: pd.DataFrame, upto: pd.Timestamp, *, x_range: list[str], y_log_range: list[float]):
    fan = figures.fig_decile_fan(
        wide,
        horizon_label="Prior 2 to 12 months",
        reveal_until=upto,
        x_range=x_range,
        y_log_range=y_log_range,
        label_size=22,
    )
    fan.update_layout(title=None)

    # The narrative beat: the marker lands the moment the reveal passes publication.
    if upto.year >= PUBLISHED_YEAR:
        fan.add_vline(
            x=pd.Timestamp(f"{PUBLISHED_YEAR}-01-01").timestamp() * 1000,
            line={"color": theme.LINE_STRONG, "width": 1, "dash": "dot"},
            annotation_text="the paper is published",
            annotation_position="top right",
            annotation_font={"family": theme.FONT_BODY, "size": 19, "color": theme.FG_MUTED},
        )

    return render.for_video(fan, title=TITLE, subtitle=str(upto.year), footer=FOOTER)


def build(preview_year: int | None = None) -> int:
    theme.register()
    wide = load()
    wealth = figures.wealth_curves(wide)
    y_log_range = figures.log_range(wealth)
    x_range = [wide.index[0].isoformat(), wide.index[-1].isoformat()]

    final = wealth.iloc[-1]
    print(f"final value of one dollar: bottom decile {final[1]:,.3f}x, top decile {final[10]:,.0f}x")
    print(f"fixed y range: 10^{y_log_range[0]:.2f} to 10^{y_log_range[1]:.2f}")

    # Two frames a year keeps the reveal smooth and lands the clip near eleven seconds.
    last = wide.index[-1]
    steps = [
        stamp
        for year in range(FIRST_FRAME_YEAR, last.year + 1)
        for stamp in (pd.Timestamp(f"{year}-06-30"), pd.Timestamp(f"{year}-12-31"))
        if stamp <= last
    ]

    if preview_year is not None:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / f"{SLUG}-preview-{preview_year}.png"
        frame(
            wide, pd.Timestamp(f"{preview_year}-12-31"), x_range=x_range, y_log_range=y_log_range
        ).write_image(path, width=render.SIZE, height=render.SIZE)
        print(f"wrote {path.relative_to(ROOT)}")
        return 0

    seconds = (len(steps) + render.FPS * 1.5) / render.FPS
    print(f"{len(steps)} frames at {render.FPS} fps, about {seconds:.0f} s with the hold")
    frames = [frame(wide, upto, x_range=x_range, y_log_range=y_log_range) for upto in steps]

    scratch = OUT / "frames" / SLUG
    render.write_frames(frames, scratch)
    mp4 = render.frames_to_mp4(scratch, OUT / f"{SLUG}.mp4")
    gif = render.mp4_to_gif(mp4, ROOT / "assets" / "previews" / f"{SLUG}.gif")

    for path in (mp4, gif):
        info = render.probe(path)
        print(
            f"  {path.name}: {info.get('width')}x{info.get('height')} "
            f"{float(info.get('duration', 0)):.1f}s {path.stat().st_size / 1_048_576:.2f} MB "
            f"streams={info.get('codec_types', '').rstrip(',')}"
        )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=int, metavar="YEAR", help="render one frame and stop")
    args = parser.parse_args()
    sys.exit(build(args.preview))
