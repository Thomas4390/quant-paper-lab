"""Page furniture shared by every paper: header, citation, stat tiles, disclaimer.

The disclaimer is not optional. This repo publishes reproductions of academic results on
public data, under the name of a firm that sells mandates. Every page has to say plainly
what the numbers are and what they are not.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import yaml

from lab import theme

DISCLAIMER = (
    "Educational reproduction on public data, published by Synerqo. "
    "These are historical results from academic portfolios, not the performance of any "
    "Synerqo strategy, product or account, and not investment advice. "
    "Past returns do not predict future returns. Figures are rebuilt from the sources "
    "listed above, and the code that builds them is public."
)


def load_paper(directory: str | Path) -> dict:
    """Read a paper's paper.yaml. It is the single source for the citation block."""
    path = Path(directory) / "paper.yaml"
    paper = yaml.safe_load(path.read_text(encoding="utf-8"))
    missing = {"slug", "title", "authors", "year", "journal", "url"} - paper.keys()
    if missing:
        raise ValueError(f"{path} is missing required keys: {sorted(missing)}")
    return paper


def page_header(paper: dict) -> None:
    """Eyebrow, title, one-liner and citation, in that order."""
    st.markdown(
        f'<div class="eyebrow">Paper reproduction · {paper["year"]}</div>',
        unsafe_allow_html=True,
    )
    st.title(paper["title"])
    if paper.get("one_liner"):
        st.markdown(
            f'<p style="color:{theme.FG_MUTED};font-size:17px;max-width:62ch;margin:0 0 20px">'
            f'{paper["one_liner"]}</p>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="citation">{paper["authors"]} ({paper["year"]}). '
        f'<em>{paper["title"]}</em>. {paper["journal"]}. '
        f'<a href="{paper["url"]}" target="_blank" rel="noopener" '
        f'style="color:{theme.ACCENT};text-decoration:none">Read the paper</a></div>',
        unsafe_allow_html=True,
    )
    st.write("")


def stat_tiles(tiles: list[tuple[str, str, str]]) -> None:
    """A row of stat tiles: (label, value, note). The number leads, the label whispers."""
    for column, (label, value, note) in zip(st.columns(len(tiles)), tiles, strict=True):
        with column:
            st.markdown(
                f'<div style="border-left:1px solid {theme.LINE};padding:2px 0 2px 14px">'
                f'<div class="eyebrow">{label}</div>'
                f'<div style="font-family:{theme.FONT_MONO};font-size:26px;color:{theme.FG};'
                f'font-variant-numeric:tabular-nums;line-height:1.35">{value}</div>'
                f'<div style="font-size:12px;color:{theme.FG_SUBTLE}">{note}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


def figure(fig, *, caption: str | None = None, key: str | None = None) -> None:
    """Render a Plotly figure with the house configuration, plus an optional caption."""
    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        config={"displayModeBar": False, "scrollZoom": False},
    )
    if caption:
        st.markdown(
            f'<p style="color:{theme.FG_SUBTLE};font-size:12px;margin:-8px 0 28px;'
            f'max-width:78ch">{caption}</p>',
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
