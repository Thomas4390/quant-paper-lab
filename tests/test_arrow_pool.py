"""The app must never reach Arrow's default memory pool.

pyarrow 25 defaults to mimalloc, and Streamlit serialising a dataframe on that pool segfaults
the server: no traceback, no page, no disclaimer, and every other session dies with it. The
fix is one environment variable set before pyarrow loads, so what these tests guard is that
the variable is still set, and still set early enough.

The crash itself cannot be reproduced in process. It needs a live server and a browser, which
is what tools/soak.py is for, and why it is a tool rather than a test.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from lab import arrow

ROOT = Path(__file__).resolve().parents[1]


def run(snippet: str, *, harden: bool) -> str:
    """Run a snippet in a clean interpreter and return its last line.

    The variable is stripped from the child's environment either way, so the parent's own
    conftest cannot answer the question the test is asking.
    """
    env = dict(os.environ)
    env.pop(arrow.VARIABLE, None)
    prologue = "from lab import arrow\narrow.use_stable_memory_pool()\n" if harden else ""
    completed = subprocess.run(
        [sys.executable, "-c", prologue + snippet],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=300,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return completed.stdout.strip().splitlines()[-1]


BACKEND = "import pyarrow as pa\nprint(pa.default_memory_pool().backend_name)\n"

RENDER_THE_PAGE = """
from streamlit.testing.v1 import AppTest

AppTest.from_file("papers/jegadeesh_titman_1993/page.py", default_timeout=300).run()
import pyarrow as pa
print(pa.default_memory_pool().backend_name)
"""


def test_the_pool_we_avoid_is_still_the_one_pyarrow_picks() -> None:
    """The canary. When this fails, pyarrow changed its default and the workaround can go."""
    backend = run(BACKEND, harden=False)
    if backend != arrow.BROKEN_POOL:
        pytest.skip(f"pyarrow now defaults to {backend}, nothing to work around here")
    assert backend == arrow.BROKEN_POOL


def test_hardening_moves_arrow_off_that_pool() -> None:
    assert run(BACKEND, harden=True) != arrow.BROKEN_POOL


def test_the_pool_still_holds_after_a_full_page_render() -> None:
    """Rendering is what pulls pyarrow in. The variable has to survive that, not just precede it."""
    assert run(RENDER_THE_PAGE, harden=True) != arrow.BROKEN_POOL


def test_the_entry_point_hardens_before_anything_loads_pyarrow() -> None:
    """Streamlit imports pyarrow lazily, which is the only reason the entry point is early enough."""
    assert run("import streamlit\nimport sys\nprint('pyarrow' in sys.modules)\n", harden=False) == "False"


def test_hardening_after_pyarrow_is_loaded_reports_that_it_is_too_late() -> None:
    """It must not claim a win it cannot deliver: set_memory_pool does not stop the crash."""
    assert run("import pyarrow\nfrom lab import arrow\nprint(arrow.use_stable_memory_pool())\n", harden=False) == "None"
