"""Hammer the running app and report how it died, if it died.

A native crash leaves no Python traceback and no failing test: the server is gone, the browser
shows a dead socket, and the shell prints a signal. Nothing in the suite can see that, because
the suite runs in one process and the crash needs a real server, a real websocket and a real
script rerun per click. This drives exactly that.

    uv run --group dev python tools/soak.py
    uv run --group dev python tools/soak.py --rounds 8 --pool mimalloc

`--pool` forces ARROW_DEFAULT_MEMORY_POOL for the server process, which is how the fix in
lab/arrow.py was measured: mimalloc segfaulted 3 runs out of 3, `system` and `jemalloc` 0 out
of 3. Use it to re-measure rather than to trust this comment.

Exits 1 on a segfault, 0 otherwise. Not part of the test suite: it needs a browser.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from shoot import settle

ROOT = Path(__file__).resolve().parents[1]
# Every horizon is one script rerun, and the expander holds the page's only dataframe, which
# is the call that serialises through Arrow.
HORIZONS = ("1 month", "2 to 12 months", "13 to 60 months")
EXPANDER = "How this reproduction differs"


def drive(page, rounds: int, alive) -> None:
    for round_number in range(rounds):
        try:
            page.get_by_text(EXPANDER, exact=False).first.click(timeout=8000)
        except Exception:
            # Already open, or gone because the server just died. Neither is the measurement,
            # and the second one is answered by the exit code a few lines down.
            pass
        page.wait_for_timeout(400)
        for label in HORIZONS:
            try:
                page.get_by_text(label, exact=True).first.click(timeout=8000)
                page.wait_for_timeout(900)
            except Exception:
                print(f"  round {round_number + 1}: {label} unreachable", flush=True)
        if not alive():
            return
        print(f"  round {round_number + 1}/{rounds} alive", flush=True)


def soak(rounds: int, port: int, pool: str | None) -> int:
    env = dict(os.environ)
    env["PYTHONFAULTHANDLER"] = "1"
    env.pop("ARROW_DEFAULT_MEMORY_POOL", None)
    if pool:
        env["ARROW_DEFAULT_MEMORY_POOL"] = pool

    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
         f"--server.port={port}", "--server.headless=true"],
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        time.sleep(6)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                page.goto(f"http://localhost:{port}/momentum-1993", wait_until="domcontentloaded")
                settle(page, charts=True)
                print("loaded", flush=True)
                drive(page, rounds, lambda: server.poll() is None)
            except Exception as exc:
                # The browser giving up is a symptom. The server's exit code is the finding,
                # and it is read below either way.
                print(f"browser gave up: {type(exc).__name__}", flush=True)
            browser.close()
    finally:
        code = server.poll()
        if code is None:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
            code = server.returncode
        output = server.stdout.read() if server.stdout else ""

    crashed = code is not None and code < 0 and -code == signal.SIGSEGV
    print(f"server exit code {code}: {'SIGSEGV' if crashed else 'no segfault'}")
    if crashed:
        print(output)
    return 1 if crashed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--port", type=int, default=8512)
    parser.add_argument("--pool", help="force ARROW_DEFAULT_MEMORY_POOL on the server")
    args = parser.parse_args()
    sys.exit(soak(args.rounds, args.port, args.pool))
