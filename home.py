"""The library index. One card per paper, newest first."""

from __future__ import annotations

import streamlit as st

from lab import layout, registry, theme

st.markdown('<div class="eyebrow">Synerqo · Quant Paper Lab</div>', unsafe_allow_html=True)
st.title("Landmark papers, rebuilt so you can turn the knobs")
st.markdown(
    f'<p style="color:{theme.FG_MUTED};font-size:17px;max-width:64ch;line-height:1.65">'
    "One paper at a time from the financial engineering literature, reproduced on public "
    "data, with the figures made interactive. The code that builds every number is public, "
    "so you can check the result instead of taking it on faith."
    "</p>",
    unsafe_allow_html=True,
)
st.write("")

for paper in registry.papers():
    st.markdown(
        f'<div style="border-top:1px solid {theme.LINE};padding-top:18px;margin-top:12px">'
        f'<div class="eyebrow">{paper["authors"]} · {paper["year"]}</div>'
        f'<div style="font-family:{theme.FONT_DISPLAY};font-size:22px;color:{theme.FG};'
        f'margin:6px 0 8px">{paper["title"]}</div>'
        f'<p style="color:{theme.FG_MUTED};font-size:15px;max-width:70ch;margin:0 0 10px">'
        f'{paper.get("one_liner", "")}</p></div>',
        unsafe_allow_html=True,
    )
    st.page_link(paper["page"], label="Open the reproduction")

st.markdown(
    f'<div class="disclaimer">{layout.DISCLAIMER}</div>',
    unsafe_allow_html=True,
)
