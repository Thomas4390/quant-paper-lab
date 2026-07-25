"""Keep Arrow off the allocator that takes this server down.

pyarrow 25 defaults to the mimalloc pool. Streamlit serialises every dataframe to Arrow IPC
bytes on the script runner thread, and on that pool the process dies with SIGSEGV inside
`convert_arrow_table_to_arrow_bytes`, no Python traceback, usually on the very first page
load. The server is simply gone, and every connected session with it. Measured against a
live server driven by a browser: 3 segfaults out of 3 on mimalloc, 0 out of 3 on `system`,
0 out of 3 on `jemalloc`.

**The environment variable is the only lever that works, and it has to be set before pyarrow
loads.** `pyarrow.set_memory_pool()` was tried first and is a trap: it does move
`default_memory_pool()`, and the app still segfaults 3 times out of 3, because the IPC writer
allocates through Arrow's C++ default, which is fixed when the shared library initialises.
That initialisation is late enough to catch only because Streamlit imports pyarrow lazily,
inside the functions that need it, so an entry point still runs first.

`system` rather than `jemalloc`: both tested clean, and `system` is the one backend Arrow
always ships, on every platform.
"""

from __future__ import annotations

import os
import sys

VARIABLE = "ARROW_DEFAULT_MEMORY_POOL"
POOL = "system"
#: What pyarrow picks when left alone here, and the whole reason this module exists.
BROKEN_POOL = "mimalloc"


def use_stable_memory_pool() -> str | None:
    """Point Arrow at a pool that does not crash, and say which one it will use.

    Returns None if pyarrow is already imported, because by then the choice is made and this
    call cannot honour its own contract. Callers get the truth rather than a silent no-op.
    """
    if "pyarrow" in sys.modules:
        return None
    os.environ.setdefault(VARIABLE, POOL)
    return os.environ[VARIABLE]
