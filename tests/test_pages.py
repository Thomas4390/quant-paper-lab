"""Smoke test: every page renders through the real navigation, with no exception.

AppTest runs the app the way Streamlit does, so this catches the class of mistake that only
shows up at runtime: a bad widget argument, a missing key, a figure that will not serialize.
Pages are tested through streamlit_app.py because st.page_link only resolves inside the
navigation context.
"""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from lab import registry


def test_the_library_page_renders() -> None:
    """The index carries the brand, a heading, and a way into every paper it lists.

    Asserted on the rendered markup rather than on st.title, because the masthead is laid out
    by hand: what matters is that a reader gets a lockup and an h1, not which Streamlit
    primitive drew them.
    """
    app = AppTest.from_file("streamlit_app.py", default_timeout=180).run()
    assert not app.exception, [e.value for e in app.exception]

    page = " ".join(str(block.value) for block in app.markdown)
    assert "<h1" in page, "the library page has no heading"
    assert "Landmark papers" in page
    assert 'aria-label="Synerqo"' in page, "the brand lockup is missing from the masthead"
    assert "not investment advice" in page, "the standing notice has to survive every change"
    assert len(app.get("page_link")) == len(registry.papers()), "every paper needs a way in"


@pytest.mark.parametrize("paper", registry.papers(), ids=lambda p: p["slug"])
def test_each_paper_page_renders(paper: dict) -> None:
    app = AppTest.from_file(paper["page"], default_timeout=180).run()
    assert not app.exception, [e.value for e in app.exception]
    assert paper["title"] in [t.value for t in app.title]
