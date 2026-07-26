"""One precision for every number a reader sees, so no figure has to decide for itself.

Two decimals, everywhere: hovers, annotations, stat tiles, tables and axis ticks. The repo had
drifted into five conventions for the same quantity — a growth multiple printed at nought, one
or two decimals depending on its size, a monthly return at two decimals in a tile and three in
a table, a drawdown at nought — and the reader has no way to know which one is in front of
them.

Two decimals rather than "the precision that suits each figure", because the rule has to be
checkable without judgement. It also never loses what the original lesson was about: rounding
a growth multiple to the nearest integer once printed 1.5152 as `2x`, a 32 percent
overstatement. Two decimals cannot do that. The cost is a trailing `.00` on the occasional
large number, which is the cheaper mistake.

Scope is what the app draws. Published prose keeps its own writing — "34 percent" in a post is
a sentence, not a readout — and so do the build and render logs, which no reader sees.
"""

from __future__ import annotations

import numpy as np

#: The one knob. Everything below is derived from it.
DECIMALS = 2

#: Plotly format strings, for hovertemplate and tickformat.
NUMBER = f",.{DECIMALS}f"
SIGNED = f"+.{DECIMALS}f"
PERCENT = f".{DECIMALS}%"

#: No sign flag, no grouping flag. A 3D scene axis silently rejects `+.2f` in `hoverformat`
#: and falls back to the raw double, which is how a tooltip came to read
#: -0.47932119658119654. Plotly draws the minus itself, so nothing is lost.
PLAIN = f".{DECIMALS}f"


def multiple(value: float) -> str:
    """A growth multiple, as the reader will check it: `1.52x`, `16,908.30x`."""
    if not np.isfinite(value):
        return "n/a"
    return f"{value:{NUMBER}}x"
