"""Run the suite on the allocator the app runs on.

Tests render the page through AppTest, which serialises a dataframe through Arrow exactly as
the server does. Leaving them on pyarrow's default would mean testing a configuration that is
never deployed, and occasionally taking the whole suite down with a signal.

pytest imports this before any test module, and before anything imports pyarrow, which is the
window lab/arrow.py needs.
"""

from __future__ import annotations

from lab import arrow

arrow.use_stable_memory_pool()
