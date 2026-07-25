"""The library index. Masthead, then one entry per paper, newest first.

This is where a reader arriving from a post lands, so it has one job before anything else:
say whose work this is and on what terms. The Apex and the wordmark carry the first, the
ledger strip carries the second, and only then does the page start on a paper.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab import layout, registry, theme

HERE = Path(__file__).resolve().parent
LOGO = HERE / "assets" / "logo" / "synerqo-logo-primary-dark.svg"
PREVIEWS = HERE / "assets" / "previews"


def masthead() -> None:
    st.markdown(
        f'<div class="brand-lockup">{LOGO.read_text(encoding="utf-8")}</div>'
        '<div class="masthead">'
        '<div class="eyebrow">Quant Paper Lab</div>'
        # A real h1, not a styled div. The masthead headline is the page's heading, and a
        # page whose only heading is a div reads as untitled to anything that is not a
        # sighted browser.
        f'<h1 style="font-family:{theme.FONT_DISPLAY};font-size:44px;font-weight:500;'
        f'line-height:1.15;color:{theme.FG};margin:14px 0 18px;max-width:27ch;padding:0">'
        "Landmark papers, rebuilt so you can turn the knobs</h1>"
        f'<p style="color:{theme.FG_MUTED};font-size:17px;line-height:1.7;'
        f'max-width:{theme.MEASURE};margin:0">'
        "One paper at a time from the financial engineering literature, reproduced on public "
        "data, with the figures made interactive. The code that builds every number is "
        "public, so you can check the result instead of taking it on faith."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def ledger(papers: list[dict]) -> None:
    """What the reader is getting, in the terms a sceptic would ask for first."""
    sources = sorted({s["name"] for p in papers for s in p.get("data_sources", [])})
    st.markdown(
        '<div class="ledger">'
        f"<div><b>{len(papers)}</b> reproduction{'' if len(papers) == 1 else 's'}</div>"
        f"<div>Data <b>{', '.join(sources) or 'public sources'}</b></div>"
        "<div>Figures <b>rebuilt from source</b></div>"
        "<div>Results <b>gross of costs</b></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def entry(paper: dict) -> None:
    """One paper: what it claims, what it looks like, and the way in.

    The still runs the full width rather than sitting in a column beside the text. Ten log
    curves at four hundred pixels are decoration. At full width they are the argument, which
    is the only reason to put a picture on an index like this one.
    """
    st.markdown(
        '<div class="entry-rule"></div>'
        f'<div class="eyebrow">{paper["authors"]} · {paper["year"]}</div>'
        f'<div class="entry-title">{paper["title"]}</div>'
        f'<p style="color:{theme.FG_MUTED};font-size:15.5px;line-height:1.7;'
        f'max-width:{theme.MEASURE};margin:0">{paper.get("one_liner", "")}</p>'
        f'<div class="entry-meta">{paper["journal"]}<br>'
        f'<span>{", ".join(s["name"] for s in paper.get("data_sources", []))}</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    still = PREVIEWS / f"{paper.get('url_path', paper['slug'])}-card.png"
    if still.exists():
        st.image(str(still))
        # The caption belongs to the paper, not to this loop. A figure legend written here
        # would describe the momentum still on top of whatever the next paper ships.
        if paper.get("card_note"):
            st.markdown(
                f'<p class="plate-note">{paper["card_note"]}</p>', unsafe_allow_html=True
            )
    st.page_link(paper["page"], label="Open the reproduction")


masthead()
papers = registry.papers()
ledger(papers)
for paper in papers:
    entry(paper)

st.markdown(
    '<div class="colophon">'
    '<a href="mailto:contact@synerqo.com">contact@synerqo.com</a>'
    '<a href="https://synerqo.com" target="_blank" rel="noopener">synerqo.com</a>'
    "</div>"
    f'<div class="disclaimer">{layout.DISCLAIMER}</div>',
    unsafe_allow_html=True,
)
