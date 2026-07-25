"""What happens at the edges of every control.

Written after an adversarial pass found that ten of the five thousand reachable slider
positions took the whole page down, disclaimer included. A page that renders nothing is
worse than a page that renders an empty chart with a reason, because the legal notice at
the bottom goes with it.

The rule these tests encode: a control can only ever produce an empty or a degenerate
result, never an exception.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from lab import data
from papers.jegadeesh_titman_1993 import figures

PAGE = "papers/jegadeesh_titman_1993/page.py"


def run(**state) -> AppTest:
    app = AppTest.from_file(PAGE, default_timeout=300)
    for key, value in state.items():
        app.session_state[key] = value
    return app.run()


def rendered(app: AppTest) -> dict:
    """What a reader actually gets, in the terms that matter."""
    text = " ".join(str(m.value) for m in app.markdown)
    return {
        "exceptions": [str(e.value) for e in app.exception],
        "charts": len(app.get("plotly_chart")),
        "disclaimer": "not investment advice" in text.lower(),
    }


# --------------------------------------------------------------- the page always survives


@pytest.mark.parametrize("horizon", list(data.HORIZON_LABELS))
def test_every_horizon_renders_over_its_own_coverage(horizon: str) -> None:
    out = rendered(run(horizon=horizon))
    assert not out["exceptions"]
    assert out["charts"] >= 3
    assert out["disclaimer"]


@pytest.mark.parametrize(
    "years",
    [
        (1927, 1930),  # before prior_60_13 has any data at all
        (1927, 1927),  # a single year
        (2026, 2026),  # the partial final year
        (1927, 2026),  # everything
        (1930, 1931),  # straddles the start of the long horizon
    ],
)
@pytest.mark.parametrize("horizon", list(data.HORIZON_LABELS))
def test_no_window_and_horizon_pair_can_break_the_page(horizon: str, years: tuple) -> None:
    """The pair that used to raise IndexError: prior_60_13 with a window ending in 1930."""
    out = rendered(run(horizon=horizon, fan_years=years))
    assert not out["exceptions"], f"{horizon} {years} raised {out['exceptions']}"
    assert out["disclaimer"], "the disclaimer must survive every control state"


def test_deselecting_the_horizon_control_falls_back() -> None:
    out = rendered(run(horizon=None))
    assert not out["exceptions"]
    assert out["charts"] >= 3


@pytest.mark.parametrize("start", [1927, 1970, 2015])
def test_surface_slider_extremes_render(start: int) -> None:
    out = rendered(run(surface_start=start))
    assert not out["exceptions"]
    assert out["charts"] >= 3


# --------------------------------------------------------------- the figures themselves


def test_fan_on_an_empty_slice_returns_a_figure_not_an_exception() -> None:
    empty = data.deciles("prior_60_13").loc["1927":"1930"]
    assert empty.empty, "fixture assumption: the long horizon has no data before 1931"
    fig = figures.fig_decile_fan(empty, horizon_label="test")
    assert fig.layout.annotations, "an empty window has to say so on the figure"


def test_fan_labels_do_not_round_a_multiple_into_a_lie() -> None:
    """1.5152x was being printed as 2x, a 32 percent overstatement."""
    wide = data.deciles("prior_12_2").loc["2026":"2026"]
    fig = figures.fig_decile_fan(wide, horizon_label="test")
    exact = figures.wealth_curves(wide).iloc[-1]
    labels = " ".join(a.text for a in fig.layout.annotations)
    for decile in (1, 10):
        assert f"{exact[decile]:,.2f}" in labels, f"decile {decile} label lost precision: {labels}"


def test_log_range_stays_finite_on_degenerate_input() -> None:
    flat = pd.DataFrame(
        [[-1.0] * 10, [0.05] * 10],
        columns=range(1, 11),
        index=pd.date_range("2000-01-31", periods=2, freq="ME"),
    )
    low, high = figures.log_range(figures.wealth_curves(flat))
    assert np.isfinite(low) and np.isfinite(high) and low < high

    nothing = pd.DataFrame(columns=range(1, 11), index=pd.DatetimeIndex([], name="date"))
    low, high = figures.log_range(figures.wealth_curves(nothing))
    assert np.isfinite(low) and np.isfinite(high) and low < high


def test_stat_tiles_accept_an_empty_row() -> None:
    from lab import layout

    app = AppTest.from_string(
        "from lab import layout\nlayout.stat_tiles([])", default_timeout=60
    ).run()
    assert not app.exception, [str(e.value) for e in app.exception]
    assert layout is not None


# --------------------------------------------------------------- the surface window


def test_a_ten_year_window_is_ten_years() -> None:
    """The displayed window was 132 months while the label said ten years."""
    dates, cube = data.size_prior_cube()
    months = figures.window_slice(dates, 1965, figures.WINDOW_YEARS)
    assert 118 <= (months.stop - months.start) <= 122, (
        f"a ten year window covered {months.stop - months.start} months"
    )


def test_bounds_cover_every_window_that_can_be_displayed() -> None:
    """Bounds and display have to use one window definition, not two that nearly agree."""
    dates, cube = data.size_prior_cube()
    low, high = figures.tilt_bounds(dates, cube)
    for start in figures.window_starts(dates):
        tilt = figures.tilt(figures.window_mean(dates, cube, start))
        assert low - 1e-9 <= np.nanmin(tilt) and np.nanmax(tilt) <= high + 1e-9, (
            f"window {start} escapes the fixed scale"
        )


def test_the_tilt_is_centred_by_construction() -> None:
    dates, cube = data.size_prior_cube()
    tilt = figures.tilt(figures.window_mean(dates, cube, 1995))
    assert abs(np.nanmean(tilt)) < 1e-9


def test_the_fixed_scale_actually_shows_the_signal() -> None:
    """The point of demeaning: a typical window must use a real share of the axis.

    On absolute returns the median window used 21 percent of a scale set by the 1930s, which
    is why every modern surface looked flat.
    """
    dates, cube = data.size_prior_cube()
    low, high = figures.tilt_bounds(dates, cube)
    used = []
    for start in figures.window_starts(dates):
        tilt = figures.tilt(figures.window_mean(dates, cube, start))
        used.append((np.nanmax(tilt) - np.nanmin(tilt)) / (high - low))
    assert np.median(used) > 0.35, f"median window uses only {np.median(used):.0%} of the axis"
