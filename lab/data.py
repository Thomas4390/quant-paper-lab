"""Read the derived series. This layer never touches the network.

Everything the app displays was computed offline by a paper's build_data.py and committed as
parquet. That is deliberate: a post can send a few hundred readers at once to a 1 GB
container, and a cold start that downloads and recomputes would fall over. Keep it that way.
tests/test_no_runtime_fetch.py fails if this module ever grows a socket.

The size by prior grid is exposed as a numpy cube rather than a tidy frame. Windowing then
costs a slice and a nanmean instead of a pivot per call, which matters because the surface is
rebuilt on every session and once more per animation frame.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"

#: Formation horizons available in deciles.parquet, with reader-facing labels.
HORIZON_LABELS = {
    "prior_1_0": "Prior 1 month",
    "prior_12_2": "Prior 2 to 12 months",
    "prior_60_13": "Prior 13 to 60 months",
}

#: Portfolio weightings. Jegadeesh and Titman used equal weighting, so it is the one that
#: compares with their published table. Value weighting is the modern convention.
WEIGHTINGS = {
    "vw": "Value weighted",
    "ew": "Equal weighted",
}


@st.cache_data(show_spinner=False)
def deciles(horizon: str, weighting: str = "vw") -> pd.DataFrame:
    """Monthly returns by prior-return decile. Index is month end, columns are 1 to 10."""
    if horizon not in HORIZON_LABELS:
        raise KeyError(f"unknown horizon {horizon!r}, expected one of {list(HORIZON_LABELS)}")
    if weighting not in WEIGHTINGS:
        raise KeyError(f"unknown weighting {weighting!r}, expected one of {list(WEIGHTINGS)}")
    tidy = pd.read_parquet(DATA / "deciles.parquet")
    picked = tidy[(tidy.horizon == horizon) & (tidy.weighting == weighting)]
    return picked.pivot(index="date", columns="decile", values="ret").sort_index()


@st.cache_data(show_spinner=False)
def size_prior() -> pd.DataFrame:
    """Monthly returns for the 5 by 5 size and prior-return portfolios, tidy."""
    return pd.read_parquet(DATA / "size_prior_25.parquet")


@st.cache_data(show_spinner=False)
def size_prior_cube() -> tuple[pd.DatetimeIndex, np.ndarray]:
    """The same grid as (dates, cube) where cube has shape (months, size, prior).

    Built by explicit indexing rather than by reshaping, so it does not depend on the row
    order of the parquet.
    """
    tidy = size_prior()
    dates = pd.DatetimeIndex(sorted(tidy.date.unique()))
    position = {stamp: index for index, stamp in enumerate(dates)}
    cube = np.full((len(dates), 5, 5), np.nan)
    cube[
        tidy.date.map(position).to_numpy(),
        tidy.size_q.to_numpy() - 1,
        tidy.prior_q.to_numpy() - 1,
    ] = tidy.ret.to_numpy()
    return dates, cube


@st.cache_data(show_spinner=False)
def factors() -> pd.DataFrame:
    """Market, size, value, risk-free and momentum factors. Index is month end."""
    return pd.read_parquet(DATA / "factors.parquet").set_index("date").sort_index()


def coverage(horizon: str = "prior_12_2") -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last month available **for this horizon**.

    The three horizons do not start together: sorting on the prior 13 to 60 months needs five
    years of history before it can produce anything, so it begins in 1931 while the one month
    sort begins in 1926. Bounding a control with another horizon's range is what produced an
    empty slice, and an empty slice used to take the whole page down.
    """
    index = deciles(horizon).index
    return index[0], index[-1]


def common_coverage() -> tuple[pd.Timestamp, pd.Timestamp]:
    """The window where all three horizons exist, which is the only fair comparison."""
    spans = [coverage(horizon) for horizon in HORIZON_LABELS]
    return max(start for start, _ in spans), min(end for _, end in spans)
