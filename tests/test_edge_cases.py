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


# --------------------------------------------------------------- the fan, playing


def animated(window: str, stop: str | None = None):
    wide = data.deciles("prior_12_2").loc[window:stop]
    return wide, figures.fig_decile_fan_animation(
        wide,
        horizon_label="test",
        y_log_range=figures.shared_log_range([wide]),
        x_range=[wide.index[0], wide.index[-1]] if not wide.empty else None,
        published_year=1993,
    )


def test_an_empty_window_animates_into_a_figure_that_says_so() -> None:
    empty = data.deciles("prior_60_13").loc["1927":"1930"]
    fig = figures.fig_decile_fan_animation(empty, horizon_label="test")
    assert not fig.frames, "there is nothing to reveal"
    assert fig.layout.annotations, "an empty window has to say so on the figure"


def test_a_window_too_short_to_reveal_is_just_the_figure() -> None:
    _, fig = animated("1965", "1965")
    assert len(fig.frames) <= 1
    assert len(fig.data) == 10, "the curves are still drawn"


def test_the_figure_opens_complete_so_not_pressing_play_costs_nothing() -> None:
    """The whole justification for animating a curve the reader can already see whole."""
    wide, fig = animated("1965", "1989")
    static = figures.fig_decile_fan(wide, horizon_label="test", show_title=False)
    assert len(fig.data[0].y) == len(wide), "the base figure is the full curve, not the first frame"
    assert [a.text for a in fig.layout.annotations] == [a.text for a in static.layout.annotations]
    assert fig.layout.sliders[0].active == len(fig.frames) - 1, "the handle matches what is drawn"


def test_the_last_frame_lands_on_the_static_figure() -> None:
    wide, fig = animated("1965", "1989")
    assert len(fig.frames[-1].data[0].y) == len(wide)
    assert [a["text"] for a in fig.frames[-1].layout.annotations] == [
        a.text for a in fig.layout.annotations
    ]


def test_no_frame_rescales_the_axis_under_the_reader() -> None:
    """A frame may move the marks and nothing else. An axis in there would rescale mid flight."""
    for frame in animated("1965", "1989")[1].frames:
        carried = set(frame.layout.to_plotly_json())
        assert carried <= {"annotations", "shapes"}, f"a frame also carries {carried}"


@pytest.mark.parametrize("window,stop", [("1927", "2026"), ("1965", "2026"), ("1965", "1989")])
def test_frames_stay_inside_the_payload_budget(window: str, stop: str) -> None:
    """The reader picks the window, so the frame count has to answer to it."""
    _, fig = animated(window, stop)
    shipped = sum(len(frame.data[0].y) * 10 for frame in fig.frames)
    assert shipped <= figures.FRAME_BUDGET_VALUES * 1.2, (
        f"{window} to {stop} ships {shipped:,} values against a budget of "
        f"{figures.FRAME_BUDGET_VALUES:,}"
    )


# --------------------------------------------------------------- the publication mark


def test_the_figure_the_page_builds_can_still_be_exported() -> None:
    """A Timestamp in the axis range survives Plotly and dies in the static export.

    The page passes index entries straight through, so the figure it draws could not be
    written to a PNG, which is the one way a chart is supposed to be judged.
    """
    _, fig = animated("1965", "1989")
    assert all(isinstance(bound, str) for bound in fig.layout.xaxis.range)


def test_the_mark_is_absent_when_the_window_does_not_reach_publication() -> None:
    """The default window stops in 1989. A mark outside the drawn range would be a lie."""
    _, before = animated("1965", "1989")
    _, after = animated("1994", "2026")
    assert not before.layout.shapes
    assert not after.layout.shapes


def test_the_mark_appears_once_the_window_contains_publication() -> None:
    _, fig = animated("1965", "2000")
    assert len(fig.layout.shapes) == 1
    assert any("published" in a.text for a in fig.layout.annotations)


def test_the_mark_waits_for_the_reveal_to_reach_it() -> None:
    """The beat the video was built around: it lands as the curve passes 1993, not before."""
    _, fig = animated("1965", "2000")
    marked = [bool(frame.layout.shapes) for frame in fig.frames]
    assert not marked[0], "the first stop is decades short of publication"
    assert marked[-1], "the last stop is past it"
    assert marked == sorted(marked), "the mark can only ever arrive, never leave"


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


def test_the_surface_tooltip_is_formatted_by_the_axis_not_by_the_template() -> None:
    """A 3D surface resolves %{z} through its scene axis, and drops the template's spec.

    Left to `%{z:+.2f}` the tooltip printed -0.47932119658119654. Both halves of the fix are
    load bearing and neither is visible in a screenshot: the axis has to carry hoverformat,
    and that format cannot start with a sign flag, which a scene axis silently rejects by
    falling back to the raw double.
    """
    dates, cube = data.size_prior_cube()
    fig = figures.fig_size_prior_animation(dates, cube, bounds=figures.tilt_bounds(dates, cube))

    hoverformat = fig.layout.scene.zaxis.hoverformat
    assert hoverformat, "without hoverformat the tooltip prints a raw double"
    assert not hoverformat.startswith("+"), "a scene axis rejects the sign flag and gives up"

    template = fig.data[0].hovertemplate
    assert "%{z:" not in template, "a format spec on %{z} is dropped rather than applied"
    assert "Q%{" not in template, "%{x} already carries the axis ticktext, so a Q prefix doubles it"


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
