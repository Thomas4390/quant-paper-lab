"""3D animation of the rolling Hill tail index of the S&P 500: GIF for the web, MP4 for LinkedIn.

Run:
  uv run --no-project --with numpy --with pandas --with pyarrow --with matplotlib \
      python render.py            # full clip into out/hill/
  ... python render.py --preview 2009   # one still, window ending in that year

LinkedIn flattens an animated GIF to its first frame, so the feed asset is the MP4.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lab import theme

from tail_numbers import K_READ, KS, WINDOW, load_losses, rolling_frame

OUT = ROOT / "out/hill"
FPS = 12
REVEAL_FRAMES = 150  # 12.5 s of reveal
HOLD_FRAMES = 30  # 2.5 s on the finished surface
T_STEP = 10  # trading days between surface columns
K_STEP = 4
Z_LIM = (1.0, 7.2)  # frozen across frames, holds the whole surface (asserted in build)
C_LIM = (
    1.5,
    4.5,
)  # colour saturates outside, so the band where the story lives keeps contrast

# Low alpha is the fat, dangerous tail, so it takes the brand's thermal amber.
CMAP = LinearSegmentedColormap.from_list(
    "tail", [theme.NEGATIVE, theme.FG_SUBTLE, theme.ACCENT]
)
EVENTS = [
    ("1987-10-19", "Black Monday"),
    ("2008-10-15", "2008"),
    ("2020-03-16", "Covid"),
]

plt.rcParams.update(
    {
        "font.family": "Inter",
        "text.color": theme.FG,
        "axes.labelcolor": theme.FG_MUTED,
        "xtick.color": theme.FG_SUBTLE,
        "ytick.color": theme.FG_SUBTLE,
    }
)


def decimal_year(idx) -> np.ndarray:
    return idx.year + (idx.dayofyear - 1) / 365.25


def build():
    loss = load_losses()
    a = rolling_frame(loss)
    lo, hi = a.min().min(), a.max().max()
    assert Z_LIM[0] <= lo and hi <= Z_LIM[1], (lo, hi)
    rows = np.unique(
        np.r_[np.arange(0, len(a), T_STEP), len(a) - 1]
    )  # always end on the latest window
    grid = a.iloc[rows, ::K_STEP]
    t = decimal_year(grid.index)
    return a, grid, t


def make_figure():
    fig = plt.figure(figsize=(12, 12), dpi=100, facecolor=theme.BG)
    ax = fig.add_axes([-0.08, 0.15, 1.16, 0.72], projection="3d", facecolor=theme.BG)
    ax.view_init(elev=26, azim=-58)
    ax.set_box_aspect((2.2, 1.15, 1.1), zoom=1.1)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((0, 0, 0, 0))
        axis._axinfo["grid"].update(color=theme.LINE, linewidth=0.6)
        axis.line.set_color(theme.LINE_STRONG)
    ax.tick_params(labelsize=13, pad=2)
    return fig, ax


def draw_static(fig, ax, t, a):
    ax.set_xlim(t[0], t[-1])
    ax.set_ylim(KS[0], KS[-1])
    ax.set_zlim(*Z_LIM)
    ax.set_xticks(range(1985, 2026, 5))
    ax.set_yticks([20, 50, 100])
    ax.set_yticklabels(["2%", "5%", "10%"])
    ax.set_zticks([2, 3, 4, 5, 6, 7])
    ax.set_xlabel("Last day of the 4-year window", fontsize=14, labelpad=16)
    ax.set_ylabel("Tail used\n(worst days)", fontsize=14, labelpad=16)
    ax.set_zlabel("Tail index α", fontsize=14, labelpad=8)

    fig.text(
        0.06,
        0.945,
        "How fat is the S&P 500's crash tail?",
        fontsize=34,
        fontfamily="Inter Display",
        fontweight="semibold",
        color=theme.FG,
    )
    fig.text(
        0.06,
        0.905,
        "Hill tail index of daily losses, rolling 4-year window",
        fontsize=18,
        color=theme.FG_MUTED,
    )
    fig.text(
        0.06,
        0.866,
        "Lower α  =  fatter tail  =  extreme crashes more likely",
        fontsize=18,
        color=theme.NEGATIVE,
        fontweight="medium",
    )

    cax = fig.add_axes([0.06, 0.075, 0.36, 0.014])
    cb = fig.colorbar(
        plt.cm.ScalarMappable(Normalize(*C_LIM), CMAP),
        cax=cax,
        orientation="horizontal",
        ticks=[1.5, 2.5, 3.5, 4.5],
    )
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=12, colors=theme.FG_SUBTLE, length=0)
    cb.ax.set_xticklabels(["1.50", "2.50", "3.50", "4.50"])
    fig.text(
        0.24,
        0.098,
        "≈ 3, the long-run norm",
        fontsize=12,
        color=theme.FG_MUTED,
        ha="center",
    )
    fig.text(0.06, 0.098, "fatter tail", fontsize=12, color=theme.NEGATIVE)
    fig.text(0.42, 0.098, "thinner tail", fontsize=12, color=theme.ACCENT, ha="right")
    fig.text(
        0.94,
        0.083,
        "S&P 500 daily closes, Yahoo Finance, 1980 to Oct 2026\n"
        f"Window {WINDOW:,} trading days. White line: worst 5% of days (k = {K_READ}).",
        fontsize=11.5,
        color=theme.FG_SUBTLE,
        ha="right",
        va="center",
        linespacing=1.5,
    )
    fig.text(
        0.94,
        0.035,
        "SYNERQO",
        fontsize=14,
        color=theme.ACCENT,
        ha="right",
        fontweight="bold",
        fontfamily="Inter Display",
    )
    fig.text(
        0.06,
        0.035,
        "Educational illustration. Not investment advice.",
        fontsize=11.5,
        color=theme.FG_SUBTLE,
    )

    date_txt = fig.text(
        0.94,
        0.945,
        "",
        fontsize=30,
        ha="right",
        color=theme.FG,
        fontfamily="Inter Display",
        fontweight="semibold",
    )
    alpha_txt = fig.text(
        0.94, 0.900, "", fontsize=24, ha="right", color=theme.FG, fontweight="medium"
    )
    band_txt = fig.text(0.94, 0.868, "", fontsize=14, ha="right", color=theme.FG_SUBTLE)
    return date_txt, (alpha_txt, band_txt)


def render_frame(ax, state, grid, t, a, e, date_txt, alpha_txt, events):
    for artist in state:
        artist.remove()
    state.clear()
    T, K = np.meshgrid(t[:e], grid.columns, indexing="ij")
    Z = grid.to_numpy()[:e]
    colors = CMAP(Normalize(*C_LIM, clip=True)(Z))
    state.append(
        ax.plot_surface(
            T,
            K,
            Z,
            facecolors=colors,
            rstride=1,
            cstride=1,
            linewidth=0,
            antialiased=False,
            shade=False,
        )
    )
    line = a[K_READ].loc[: grid.index[e - 1]]
    tl = decimal_year(line.index)
    state.extend(
        ax.plot(
            tl,
            np.full(len(tl), K_READ),
            line.to_numpy() + 0.03,
            color=theme.FG,
            linewidth=1.6,
            zorder=10,
        )
    )
    state.append(
        ax.scatter(
            [tl[-1]],
            [K_READ],
            [line.iloc[-1] + 0.03],
            s=60,
            color=theme.FG,
            depthshade=False,
            zorder=11,
        )
    )
    for (
        day,
        tx,
        z,
        label,
    ) in events:  # a mark appears only once the reveal has reached it
        if day <= grid.index[e - 1]:
            state.append(
                ax.text(
                    tx,
                    K_READ,
                    z - 0.45,
                    label,
                    fontsize=13,
                    color=theme.FG,
                    ha="center",
                    va="top",
                    zorder=12,
                )
            )
    v = line.iloc[-1]
    se = v / np.sqrt(K_READ)
    date_txt.set_text(f"{line.index[-1]:%b %Y}")
    alpha_txt[0].set_text(f"α = {v:.2f}")
    alpha_txt[1].set_text(f"95% band {v - 1.96 * se:.2f} to {v + 1.96 * se:.2f} (iid)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--preview", type=int, help="render one still, window ending in this year"
    )
    args = p.parse_args()

    import pandas as pd

    a, grid, t = build()
    events = []
    for (
        d,
        label,
    ) in EVENTS:  # label the trough of alpha among the windows holding that day
        held = a[K_READ].loc[pd.Timestamp(d) :].iloc[:WINDOW]
        trough = held.idxmin()
        events.append(
            (trough, decimal_year(pd.DatetimeIndex([trough]))[0], held.min(), label)
        )
    fig, ax = make_figure()
    date_txt, alpha_txt = draw_static(fig, ax, t, a)
    state: list = []
    OUT.mkdir(parents=True, exist_ok=True)

    if args.preview:
        e = int(
            np.searchsorted(grid.index, pd.Timestamp(f"{args.preview}-12-31"))
        ) or len(grid)
        render_frame(
            ax, state, grid, t, a, min(e, len(grid)), date_txt, alpha_txt, events
        )
        path = OUT / f"preview-{args.preview}.png"
        fig.savefig(path, facecolor=theme.BG)
        print(path)
        return

    frames = OUT / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()
    ends = np.unique(np.linspace(2, len(grid), REVEAL_FRAMES).round().astype(int))
    for i, e in enumerate(ends):
        render_frame(ax, state, grid, t, a, e, date_txt, alpha_txt, events)
        fig.savefig(frames / f"f{i:04d}.png", facecolor=theme.BG)
    for j in range(HOLD_FRAMES):
        shutil.copy(
            frames / f"f{len(ends) - 1:04d}.png", frames / f"f{len(ends) + j:04d}.png"
        )

    src = ["-framerate", str(FPS), "-i", str(frames / "f%04d.png")]
    run = lambda *x: subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *x], check=True
    )
    run(
        *src,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-movflags",
        "+faststart",
        str(OUT / "hill-sp500.mp4"),
    )
    gif_scale = "fps=12,scale=900:-1:flags=lanczos"
    run(
        *src,
        "-vf",
        f"{gif_scale},palettegen=max_colors=128:stats_mode=diff",
        str(OUT / "palette.png"),
    )
    run(
        *src,
        "-i",
        str(OUT / "palette.png"),
        "-lavfi",
        f"{gif_scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
        str(OUT / "hill-sp500.gif"),
    )
    # The feed shows the first frame before play, so give it the finished surface as a poster.
    shutil.copy(frames / f"f{len(ends) - 1:04d}.png", OUT / "hill-sp500-poster.png")
    print(OUT)


if __name__ == "__main__":
    main()
