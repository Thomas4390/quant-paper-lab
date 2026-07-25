"""Does the reproduction still reproduce?

Two kinds of test live here and they have different rules.

**Invariants** describe the pipeline: shapes, units, orderings, the positional mapping of the
25 portfolios. They must never be relaxed. If one goes red, something is genuinely wrong.

**Golden numbers** pin the values this repo publishes, with a tolerance wide enough to absorb
a Ken French revision and narrow enough to catch picking the wrong table. The equal weighted
table sits in the same file as the value weighted one and differs by 0.30 points a month, so
a loose bound would let that swap through unnoticed. When French revises history, regenerate
these deliberately and say so in the commit, do not widen them quietly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lab import data
from papers.jegadeesh_titman_1993 import figures

#: Published in the paper, table I, for the 12 month formation and 3 month holding strategy.
PUBLISHED_MONTHLY_PERCENT = 1.31

#: Values this repo states publicly, in percent a month. Tolerance is absolute.
GOLDEN = {
    ("prior_12_2", "vw", "1965", "1989"): (1.630, 0.06),
    ("prior_12_2", "ew", "1965", "1989"): (1.332, 0.06),
    ("prior_12_2", "vw", "2009", None): (0.160, 0.10),
    ("prior_12_2", "vw", "1990", "2008"): (1.562, 0.10),
    ("prior_1_0", "vw", "1931", None): (-0.849, 0.06),
    ("prior_60_13", "vw", "1931", None): (-0.422, 0.06),
}


def spread(horizon: str, weighting: str = "vw", start=None, end=None) -> pd.Series:
    wide = data.deciles(horizon, weighting)
    return (wide[10] - wide[1]).dropna().loc[start:end]


# ------------------------------------------------------------------------- invariants


@pytest.mark.parametrize("horizon", list(data.HORIZON_LABELS))
@pytest.mark.parametrize("weighting", list(data.WEIGHTINGS))
def test_decile_frames_are_well_formed(horizon: str, weighting: str) -> None:
    wide = data.deciles(horizon, weighting)
    assert len(wide) > 1100, "expected nearly a century of monthly observations"
    assert wide.index.is_monotonic_increasing
    assert list(wide.columns) == list(range(1, 11))
    assert wide.abs().max().max() < 1.5, "returns must be decimals, not percent"
    assert not wide.isin([-0.9999, -9.99, -99.99]).any().any(), "sentinel leaked into the data"


def test_the_25_portfolios_are_not_transposed() -> None:
    """Volatility falls with size and is U shaped across prior return.

    The positional size-major mapping is the heaviest assumption in build_data.py and the
    column labels are too irregular to key on, so this is the check that would catch a
    transposition. Without it, swapping the two axes passes every other test in the suite.
    """
    tidy = data.size_prior()
    by_size = tidy.groupby("size_q").ret.std()
    by_prior = tidy.groupby("prior_q").ret.std()
    assert by_size.is_monotonic_decreasing, f"volatility not decreasing in size: {by_size.round(3).to_dict()}"
    assert not by_prior.is_monotonic_decreasing, "prior-return volatility should be U shaped, not monotone"


def test_size_and_prior_grid_is_complete() -> None:
    tidy = data.size_prior()
    assert set(tidy.size_q) == set(range(1, 6))
    assert set(tidy.prior_q) == set(range(1, 6))
    latest = tidy[tidy.date == tidy.date.max()]
    assert len(latest) == 25, "the most recent month should have all 25 portfolios"


def test_the_horizons_do_not_all_start_together() -> None:
    """A fact the page has to account for, so it is pinned rather than rediscovered."""
    starts = {h: data.coverage(h)[0] for h in data.HORIZON_LABELS}
    assert starts["prior_60_13"] > starts["prior_12_2"] > starts["prior_1_0"]


# ---------------------------------------------------------------------- golden numbers


@pytest.mark.parametrize("key", list(GOLDEN))
def test_published_numbers_hold(key: tuple) -> None:
    horizon, weighting, start, end = key
    expected, tolerance = GOLDEN[key]
    actual = spread(horizon, weighting, start, end).mean() * 100
    assert abs(actual - expected) < tolerance, (
        f"{key} came out at {actual:+.3f}, expected {expected:+.3f}. "
        "If Ken French revised history, regenerate GOLDEN deliberately."
    )


def test_equal_weighted_reproduces_the_published_result() -> None:
    """The paper used equal weighted portfolios. That is what makes the numbers comparable."""
    equal = spread("prior_12_2", "ew", "1965", "1989").mean() * 100
    value = spread("prior_12_2", "vw", "1965", "1989").mean() * 100
    assert abs(equal - PUBLISHED_MONTHLY_PERCENT) < 0.10, (
        f"equal weighted gives {equal:.3f} against {PUBLISHED_MONTHLY_PERCENT} published"
    )
    assert value > equal, "value weighting should read higher here, and the gap is the point"


def test_the_sign_flips_with_the_formation_horizon() -> None:
    """Compared on the common sample, because the three horizons do not start together."""
    common = "1931"
    short = spread("prior_1_0", start=common).mean()
    medium = spread("prior_12_2", start=common).mean()
    long = spread("prior_60_13", start=common).mean()
    assert short < 0 < medium
    assert long < 0


def test_momentum_crashed_in_april_2009() -> None:
    mom = data.factors()["mom"].dropna()
    worst_recent = mom.loc["1950":].idxmin()
    assert worst_recent == pd.Timestamp("2009-04-30"), f"worst post-1950 month is {worst_recent}"
    assert mom.loc[worst_recent] < -0.30
    assert mom.idxmin() == pd.Timestamp("1932-08-31"), "the all time worst month is 1932, not 2009"


def test_the_recent_era_is_weaker_but_not_conclusively(caplog) -> None:
    """The honest version of "it stopped working".

    The point estimate collapses, the difference does not clear significance, and two months
    drive most of it. All three have to stay true for the copy to stay true.
    """
    before = spread("prior_12_2", start="1990", end="2008")
    after = spread("prior_12_2", start="2009")
    assert after.mean() < before.mean() / 3

    standard_error = np.sqrt(before.var() / len(before) + after.var() / len(after))
    t_statistic = (before.mean() - after.mean()) / standard_error
    assert abs(t_statistic) < 1.96, f"the era difference now clears significance at t={t_statistic:.2f}"

    without_unwind = after.drop([pd.Timestamp("2009-03-31"), pd.Timestamp("2009-04-30")])
    assert without_unwind.mean() > after.mean() * 2, "two months should still dominate the average"


# ------------------------------------------------------------------- what the page draws


def test_crash_annotations_point_at_the_months_they_name() -> None:
    """The two trough annotations used to land on the same point, one of them mislabelled."""
    fig = figures.fig_momentum_crash(data.factors()["mom"])
    marks = [(pd.Timestamp(a.x), a.text) for a in fig.layout.annotations]
    assert len({stamp for stamp, _ in marks}) == len(marks), "annotations overlap"

    dated = [(stamp, text) for stamp, text in marks if f"{stamp:%B %Y}" in text]
    assert len(dated) >= 2, f"expected the troughs to name their own month, got {marks}"

    deepest, deepest_text = min(dated, key=lambda mark: mark[0])
    assert deepest.year == 1939, f"the deepest drawdown is 1939, annotation sits at {deepest:%Y-%m}"
    assert "78" in deepest_text or "79" in deepest_text, deepest_text


def test_era_stats_report_their_sample_size() -> None:
    """A Sharpe ratio without n and t is a decoration."""
    tiles = figures.era_stats(data.deciles("prior_12_2"))
    assert tiles
    for _label, value, note in tiles:
        assert "%" in value
        assert "n " in note and "t " in note, f"tile note is missing n or t: {note!r}"
