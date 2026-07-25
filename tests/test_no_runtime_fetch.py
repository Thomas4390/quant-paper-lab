"""The app must not touch the network, and the render path must not need the app.

Two invariants that are easy to break by accident and expensive to discover in production.

First, a post can send hundreds of readers at once into a 1 GB container. Anything that
downloads or recomputes on request will fall over exactly when it matters. So the data layer
reads local parquet, and this test proves it by taking sockets away.

Second, figures.py is shared by the Streamlit page and the video renderer. If the render
path picks up a streamlit import, the video can no longer be built in a plain script.
"""

from __future__ import annotations

import socket
import subprocess
import sys

import pytest


@pytest.fixture
def no_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args, **kwargs):
        raise AssertionError("the data layer opened a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def test_loaders_work_without_a_network(no_sockets: None) -> None:
    from lab import data

    data.deciles.clear()
    data.size_prior.clear()
    data.factors.clear()

    assert not data.deciles("prior_12_2").empty
    assert not data.size_prior().empty
    assert not data.factors().empty


def test_render_path_does_not_import_streamlit() -> None:
    probe = (
        "import sys;"
        "from lab import render, theme;"
        "from papers.jegadeesh_titman_1993 import figures;"
        "assert 'streamlit' not in sys.modules, sorted(m for m in sys.modules if 'streamlit' in m);"
        "print('clean')"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-600:]
    assert "clean" in result.stdout
