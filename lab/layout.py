"""Page furniture shared by every paper: header, sections, stat tiles, disclaimer.

One vertical rhythm, declared once. Every block on a paper page goes through a helper here
rather than through its own inline HTML, which is what keeps the spacing from drifting from
section to section.

The disclaimer is not optional. This repo publishes reproductions of academic results on
public data, under the name of a firm that sells mandates. Every page has to say plainly what
the numbers are and what they are not. It is also why nothing on a page is allowed to raise:
an exception does not blank a chart, it blanks the page, and the notice goes with it.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from lab import theme


DISCLAIMER = (
    "Educational reproduction on public data, published by Synerqo. "
    "These are historical results from academic portfolios, gross of costs, not the "
    "performance of any Synerqo strategy, product or account, and not investment advice. "
    "Past returns do not predict future returns. Figures are rebuilt from the sources listed "
    "above, and the code that builds them is public."
)


def load_paper(directory: str | Path) -> dict:
    """Read a paper's paper.yaml. It is the single source for the citation block."""
    path = Path(directory) / "paper.yaml"
    paper = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = {"slug", "title", "authors", "year", "journal", "url"} - paper.keys()
    if missing:
        raise ValueError(f"{path} is missing required keys: {sorted(missing)}")
    return paper


def _space(height: int) -> None:
    st.markdown(f'<div style="height:{height}px"></div>', unsafe_allow_html=True)


def page_header(paper: dict) -> None:
    """Eyebrow, title, one-liner and citation, in that order."""
    st.markdown(
        f'<div class="eyebrow">Paper reproduction · {paper["year"]}</div>',
        unsafe_allow_html=True,
    )
    st.title(paper["title"])
    if paper.get("one_liner"):
        st.markdown(
            f'<p style="color:{theme.FG_MUTED};font-size:18px;line-height:1.6;'
            f'max-width:{theme.MEASURE};margin:0 0 24px">{paper["one_liner"]}</p>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="citation">{paper["authors"]} ({paper["year"]}). '
        f'<em>{paper["title"]}</em>. {paper["journal"]}. '
        f'<a href="{paper["url"]}" target="_blank" rel="noopener" '
        f'style="color:{theme.ACCENT};text-decoration:none">Read the paper</a></div>',
        unsafe_allow_html=True,
    )
    _space(28)


def section(eyebrow: str, title: str, blurb: str | None = None) -> None:
    """Start a section: eyebrow, heading, and the paragraph that sets up what follows.

    Every section opens the same way, so the page has one rhythm instead of one per block.
    """
    _space(theme.SPACE_SECTION)
    st.markdown(
        f'<div class="section-eyebrow" style="margin-bottom:12px">{eyebrow}</div>'
        f'<div style="font-family:{theme.FONT_DISPLAY};font-size:24px;font-weight:500;'
        f'color:{theme.FG};line-height:1.3;margin-bottom:10px">{title}</div>'
        + (
            f'<p style="color:{theme.FG_MUTED};font-size:15px;line-height:1.65;'
            f'max-width:{theme.MEASURE};margin:0 0 {theme.SPACE_BLOCK}px">{blurb}</p>'
            if blurb
            else ""
        ),
        unsafe_allow_html=True,
    )


def caption(text: str) -> None:
    """Small print under a figure or a table of numbers."""
    st.markdown(
        f'<p style="color:{theme.FG_SUBTLE};font-size:12.5px;line-height:1.6;'
        f'max-width:{theme.MEASURE};margin:-4px 0 8px">{text}</p>',
        unsafe_allow_html=True,
    )


def stat_tiles(tiles: list[tuple[str, str, str]]) -> None:
    """A row of stat tiles: (label, value, note). The number leads, the label whispers.

    An empty list renders nothing. st.columns(0) raises, and a raising helper here would take
    the disclaimer down with it.
    """
    if not tiles:
        return
    _space(4)
    for column, (label, value, note) in zip(st.columns(len(tiles), gap="medium"), tiles, strict=True):
        with column:
            st.markdown(
                f'<div style="border-left:1px solid {theme.LINE};padding:4px 0 4px 14px;'
                f'height:100%">'
                f'<div class="eyebrow">{label}</div>'
                f'<div style="font-family:{theme.FONT_MONO};font-size:27px;color:{theme.FG};'
                f'line-height:1.4;margin:2px 0 4px">{value}</div>'
                f'<div style="font-size:11.5px;color:{theme.FG_SUBTLE};line-height:1.5">{note}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    _space(10)


def figure(fig, *, note: str | None = None, key: str | None = None) -> None:
    """Render a Plotly figure with the house configuration, plus an optional note under it."""
    # theme=None is not a preference. Streamlit's default rewrites the figure's fonts and
    # title sizing with its own, which silently neutralises lab/theme.py inside the app while
    # leaving the video render correct, so the two drift apart.
    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        theme=None,
        config={"displayModeBar": False, "scrollZoom": False},
    )
    if note:
        st.markdown(
            f'<p style="color:{theme.FG_SUBTLE};font-size:12.5px;line-height:1.6;'
            f'max-width:{theme.MEASURE};margin:-6px 0 26px">{note}</p>',
            unsafe_allow_html=True,
        )


def sources_and_disclaimer(paper: dict) -> None:
    """Data provenance then the standing disclaimer. Always last on the page."""
    lines = []
    for source in paper.get("data_sources", []):
        lines.append(
            f'<a href="{source["url"]}" target="_blank" rel="noopener" '
            f'style="color:{theme.FG_MUTED}">{source["name"]}</a> ({source["licence"]})'
        )
    provenance = "Data: " + ", ".join(lines) if lines else ""
    st.markdown(
        f'<div class="disclaimer">{provenance}<br>{DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )
