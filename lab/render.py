"""Turn Plotly figures into the assets a LinkedIn post actually needs.

The important constraint, learned the hard way: LinkedIn does not animate GIFs in the feed.
An uploaded GIF is flattened to its first frame. Motion has to ship as native video, which
autoplays muted. So the MP4 is the deliverable and the GIF is a by-product for the README,
for X and for the site.

This module deliberately does not import streamlit. The whole render path stays free of the
app runtime, which is what lets the same figures.py drive both.

Format targets, square because it takes the most vertical space in the feed:
  1200 by 1200, 12 fps, 10 to 15 seconds, no audio track, all labels burned in.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import plotly.graph_objects as go

from lab import theme

SIZE = 1200
FPS = 12


def for_video(fig: go.Figure, *, title: str, subtitle: str, footer: str) -> go.Figure:
    """Lay a figure out for a square muted frame.

    Type goes up, chrome goes down, and every label the interactive version would have put
    in a tooltip has to be visible instead. Uses the body font family throughout: the
    display face is a webfont and the headless renderer only sees installed fonts.
    """
    out = go.Figure(fig)

    # A feed frame is read at a glance on a phone. Everything that carries meaning has to
    # survive that: thicker strokes, bigger ticks, no legend box competing with the title.
    for trace in out.data:
        width = getattr(getattr(trace, "line", None), "width", None)
        if width:
            trace.line.width = width * 1.8
    out.update_xaxes(
        tickfont={"family": theme.FONT_MONO, "size": 20, "color": theme.FG_SUBTLE},
        title_font={"family": theme.FONT_BODY, "size": 20, "color": theme.FG_MUTED},
    )
    out.update_yaxes(
        tickfont={"family": theme.FONT_MONO, "size": 20, "color": theme.FG_SUBTLE},
        title_font={"family": theme.FONT_BODY, "size": 20, "color": theme.FG_MUTED},
    )

    out.update_layout(
        width=SIZE,
        height=SIZE,
        showlegend=False,
        title={
            "text": title,
            "font": {"family": theme.FONT_BODY, "size": 34, "color": theme.FG},
            "x": 0.055,
            "xanchor": "left",
            "y": 0.955,
            "yanchor": "top",
        },
        margin={"l": 40, "r": 300, "t": 190, "b": 110},
        # Append, never replace: the figure's own end-of-line labels are what stand in for
        # the legend once the legend is gone.
        annotations=list(out.layout.annotations)
        + [
            {
                "text": subtitle,
                "xref": "paper",
                "yref": "paper",
                "x": 0.055,
                "y": 1.075,
                "xanchor": "left",
                "yanchor": "top",
                "showarrow": False,
                "font": {"family": theme.FONT_MONO, "size": 26, "color": theme.ACCENT},
            },
            {
                "text": footer,
                "xref": "paper",
                "yref": "paper",
                "x": 0.055,
                "y": -0.085,
                "xanchor": "left",
                "yanchor": "bottom",
                "showarrow": False,
                "font": {"family": theme.FONT_BODY, "size": 19, "color": theme.FG_SUBTLE},
            },
        ],
    )
    return out


def write_frames(figures: list[go.Figure], directory: Path) -> list[Path]:
    """Export each figure as a numbered PNG. Returns the paths in order."""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    paths = []
    for index, fig in enumerate(figures):
        path = directory / f"frame_{index:04d}.png"
        fig.write_image(path, width=SIZE, height=SIZE, scale=1)
        paths.append(path)
    return paths


def _ffmpeg(args: list[str]) -> None:
    result = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-800:]}")


def frames_to_mp4(directory: Path, out_path: Path, *, fps: int = FPS, hold_seconds: float = 1.5) -> Path:
    """Encode the frames into a feed ready MP4: H.264, yuv420p, no audio track.

    The last frame is held so a viewer sees the end state before the loop restarts.
    """
    frames = sorted(directory.glob("frame_*.png"))
    if not frames:
        raise FileNotFoundError(f"no frames in {directory}")
    last = frames[-1]
    start = len(frames)
    for extra in range(round(fps * hold_seconds)):
        shutil.copy(last, directory / f"frame_{start + extra:04d}.png")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(
        [
            "-framerate", str(fps),
            "-i", str(directory / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-crf", "20",
            "-movflags", "+faststart",
            "-an",
            str(out_path),
        ]
    )
    return out_path


def mp4_to_gif(mp4_path: Path, out_path: Path, *, fps: int = FPS, width: int = 760) -> Path:
    """Derive a GIF from the MP4. Not for LinkedIn, for the README and other networks."""
    palette = out_path.with_suffix(".palette.png")
    scale = f"fps={fps},scale={width}:-1:flags=lanczos"
    _ffmpeg(["-i", str(mp4_path), "-vf", f"{scale},palettegen=max_colors=128", str(palette)])
    _ffmpeg(
        [
            "-i", str(mp4_path),
            "-i", str(palette),
            "-lavfi", f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
            "-loop", "0",
            str(out_path),
        ]
    )
    palette.unlink(missing_ok=True)
    return out_path


def probe(path: Path) -> dict:
    """Read back what was written: dimensions, fps, duration, audio presence."""
    fields = "stream=width,height,r_frame_rate,codec_type:format=duration,size"
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", fields, "-of", "default=noprint_wrappers=1", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            info.setdefault(key, value)
            if key == "codec_type":
                info.setdefault("codec_types", "")
                info["codec_types"] += value + ","
    return info
