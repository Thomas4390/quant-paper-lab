"""Figures and summary numbers for the momentum reproduction.

This module is the single source of visual truth. The Streamlit page imports it, and so does
animate.py when it renders the video. Nothing here knows about either one, and nothing here
reads a file: callers pass data in. That includes the narrative marks: the line at
publication used to be drawn by animate.py, which is how the video carried it for a year while
the app never did. Numbers are formatted through lab/format.py, for the same reason.

Encoding choices, so they are not re-litigated per figure:
  Decile rank is ordered, not signed, so the ten lines take a single hue ramp with the bottom
  decile in amber. Only the two extremes get a label, because the reader is asked to see a
  fan, not to identify decile six.
  The surface shows the tilt, meaning each window's grid minus that window's own average.
  Absolute returns need a fixed scale set by the 1930s, on which a typical window occupies a
  fifth of the axis and every modern surface looks flat. The tilt is also the actual question:
  where does sorting on past returns pay, relative to holding everything in that window.
  Drawdown is one measure, so it gets one axis and no legend.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from lab import format as fmt
from lab import theme

WINDOW_YEARS = 10
PRIOR_TICKS = ["Q1", "Q2", "Q3", "Q4", "Q5"]
SIZE_TICKS = ["Q1", "Q2", "Q3", "Q4", "Q5"]


def _rank_colors() -> list[str]:
    """Ordered colors for the ten deciles, bottom to top.

    Decile rank is ordered, not signed, so the middle of the scale does not mean zero and a
    diverging ramp is the wrong instrument. Sampling one put four of the ten lines under 3:1
    against the background and gave deciles 5 and 6 the same lightness. A single hue ramp
    reads as an ordered fan, and the bottom decile keeps the amber accent so the polarity of
    the extremes stays obvious.
    """
    return [theme.NEGATIVE, *theme.RANK_RAMP]


def _empty(message: str, height: int) -> go.Figure:
    """A figure that says why it is empty.

    An exception here would not blank the chart, it would blank the page, and the standing
    disclaimer at the bottom of that page goes with it.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"family": theme.FONT_BODY, "size": 14, "color": theme.FG_SUBTLE},
    )
    fig.update_layout(
        height=height,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 24, "r": 24, "t": 24, "b": 24},
    )
    return fig


# --------------------------------------------------------------------------- deciles


def wealth_curves(wide: pd.DataFrame) -> pd.DataFrame:
    """Value of one dollar per decile. Compounded once, so a reveal can slice it later."""
    return (1.0 + wide).cumprod()


def log_range(wealth: pd.DataFrame, *, pad: float = 0.12) -> list[float]:
    """Fixed y bounds in log10 units, so an animated reveal never rescales mid flight.

    Both ends are floored away from zero and the span is never allowed to collapse, because a
    log axis given a nan or an infinity is silently replaced by autorange, which is the exact
    opposite of what a fixed range is for.
    """
    values = wealth.to_numpy(dtype="float64").ravel() if len(wealth) else np.array([])
    values = values[np.isfinite(values) & (values > 0)]
    if values.size == 0:
        return [-1.0, 1.0]
    low, high = float(np.log10(values.min())), float(np.log10(values.max()))
    if high - low < 0.5:  # a single point, or a window too short to have a span
        middle = (high + low) / 2
        low, high = middle - 0.25, middle + 0.25
    reach = (high - low) * pad
    return [low - reach, high + reach]


def shared_log_range(windows) -> list[float]:
    """One y scale across several windows, so switching between them compares like with like.

    Without this, each horizon gets its own autoscaled axis and three fans spanning 2.0, 3.5
    and 2.1 decades all render at the same apparent height. That is the same mistake the
    surface avoids with fixed bounds.
    """
    ranges = [log_range(wealth_curves(w)) for w in windows if not w.empty]
    if not ranges:
        return [-1.0, 1.0]
    return [min(r[0] for r in ranges), max(r[1] for r in ranges)]


def _as_dates(bounds: list | None) -> list | None:
    """An axis range as strings, so the figure survives a static export."""
    if bounds is None:
        return None
    return [b.isoformat() if hasattr(b, "isoformat") else b for b in bounds]


def _end_labels(shown: pd.DataFrame, colors: list[str], size: int) -> list[dict]:
    """The two labels that ride the end of the drawn lines.

    Returned as plain dicts instead of being added to a figure, because an animated reveal has
    to rebuild them per frame: they are layout, and they travel with the last drawn point.
    """
    last = shown.index[-1]
    labels = []
    for decile, text in ((10, "Top decile"), (1, "Bottom decile")):
        value = float(shown[decile].iloc[-1])
        labels.append(
            {
                "x": last.isoformat(),
                "y": float(np.log10(max(value, 1e-6))),
                "text": f"  {text} · {fmt.multiple(value)}",
                "showarrow": False,
                "xanchor": "left",
                "font": {"family": theme.FONT_BODY, "size": size, "color": colors[decile - 1]},
            }
        )
    return labels


def publication_mark(year: int, size: int) -> tuple[dict, dict]:
    """The dotted line where the paper lands, and the note that names it.

    It lives here rather than in the caller that first wanted it. The video drew this mark for
    a year while the app had never had it, which is exactly what a module calling itself the
    single source of visual truth is supposed to prevent.

    Milliseconds since the epoch, not a date string: that is the coordinate a shape takes on a
    date axis, and it is what the rendered video has been using.
    """
    stamp = pd.Timestamp(f"{year}-01-01").timestamp() * 1000
    line = {
        "type": "line",
        "x0": stamp,
        "x1": stamp,
        "y0": 0,
        "y1": 1,
        "yref": "y domain",
        "line": {"color": theme.LINE_STRONG, "width": 1, "dash": "dot"},
    }
    note = {
        "x": stamp,
        "y": 1.0,
        "yref": "y domain",
        "text": "the paper is published",
        "showarrow": False,
        "xanchor": "left",
        "yanchor": "bottom",
        "font": {"family": theme.FONT_BODY, "size": size, "color": theme.FG_MUTED},
    }
    return line, note


def _marks(shown: pd.DataFrame, published_year: int | None, size: int) -> tuple[list, list]:
    """Shapes and annotations for one drawn state: the end labels, plus the mark if it is due.

    The mark is withheld on two counts. Outside the drawn range it would be a lie about the
    scale, and ahead of the reveal it would give away the beat the animation exists for.
    """
    shapes: list[dict] = []
    annotations = _end_labels(shown, _rank_colors(), size)
    if published_year is not None and shown.index[0].year <= published_year <= shown.index[-1].year:
        line, note = publication_mark(published_year, max(11, size - 3))
        shapes.append(line)
        annotations.append(note)
    return shapes, annotations


def fig_decile_fan(
    wide: pd.DataFrame,
    *,
    horizon_label: str,
    reveal_until: pd.Timestamp | None = None,
    x_range: list | None = None,
    y_log_range: list[float] | None = None,
    height: int = 460,
    label_size: int = 12,
    show_title: bool = True,
    published_year: int | None = None,
) -> go.Figure:
    """Cumulative value of one dollar in each prior-return decile, log scale.

    wide: monthly returns, index month end, columns 1 to 10, already sliced to the window.
    reveal_until truncates the drawn portion without restarting the compounding, which is what
    makes the animated version grow into a fixed frame instead of rescaling.
    published_year draws the mark where the paper lands, when the drawn range has reached it.
    """
    if wide.empty:
        return _empty(f"No data for this window on {horizon_label.lower()}.", height)

    wealth = wealth_curves(wide)
    shown = wealth.loc[:reveal_until] if reveal_until is not None else wealth
    if shown.empty:
        return _empty(f"No data for this window on {horizon_label.lower()}.", height)

    colors = _rank_colors()
    fig = go.Figure()

    for decile in range(1, 11):
        extreme = decile in (1, 10)
        fig.add_trace(
            go.Scatter(
                x=shown.index,
                y=shown[decile],
                mode="lines",
                name="Bottom decile" if decile == 1 else "Top decile" if decile == 10 else f"D{decile}",
                line={"color": colors[decile - 1], "width": 2.2 if extreme else 1.1},
                opacity=1.0 if extreme else 0.75,
                showlegend=False,
                hovertemplate=f"%{{y:{fmt.NUMBER}}}x<extra>%{{fullData.name}}</extra>",
            )
        )

    # Labels ride the end of each line, so an animated reveal carries its own legend and the
    # static version needs no legend box competing with the title.
    shapes, annotations = _marks(shown, published_year, label_size)

    axis_range = y_log_range if y_log_range is not None else log_range(shown)
    decades = axis_range[1] - axis_range[0]
    fig.update_layout(
        title=f"One dollar by formation decile · {horizon_label}" if show_title else None,
        shapes=shapes,
        annotations=annotations,
        yaxis={
            "type": "log",
            "title": "Value of one dollar, log scale",
            "range": axis_range,
            # Decade ticks are right across a wide span and leave a single gridline across a
            # narrow one, so the choice follows the span.
            "dtick": 1 if decades >= 2.0 else None,
            "tickformat": fmt.NUMBER,
        },
        # Timestamps go in as strings. Plotly's own encoder takes them either way, but the
        # static export path does not, so a figure built the way the page builds it could not
        # be written to PNG and therefore could not be looked at.
        xaxis={"title": None, "range": _as_dates(x_range)},
        hovermode="x unified",
        margin={"l": 64, "r": 165, "t": 56 if show_title else 24, "b": 40},
        height=height,
    )
    return fig


# --------------------------------------------------------------------------- animation


def _play_pause(duration: int, *, from_current: bool, y: float = -0.02) -> dict:
    """Play and Pause, styled here because their defaults ignore the template.

    Left alone they land as white browser chrome on a graphite page. `redraw` is on for both
    figures that use this: the surface because a 3D trace never updates without it, the fan
    because its frames move layout annotations, which a data-only redraw does not touch.

    `y` is a fraction of the plotting area, measured down from its bottom edge. A 3D scene has
    nothing under it, so the default sits close. A cartesian figure has its tick labels there,
    and the readout lands on top of them unless the controls are pushed clear.
    """
    return {
        "type": "buttons",
        "direction": "right",
        "showactive": False,
        "x": 0,
        "y": y,
        "xanchor": "left",
        "yanchor": "top",
        "pad": {"r": 8},
        "font": {"family": theme.FONT_BODY, "size": 12, "color": theme.FG},
        "bgcolor": theme.BG_ELEVATED,
        "bordercolor": theme.LINE_STRONG,
        "borderwidth": 1,
        "buttons": [
            {
                "label": "Play",
                "method": "animate",
                "args": [
                    None,
                    {
                        "frame": {"duration": duration, "redraw": True},
                        "fromcurrent": from_current,
                        "transition": {"duration": 0},
                    },
                ],
            },
            {
                "label": "Pause",
                "method": "animate",
                "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
            },
        ],
    }


def _slider(
    names: list[str], labels: list[str], prefix: str, *, active: int, y: float = -0.02
) -> dict:
    """One step per frame. Scrubbing runs client side, with no rerun and no server work."""
    return {
        "active": active,
        "x": 0.18,
        "y": y,
        "len": 0.78,
        "yanchor": "top",
        "pad": {"t": 6},
        "bgcolor": theme.LINE,
        "bordercolor": theme.LINE_STRONG,
        "borderwidth": 0,
        "tickcolor": theme.LINE_STRONG,
        "font": {"family": theme.FONT_MONO, "size": 11, "color": theme.FG_SUBTLE},
        "currentvalue": {
            "prefix": prefix,
            "font": {"family": theme.FONT_MONO, "size": 13, "color": theme.ACCENT},
        },
        "steps": [
            {
                # The step label is also the readout, so it stays short and the slider prefix
                # carries the meaning. Plotly thins the ticks itself.
                "label": label,
                "method": "animate",
                "args": [[name], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
            }
            for name, label in zip(names, labels, strict=True)
        ],
    }


#: Months that end a reveal stop. Twice a year is the video's own cadence (animate.py), and
#: the app matches it so the two read as the same animation at the same rate.
STOP_MONTHS = (6, 12)

#: The video opens on two years of curve rather than a single dot, and so does the app.
HEAD_START_YEARS = 2

#: Float values a fan animation may ship. Sized by measurement rather than by taste: it leaves
#: the default 1965 to 1989 window the video's full twice-a-year cadence, at about 870 KB of
#: figure spec and 90 KB on the wire, and caps the whole century a reader can drag to at the
#: same cost by thinning the stops instead of the curve. Ungoverned, that century would be two
#: hundred frames and some 20 MB. Frames grow from nothing to the full window, so they average
#: half its length, which is the 5 rather than the 10 deciles in the arithmetic below.
FRAME_BUDGET_VALUES = 80_000


def reveal_steps(index: pd.DatetimeIndex, budget: int = FRAME_BUDGET_VALUES) -> list[pd.Timestamp]:
    """Where to stop the reveal: the video's cadence, thinned only when it will not fit.

    Twenty five years get all fifty stops, so the app plays exactly what the clip plays. A
    century keeps the same budget by taking every eighth stop. Fewer stops on the same data,
    never a thinned curve: the animation has to end on exactly the figure drawn without it.
    """
    if len(index) == 0:
        return []
    head = index[0] + pd.DateOffset(years=HEAD_START_YEARS)
    candidates = list(index[(index.month.isin(STOP_MONTHS)) & (index >= head)])
    if not candidates:
        return [index[-1]]

    affordable = max(2, budget // (5 * len(index)))
    stride = max(1, -(-len(candidates) // affordable))
    stops = candidates[::stride]
    if stops[-1] != index[-1]:
        stops.append(index[-1])
    return stops


def fig_decile_fan_animation(
    wide: pd.DataFrame,
    *,
    horizon_label: str,
    x_range: list | None = None,
    y_log_range: list[float] | None = None,
    height: int = 540,
    label_size: int = 12,
    published_year: int | None = None,
) -> go.Figure:
    """The fan again, with the reveal the video does, playable in the browser.

    A curve redrawing itself does not usually earn an animation, because the reader can
    already see the whole curve. What earns it here is that the figure **opens complete**: a
    reader who never presses play gets exactly the chart that was there before, and the motion
    is theirs to ask for, which is also how prefers-reduced-motion is honoured. Play rewinds
    and draws, so it always does something; the slider scrubs.

    Frames carry only y, as float32, cut at the stop. x is never resent: it stays on the base
    traces at full length, and Plotly draws whichever of the two runs out first, so a short y
    is a reveal. That is half the payload of masking the tail with nulls, and a quarter of
    resending the dates. The y range is fixed for all of them, so the curves grow into a
    stationary frame rather than the frame rescaling around them.
    """
    base = fig_decile_fan(
        wide,
        horizon_label=horizon_label,
        x_range=x_range,
        y_log_range=y_log_range,
        height=height,
        label_size=label_size,
        show_title=False,
        published_year=published_year,
    )
    if wide.empty:
        return base

    wealth = wealth_curves(wide)
    stops = reveal_steps(wealth.index)
    if len(stops) < 2:  # a window too short to reveal is just the figure
        return base

    frames = []
    for stop in stops:
        drawn = wealth.loc[:stop]
        shapes, annotations = _marks(drawn, published_year, label_size)
        frames.append(
            go.Frame(
                name=stop.isoformat(),
                data=[
                    go.Scatter(y=drawn[decile].to_numpy(dtype="float32"))
                    for decile in range(1, 11)
                ],
                layout={"shapes": shapes, "annotations": annotations},
            )
        )
    base.frames = frames
    # The controls clear the x axis rather than sitting on it, which is what the extra bottom
    # margin buys: tick labels, then buttons and the handle, then the handle's own ticks.
    below_the_axis = -0.09
    base.update_layout(
        margin={"l": 64, "r": 165, "t": 24, "b": 112},
        # 83 ms is the video's 12 fps. Same cadence, same rate, same animation.
        updatemenus=[_play_pause(83, from_current=False, y=below_the_axis)],
        sliders=[
            _slider(
                [frame.name for frame in frames],
                [str(stop.year) for stop in stops],
                "drawn through ",
                active=len(frames) - 1,
                y=below_the_axis,
            )
        ],
    )
    return base


# --------------------------------------------------------------------------- surface


def window_starts(dates: pd.DatetimeIndex, years: int = WINDOW_YEARS) -> list[int]:
    """Every start year for which a full window of data exists."""
    if len(dates) == 0:
        return []
    first, last = dates[0].year, dates[-1].year
    return [year for year in range(first, last + 1) if year + years - 1 <= last]


def window_slice(dates: pd.DatetimeIndex, start_year: int, years: int = WINDOW_YEARS) -> slice:
    """Positions covering exactly `years` calendar years from January of start_year.

    The end bound used to be December of start_year + years, which is eleven years of data
    under a label that says ten, and up to 0.88 percent a month of difference per cell.
    """
    begin = dates.searchsorted(pd.Timestamp(f"{start_year}-01-01"))
    end = dates.searchsorted(pd.Timestamp(f"{start_year + years - 1}-12-31"), side="right")
    return slice(int(begin), int(end))


def window_mean(dates: pd.DatetimeIndex, cube: np.ndarray, start_year: int) -> np.ndarray:
    """Mean monthly return in percent for the 5 by 5 grid over one window."""
    chunk = cube[window_slice(dates, start_year)]
    if chunk.size == 0:
        return np.full((5, 5), np.nan)
    with np.errstate(invalid="ignore"):
        return np.nanmean(chunk, axis=0) * 100.0


def tilt(matrix: np.ndarray) -> np.ndarray:
    """The grid relative to its own window average, which is what the surface shows."""
    return matrix - np.nanmean(matrix)


def tilt_bounds(dates: pd.DatetimeIndex, cube: np.ndarray) -> tuple[float, float]:
    """Symmetric bounds covering every window the reader can reach.

    Computed over exactly the windows the page can display, so bounds and display cannot
    drift apart. A fixed scale is required, otherwise a flat window and a steep one render
    identically, but it has to be the tightest fixed scale that still contains everything.
    """
    reach = 0.0
    for start in window_starts(dates):
        values = tilt(window_mean(dates, cube, start))
        if np.isfinite(values).any():
            reach = max(reach, float(np.nanmax(np.abs(values))))
    reach = reach or 1.0
    return -reach, reach


def _surface(matrix: np.ndarray, bounds: tuple[float, float], show_colorbar: bool) -> go.Surface:
    return go.Surface(
        x=list(range(1, 6)),
        y=list(range(1, 6)),
        z=matrix,
        colorscale=theme.DIVERGING,
        cauto=False,
        cmid=0.0,
        cmin=bounds[0],
        cmax=bounds[1],
        lighting={"ambient": 0.9, "diffuse": 0.3, "specular": 0.03, "roughness": 1.0},
        contours={"z": {"show": True, "color": theme.LINE, "width": 1, "usecolormap": False}},
        # No format spec on %{z}, and no literal Q. A 3D surface resolves both through its
        # scene axes before the template runs: the spec is dropped, so `:+.2f` printed
        # -0.47932119658119654, and %{x} already carries the axis ticktext, so a "Q" in front
        # of it printed QQ1. Precision now comes from zaxis.hoverformat in _scene.
        hovertemplate="size %{y} · prior %{x}<br>%{z} points vs window average<extra></extra>",
        showscale=show_colorbar,
        colorbar={
            "title": {
                "text": "points<br>per month",
                "font": {"family": theme.FONT_BODY, "size": 11, "color": theme.FG_MUTED},
            },
            "tickfont": {"family": theme.FONT_MONO, "size": 10, "color": theme.FG_SUBTLE},
            "tickformat": fmt.NUMBER,
            "outlinewidth": 0,
            "thickness": 10,
            "len": 0.55,
            "x": 0.9,
        },
    )


def _scene(bounds: tuple[float, float]) -> dict:
    scene = theme.scene("Prior return", "Size", "Tilt")
    # Starting at 0.02 pushed the box against the left edge once the camera moved to the far
    # side, and took the z ticks with it. Below roughly 800 pixels of panel a 3D axis title
    # still clips, because Plotly reserves no room for one and a fraction buys fewer pixels
    # the narrower the container gets.
    scene["domain"] = {"x": [0.14, 0.90], "y": [0.0, 1.0]}
    scene["xaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": PRIOR_TICKS}
    scene["yaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": SIZE_TICKS}
    # tickformat governs the ticks, hoverformat governs the hover label, and setting only the
    # first leaves the tooltip printing a raw double. fmt.PLAIN rather than fmt.SIGNED here:
    # the sign flag is what a scene axis rejects.
    scene["zaxis"] |= {
        "range": list(bounds),
        "dtick": 0.5,
        "tickformat": fmt.NUMBER,
        "hoverformat": fmt.PLAIN,
    }
    # The camera and the relief come from theme.scene. They used to be restated here with the
    # same numbers, which is two places to change and one of them to forget.
    return scene


def fig_size_prior_surface(
    matrix: np.ndarray,
    *,
    title: str | None,
    bounds: tuple[float, float],
    show_colorbar: bool = True,
    height: int = 560,
) -> go.Figure:
    """The size by prior-return tilt for one window, on a fixed diverging scale."""
    fig = go.Figure(_surface(matrix, bounds, show_colorbar))
    fig.update_layout(
        title=title,
        scene=_scene(bounds),
        height=height,
        margin={"l": 0, "r": 0, "t": 56, "b": 0},
    )
    return fig


def fig_size_prior_animation(
    dates: pd.DatetimeIndex,
    cube: np.ndarray,
    *,
    bounds: tuple[float, float],
    height: int = 580,
) -> go.Figure:
    """The same surface, rolling through the century, played in the browser.

    Time is the one dimension a static surface cannot show, which is what earns the animation.
    Frames carry only the z values, so ninety of them cost about 84 KB, and play and scrub run
    entirely client side with no rerun and no server work per step.

    There is no autoplay: motion starts when the reader asks for it.
    """
    starts = window_starts(dates)
    if not starts:
        return _empty("No window fits the available data.", height)

    def label(year: int) -> str:
        return f"{year} to {year + WINDOW_YEARS - 1}"

    # Frames replace the whole trace, so each one has to carry the colorbar. Dropping it in
    # the frames makes the scale vanish the moment the reader presses play.
    frames = [
        go.Frame(
            data=[_surface(tilt(window_mean(dates, cube, year)), bounds, True)],
            layout={"scene": {"zaxis": {"range": list(bounds)}}},
            name=label(year),
        )
        for year in starts
    ]

    fig = go.Figure(data=[_surface(tilt(window_mean(dates, cube, starts[0])), bounds, True)])
    fig.frames = frames

    fig.update_layout(
        scene=_scene(bounds),
        height=height,
        margin={"l": 60, "r": 20, "t": 10, "b": 80},
        updatemenus=[_play_pause(240, from_current=True)],
        sliders=[
            _slider(
                [label(year) for year in starts],
                [str(year) for year in starts],
                "ten years from ",
                active=0,
            )
        ],
    )
    return fig


# --------------------------------------------------------------------------- the crash


def fig_momentum_crash(mom: pd.Series, height: int = 400, *, show_title: bool = True) -> go.Figure:
    """Drawdown of the momentum factor, with the two deepest holes and today marked."""
    series = mom.dropna()
    if series.empty:
        return _empty("No factor history available.", height)

    wealth = (1.0 + series).cumprod()
    drawdown = wealth / wealth.cummax() - 1.0

    fig = go.Figure(
        go.Scatter(
            x=drawdown.index,
            y=drawdown,
            mode="lines",
            line={"color": theme.NEGATIVE, "width": 1.6},
            fill="tozeroy",
            fillcolor="rgba(255,124,0,0.14)",
            showlegend=False,
            hovertemplate=f"%{{x|%b %Y}}<br>%{{y:{fmt.PERCENT}}} below peak<extra></extra>",
        )
    )

    # Marks are derived, never hardcoded. Both used to be placed on the global minimum of the
    # monthly series, which put them on the same point with one of the two mislabelled.
    deepest = drawdown.idxmin()
    modern_trough = drawdown.loc["2009":"2012"].idxmin()
    today = drawdown.index[-1]
    marks = [
        (deepest, f"{deepest:%B %Y}, {drawdown.loc[deepest]:{fmt.PERCENT}} below peak", 46, -46),
        (
            modern_trough,
            f"{modern_trough:%B %Y}, {drawdown.loc[modern_trough]:{fmt.PERCENT}} below peak",
            6,
            62,
        ),
        (today, f"still {drawdown.loc[today]:{fmt.PERCENT}} below its 2008 peak", -110, -46),
    ]
    for stamp, note, ax, ay in marks:
        fig.add_annotation(
            x=stamp.isoformat(),
            y=float(drawdown.loc[stamp]),
            text=note,
            showarrow=True,
            arrowhead=0,
            arrowwidth=1,
            arrowcolor=theme.LINE_STRONG,
            ax=ax,
            ay=ay,
            font={"family": theme.FONT_BODY, "size": 11, "color": theme.FG_MUTED},
        )

    fig.update_layout(
        title="Momentum factor drawdown, monthly" if show_title else None,
        yaxis={"tickformat": fmt.PERCENT, "title": "Below running peak"},
        xaxis={"title": None},
        margin={"l": 64, "r": 40, "t": 56, "b": 40},
        height=height,
    )
    return fig


# --------------------------------------------------------------------------- numbers


ERAS = [
    ("1927 to 1964", "1927", "1964", "before publication"),
    ("1965 to 1989", "1965", "1989", "the paper's sample"),
    ("1990 to 2008", "1990", "2008", "after publication"),
    ("2009 to now", "2009", None, "including the 2009 unwind"),
]


def decile_table(wide: pd.DataFrame) -> pd.DataFrame:
    """Mean monthly return per decile, for readers who want the numbers rather than the fan.

    The eight middle lines carry no label and no legend entry by design. A table is what makes
    them readable without relying on hovering, which is not available on a touch screen.
    """
    if wide.empty:
        return pd.DataFrame(columns=["Decile", "Mean %/month", "Months"])
    return pd.DataFrame(
        {
            "Decile": [f"D{d}" for d in wide.columns],
            "Mean %/month": [round(wide[d].mean() * 100, fmt.DECIMALS) for d in wide.columns],
            "Months": [int(wide[d].notna().sum()) for d in wide.columns],
        }
    )


def era_stats(wide: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Top minus bottom decile per era, formatted for the stat tiles.

    Every ratio ships with its sample size and t statistic. A Sharpe ratio on its own, on a
    series this skewed, is a decoration.
    """
    if wide.empty:
        return []
    spread = (wide[10] - wide[1]).dropna()
    tiles = []
    for label, start, end, note in ERAS:
        window = spread.loc[start:end]
        if len(window) < 12 or window.std() == 0:
            tiles.append((label, "n/a", f"{note} · no data"))
            continue
        t_statistic = window.mean() / window.std() * np.sqrt(len(window))
        sharpe = window.mean() / window.std() * np.sqrt(12)
        tiles.append(
            (
                label,
                f"{window.mean() * 100:{fmt.SIGNED}}%",
                # Two lines by design. One long line wraps unpredictably across four columns.
                f"{note}<br>n {len(window)} · t {t_statistic:{fmt.SIGNED}} · SR {sharpe:{fmt.SIGNED}}",
            )
        )
    return tiles
