"""Does the reproduction still reproduce?

These are the tests that matter. If one of them goes red, the fix is in the pipeline or in
the source data, not in the threshold. Bounds are wide on purpose: they catch a broken sort,
a sign error or a units mistake, not a third decimal place. Ken French revises history, so
exact equality would be a false alarm every month.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lab import data


@pytest.fixture(scope="module")
def canonical() -> pd.DataFrame:
    return data.deciles("prior_12_2")


def spread(wide: pd.DataFrame, start: str | None = None, end: str | None = None) -> pd.Series:
    series = (wide[10] - wide[1]).dropna()
    return series.loc[start:end] if start else series


def test_coverage_is_a_full_history(canonical: pd.DataFrame) -> None:
    assert len(canonical) > 1100, "expected nearly a century of monthly observations"
    assert canonical.index.is_monotonic_increasing
    assert list(canonical.columns) == list(range(1, 11))


def test_momentum_pays_over_the_papers_own_sample(canonical: pd.DataFrame) -> None:
    """Jegadeesh and Titman report about 1.3 percent a month on 1965 to 1989.

    Our construction is monthly rebalanced deciles rather than their overlapping portfolios,
    so we check the neighbourhood, not the number.
    """
    monthly = spread(canonical, "1965", "1989").mean() * 100
    assert 1.0 < monthly < 2.5, f"paper sample spread came out at {monthly:.2f} percent a month"


def test_the_sign_flips_with_the_formation_horizon() -> None:
    """One month reverses, one year continues, five years reverse. Full sample."""
    short_term = spread(data.deciles("prior_1_0")).mean()
    medium_term = spread(data.deciles("prior_12_2")).mean()
    long_term = spread(data.deciles("prior_60_13")).mean()

    assert short_term < 0, "prior one month should reverse"
    assert medium_term > 0, "prior 2 to 12 months should continue"
    assert long_term < 0, "prior 13 to 60 months should reverse"
    assert medium_term > abs(short_term), "momentum should dominate short-term reversal in size"


def test_momentum_crashed_in_april_2009() -> None:
    mom = data.factors()["mom"].dropna()
    worst_recent = mom.loc["1950":].idxmin()
    assert worst_recent == pd.Timestamp("2009-04-30"), f"worst post-1950 month is {worst_recent}"
    assert mom.loc[worst_recent] < -0.30, "April 2009 should be worse than minus 30 percent"


def test_the_premium_shrank_after_2009(canonical: pd.DataFrame) -> None:
    before = spread(canonical, "1990", "2008")
    after = spread(canonical, "2009", None)
    assert after.mean() < before.mean() / 3, "post-2009 spread should be a fraction of the prior era"
    sharpe = after.mean() / after.std() * np.sqrt(12)
    assert -0.5 < sharpe < 0.5, f"post-2009 Sharpe came out at {sharpe:.2f}"


def test_size_and_prior_grid_is_complete() -> None:
    tidy = data.size_prior()
    assert set(tidy.size_q) == set(range(1, 6))
    assert set(tidy.prior_q) == set(range(1, 6))
    latest = tidy[tidy.date == tidy.date.max()]
    assert len(latest) == 25, "the most recent month should have all 25 portfolios"
