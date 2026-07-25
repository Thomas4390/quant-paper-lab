"""Entry point. Registers the brand theme, then hands over to the selected page.

Navigation is built from the papers/ directory, so a new paper folder shows up here without
touching this file.
"""

from __future__ import annotations

import streamlit as st

from lab import registry, theme

st.set_page_config(
    page_title="Quant Paper Lab · Synerqo",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.register()
theme.inject_css()

pages = [st.Page("home.py", title="The library", default=True)]
pages += [
    st.Page(paper["page"], title=paper.get("nav_title", paper["title"]), url_path=paper.get("url_path"))
    for paper in registry.papers()
]

st.navigation(pages).run()
