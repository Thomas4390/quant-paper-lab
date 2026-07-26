"""Synerqo visual identity, declared once for both the app and the rendered video.

Colors are the brand's canonical hex seeds (see the synerqo-brand skill and synerqo.com).
The brand authors in OKLCH, so each value carries its OKLCH origin in a comment. Hex is what
Plotly and the headless renderer actually consume.

Every figure in this repo must go through PLOTLY_TEMPLATE, and every figure must be rendered
with `theme=None`. Streamlit's default is to overwrite a figure's typography with its own,
which silently neutralises everything below.

Fonts are declared in .streamlit/config.toml, not here. A CSS rule injected into the page
loses the cascade to Streamlit's own class selectors, and because webfonts load lazily, a
family that never wins a rule is never even downloaded.

Color policy, in short:
  Emerald carries identity and stays under 10 percent of the chrome.
  Full-spectrum color is allowed only when it encodes data. Here that means one diverging
  scale for signed quantities, validated for colour-vision deficiency (deuteranopia dE 13.1
  against a floor of 8) so polarity never rests on red against green.
  Rank is ordered, not signed, so it takes a single-hue ramp. Using the diverging scale for
  decile rank put four of the ten lines under 3:1 against the background and made two of them
  the same lightness.
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

#: Single-hue ramp for ordered ranks, dark to light at hue 165. Every step clears 3:1
#: against the graphite surface, from 3.8:1 to 11.3:1, and lightness rises monotonically.
RANK_RAMP = [
    "#377E62",
    "#3A8A6B",
    "#3D9674",
    "#3FA27D",
    "#42AF86",
    "#45BB8F",
    "#47C899",
    "#49D5A2",
    "#4CE2AC",
]

# --- Rhythm -----------------------------------------------------------------------
# Three spacing steps, not two. Before this the page only ever used 0 or 16 pixels, so the
# gap between two sections read the same as the gap between a figure and its own caption.
SPACE_SECTION = 60
SPACE_BLOCK = 24
SPACE_TIGHT = 8

#: Prose measure, in characters so it holds at any window width. One value for every text
#: block on the page, otherwise the left edge is straight and the right edge is a staircase.
MEASURE = "68ch"

# --- Type -------------------------------------------------------------------------
# Names only. The files are loaded by .streamlit/config.toml, which is the only place that
# wins the cascade against Streamlit's own stylesheet.
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
        "tickfont": {"family": FONT_MONO, "size": 11, "color": FG_SUBTLE},
    }


def scene(x_title: str, y_title: str, z_title: str) -> dict:
    """Styled 3D scene. Kept as a helper because every surface figure needs it."""
    return {
        "xaxis": _scene_axis(x_title),
        "yaxis": _scene_axis(y_title),
        "zaxis": _scene_axis(z_title),
        # Negative x, so the first category of the x axis sits on the left and the last on the
        # right, the way a reader expects to be told a story. From the positive side the axis
        # ran away into the screen and the whole scene read as if seen from behind.
        "camera": {"eye": {"x": -0.85, "y": -1.55, "z": 0.48}},
        # A 3D axis title is drawn outside the box, and Plotly reserves no room for it: at
        # 1.15 the x title was cut to "Prio" in the app while rendering whole at twice the
        # size, which is why a static export never showed it. 0.95 keeps the whole label
        # inside a 560 pixel panel, and the z over x ratio is unchanged, so the relief that
        # makes a point a month legible is exactly as tall as before.
        "aspectratio": {"x": 0.95, "y": 0.95, "z": 0.74},
        # Preserve the camera across frames and across Streamlit reruns. Without it every
        # animation frame snaps the viewpoint back and the reader cannot orbit while playing.
        "uirevision": "synerqo-scene",
    }


def register() -> None:
    """Register the Synerqo Plotly template and make it the default."""
    pio.templates[_TEMPLATE_NAME] = go.layout.Template(
        layout={
            "paper_bgcolor": BG,
            "plot_bgcolor": BG,
            "font": {"family": FONT_BODY, "size": 14, "color": FG},
            "title": {
                # Body face, not the display face. A serif on a chart title is decoration.
                "font": {"family": FONT_BODY, "size": 17, "color": FG},
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
            "uirevision": "synerqo",
        }
    )
    pio.templates.default = _TEMPLATE_NAME


CSS = f"""
<style>
:root {{
  --bg: {BG};
  --bg-elevated: {BG_ELEVATED};
  --line: {LINE};
  --fg: {FG};
  --fg-muted: {FG_MUTED};
  --fg-subtle: {FG_SUBTLE};
  --accent: {ACCENT};
  --measure: {MEASURE};
}}

/* Streamlit leaves a deep gutter above the first block. Pull it back so the opening figure
   reaches the fold. */
.stMainBlockContainer {{ padding-top: 3.2rem; }}

/* Micro label: tile headings, page kicker. Deliberately quiet. */
.eyebrow {{
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: {FG_SUBTLE};
}}

/* Structural label: the only marker of where one section ends and the next begins, so it
   carries a rule and a stronger ink than a tile heading. */
.section-eyebrow {{
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: {FG_MUTED};
  border-top: 1px solid {LINE};
  padding-top: 14px;
}}

.citation, .disclaimer, .measured {{ max-width: var(--measure); }}

.citation {{
  border-left: 2px solid {ACCENT};
  padding: 2px 0 2px 14px;
  color: {FG_MUTED};
  font-size: 14px;
  line-height: 1.65;
}}

.disclaimer {{
  border-top: 1px solid {LINE};
  margin-top: 44px;
  padding-top: 16px;
  color: {FG_SUBTLE};
  font-size: 12px;
  line-height: 1.7;
}}

/* ---------------------------------------------------------------- the brand lockup */

/* The Apex sits above the masthead rule, at the size the charter calls the minimum for the
   primary logo. Clear space is half the symbol height, which is the margin below. */
.brand-lockup svg {{ display: block; height: 52px; width: auto; }}
.brand-lockup {{ margin-bottom: 30px; }}

.masthead {{
  border-top: 1px solid {LINE};
  padding-top: 26px;
}}

/* A quiet strip of what the reader is getting, in the monospace reserved for figures, so it
   reads as metadata rather than as marketing. */
.ledger {{
  display: flex;
  flex-wrap: wrap;
  gap: 0 28px;
  font-family: {FONT_MONO};
  font-size: 11.5px;
  letter-spacing: 0.04em;
  color: {FG_SUBTLE};
  border-top: 1px solid {LINE};
  padding: 12px 0 0;
  margin: 30px 0 0;
}}
.ledger b {{ color: {FG_MUTED}; font-weight: 400; }}

/* ---------------------------------------------------------------- the paper entries */

/* The ledger closes on this rule rather than carrying its own. Two hairlines seventy pixels
   apart read as a rendering accident, not as structure. */
.entry-rule {{ border-top: 1px solid {LINE}; margin: 34px 0 22px; }}

.entry-title {{
  font-family: {FONT_DISPLAY};
  font-size: 27px;
  font-weight: 500;
  line-height: 1.25;
  color: {FG};
  margin: 8px 0 10px;
}}

.entry-meta {{
  font-family: {FONT_MONO};
  font-size: 11.5px;
  color: {FG_SUBTLE};
  margin: 12px 0 18px;
}}
.entry-meta span {{ color: {FG_MUTED}; }}

/* The still is data, not decoration, so it gets a hairline and no rounding, like a plate in
   a paper rather than a card in a feed. */
.stImage img {{ border: 1px solid {LINE}; width: 100%; }}

.plate-note {{
  color: {FG_SUBTLE};
  font-size: 12.5px;
  line-height: 1.6;
  max-width: var(--measure);
  margin: 10px 0 22px;
}}

/* Contact before the legal notice, quiet, in the monospace the figures use. */
.colophon {{
  display: flex;
  gap: 24px;
  font-family: {FONT_MONO};
  font-size: 12px;
  margin-top: 54px;
}}
.colophon a {{ color: {FG_MUTED}; text-decoration: none; }}
.colophon a:hover {{ color: {ACCENT}; }}
.colophon + .disclaimer {{ margin-top: 18px; }}

/* ---------------------------------------------------------------- the call to action */

/* st.page_link ships as an underlined blue-ish link, which reads as boilerplate next to a
   Playfair title. Outlined rather than filled: emerald stays under a tenth of the chrome and
   is spent on the arrow and the hover, where it means "go". */
[data-testid="stPageLink"] a[data-testid="stPageLink-NavLink"] {{
  display: inline-flex;
  align-items: center;
  padding: 11px 20px;
  border: 1px solid {LINE_STRONG};
  border-radius: 2px;
  background: {BG_ELEVATED};
  text-decoration: none;
  transition: border-color 220ms cubic-bezier(0.25, 1, 0.5, 1),
              background-color 220ms cubic-bezier(0.25, 1, 0.5, 1);
}}
[data-testid="stPageLink"] a[data-testid="stPageLink-NavLink"] p {{
  font-family: {FONT_BODY};
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: {FG};
  margin: 0;
}}
[data-testid="stPageLink"] a[data-testid="stPageLink-NavLink"] p::after {{
  content: " \\2192";
  color: {ACCENT};
  letter-spacing: 0;
  padding-left: 10px;
}}
[data-testid="stPageLink"] a[data-testid="stPageLink-NavLink"]:hover {{
  border-color: {ACCENT};
  background: {BG};
}}
[data-testid="stPageLink"] a[data-testid="stPageLink-NavLink"]:hover p {{ color: {ACCENT}; }}

/* The slider rail was the most saturated block on the page, in the same emerald that means
   "top decile" two hundred pixels above. Rail neutral, handle emerald. */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{ background: {ACCENT}; }}

/* Focus ring: 2px emerald at 2px offset, on every interactive element. */
*:focus-visible {{ outline: 2px solid {ACCENT}; outline-offset: 2px; }}

/* Reduced motion only reaches CSS. Plotly animates in JavaScript, which is why nothing on
   this page autoplays: motion starts when the reader presses play. */
@media (prefers-reduced-motion: reduce) {{
  * {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
}}
</style>
"""


def inject_css() -> None:
    """Load the CSS tokens into the Streamlit page. Fonts come from config.toml."""
    import streamlit as st

    st.markdown(CSS, unsafe_allow_html=True)
