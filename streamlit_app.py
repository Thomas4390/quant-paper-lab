"""Entry point. Registers the brand theme, then hands over to the selected page.

Navigation is built from the papers/ directory, so a new paper folder shows up here without
touching this file.
"""

from __future__ import annotations

import streamlit as st

from lab import arrow, registry, theme

# Before anything imports pyarrow, which is why it sits above every other statement that runs.
# Streamlit reaches for Arrow the first time a dataframe is rendered, and on pyarrow's own
# default pool that call segfaults the whole server. See lab/arrow.py.
arrow.use_stable_memory_pool()

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
