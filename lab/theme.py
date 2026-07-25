"""Synerqo visual identity, declared once for both the app and the rendered video.

Colors are the brand's canonical hex seeds (see the synerqo-brand skill and synerqo.com).
The brand authors in OKLCH, so each value carries its OKLCH origin in a comment. Hex is
what Plotly and the headless renderer actually consume.

Every figure in this repo must go through PLOTLY_TEMPLATE. That is what keeps the app and
the MP4 frames from drifting apart.

Color policy, in short:
  Emerald carries identity and stays under 10 percent of the chrome.
  Full-spectrum color is allowed only when it encodes data. Here that means one diverging
  scale, amber for negative through neutral gray to emerald for positive. The pair was
  validated for color-vision deficiency (deuteranopia dE 13.1, floor 8) so the polarity
  survives without relying on red versus green.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --- Surfaces and ink -------------------------------------------------------------
BG = "#0D0F12"  # oklch(0.165 0.006 250) graphite, the brand's primary dark surface
BG_ELEVATED = "#15171A"  # oklch(0.205 0.006 250)
LINE = "#2A2D30"  # oklch(0.295 0.007 250) hairlines, grid
LINE_STRONG = "#3F4347"  # oklch(0.380 0.008 250) emphasized rules, neutral scale midpoint
FG = "#EFF3F8"  # oklch(0.955 0.008 240) primary text
FG_MUTED = "#ADB2B6"  # oklch(0.760 0.008 240) secondary text
FG_SUBTLE = "#7E8286"  # oklch(0.605 0.008 240) captions, tick labels

# --- Accent and polarity ----------------------------------------------------------
ACCENT = "#00C896"  # oklch(0.745 0.158 165) emerald, digital only
ACCENT_HOVER = "#00B682"  # oklch(0.685 0.150 165)
NEGATIVE = "#FF7C00"  # oklch(0.780 0.250 56), the brand thermal ramp at 0.86

#: Diverging scale for any quantity that can flip sign. Always pass cmid=0 with it.
DIVERGING = [[0.0, NEGATIVE], [0.5, LINE_STRONG], [1.0, ACCENT]]

# --- Type -------------------------------------------------------------------------
# Google Fonts are loaded by inject_css() for the browser. The headless renderer used for
# video frames falls back to the next family in the stack when a font is not installed
# system wide, which is why every stack ends in a widely available face.
FONT_BODY = "DM Sans, Inter, Helvetica Neue, Arial, sans-serif"
FONT_DISPLAY = "Playfair Display, Georgia, serif"
FONT_MONO = "JetBrains Mono, DejaVu Sans Mono, Menlo, monospace"

_TEMPLATE_NAME = "synerqo"


def _axis(*, grid: bool = True) -> dict:
    """Recessive axis: hairline grid, subtle ticks, no heavy frame."""
    return {
        "showgrid": grid,
        "gridcolor": LINE,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": LINE_STRONG,
        "zerolinewidth": 1,
        "showline": False,
        "ticks": "outside",
        "ticklen": 4,
        "tickcolor": LINE,
        "tickfont": {"family": FONT_MONO, "size": 12, "color": FG_SUBTLE},
        "title": {"font": {"family": FONT_BODY, "size": 13, "color": FG_MUTED}},
        "automargin": True,
    }


def _scene_axis(title: str) -> dict:
    """3D axes need their own styling: Plotly ignores the 2D axis template there."""
    return {
        "title": {"text": title, "font": {"family": FONT_BODY, "size": 12, "color": FG_MUTED}},
        "backgroundcolor": BG,
        "showbackground": True,
        "gridcolor": LINE,
        "zerolinecolor": LINE_STRONG,
        "tickfont": {"family": FONT_MONO, "size": 10, "color": FG_SUBTLE},
    }


def scene(x_title: str, y_title: str, z_title: str) -> dict:
    """Styled 3D scene. Kept as a helper because every surface figure needs it."""
    return {
        "xaxis": _scene_axis(x_title),
        "yaxis": _scene_axis(y_title),
        "zaxis": _scene_axis(z_title),
        "camera": {"eye": {"x": 1.55, "y": -1.65, "z": 0.85}},
        "aspectratio": {"x": 1, "y": 1, "z": 0.62},
    }


def register() -> None:
    """Register the Synerqo Plotly template and make it the default."""
    pio.templates[_TEMPLATE_NAME] = go.layout.Template(
        layout={
            "paper_bgcolor": BG,
            "plot_bgcolor": BG,
            "font": {"family": FONT_BODY, "size": 14, "color": FG},
            "title": {
                "font": {"family": FONT_DISPLAY, "size": 20, "color": FG},
                "x": 0,
                "xanchor": "left",
                "pad": {"b": 12},
            },
            "colorway": [ACCENT, FG_MUTED, NEGATIVE, FG_SUBTLE],
            "xaxis": _axis(),
            "yaxis": _axis(),
            "legend": {
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "font": {"family": FONT_BODY, "size": 12, "color": FG_MUTED},
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.0,
                "xanchor": "right",
                "x": 1.0,
            },
            "hoverlabel": {
                "bgcolor": BG_ELEVATED,
                "bordercolor": LINE_STRONG,
                "font": {"family": FONT_MONO, "size": 12, "color": FG},
            },
            "margin": {"l": 64, "r": 24, "t": 56, "b": 48},
        }
    )
    pio.templates.default = _TEMPLATE_NAME


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Playfair+Display:wght@500&family=JetBrains+Mono:wght@400&display=swap');

:root {{
  --bg: {BG};
  --bg-elevated: {BG_ELEVATED};
  --line: {LINE};
  --fg: {FG};
  --fg-muted: {FG_MUTED};
  --fg-subtle: {FG_SUBTLE};
  --accent: {ACCENT};
}}

html, body, [class*="css"] {{ font-family: {FONT_BODY}; }}
h1, h2, h3 {{ font-family: {FONT_DISPLAY}; font-weight: 500; letter-spacing: 0; }}
code, pre, .stMetricValue {{ font-family: {FONT_MONO}; font-variant-numeric: tabular-nums; }}

/* The eyebrow above a section title. Uppercase, subtle, never emerald. */
.eyebrow {{
  font-family: {FONT_BODY};
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: {FG_SUBTLE};
}}

.citation {{
  border-left: 2px solid {ACCENT};
  padding: 2px 0 2px 14px;
  color: {FG_MUTED};
  font-size: 14px;
  line-height: 1.6;
}}

.disclaimer {{
  border-top: 1px solid {LINE};
  margin-top: 40px;
  padding-top: 16px;
  color: {FG_SUBTLE};
  font-size: 12px;
  line-height: 1.7;
}}

/* Focus ring: 2px emerald at 2px offset, on every interactive element. */
*:focus-visible {{ outline: 2px solid {ACCENT}; outline-offset: 2px; }}

@media (prefers-reduced-motion: reduce) {{
  * {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
}}
</style>
"""


def inject_css() -> None:
    """Load brand fonts and CSS tokens into the Streamlit page."""
    import streamlit as st

    st.markdown(CSS, unsafe_allow_html=True)
