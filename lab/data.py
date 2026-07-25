"""Read the derived series. This layer never touches the network.

Everything the app displays was computed offline by a paper's build_data.py and committed
as parquet. That is deliberate: a post can send a few hundred readers at once to a 1 GB
container, and a cold start that downloads and recomputes would fall over. Keep it that
way. tests/test_no_runtime_fetch.py fails if this module ever grows a socket.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"

#: Formation horizons available in deciles.parquet, with reader-facing labels.
HORIZON_LABELS = {
    "prior_1_0": "Prior 1 month",
    "prior_12_2": "Prior 2 to 12 months",
    "prior_60_13": "Prior 13 to 60 months",
}


@st.cache_data(show_spinner=False)
def deciles(horizon: str) -> pd.DataFrame:
    """Monthly returns by prior-return decile. Index is month end, columns are 1 to 10."""
    if horizon not in HORIZON_LABELS:
        raise KeyError(f"unknown horizon {horizon!r}, expected one of {list(HORIZON_LABELS)}")
    tidy = pd.read_parquet(DATA / "deciles.parquet")
    wide = tidy[tidy.horizon == horizon].pivot(index="date", columns="decile", values="ret")
    return wide.sort_index()


@st.cache_data(show_spinner=False)
def size_prior() -> pd.DataFrame:
    """Monthly returns for the 5 by 5 size and prior-return portfolios, tidy."""
    return pd.read_parquet(DATA / "size_prior_25.parquet")


@st.cache_data(show_spinner=False)
def factors() -> pd.DataFrame:
    """Market, size, value, risk-free and momentum factors. Index is month end."""
    return pd.read_parquet(DATA / "factors.parquet").set_index("date").sort_index()


def coverage(horizon: str = "prior_12_2") -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last month available, used to bound the date controls."""
    idx = deciles(horizon).index
    return idx[0], idx[-1]
