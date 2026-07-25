"""Figures and summary numbers for the momentum reproduction.

This module is the single source of visual truth. The Streamlit page imports it, and so does
animate.py when it renders the video. Nothing here knows about either one, and nothing here
reads a file: callers pass data in.

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


def _multiple(value: float) -> str:
    """Format a growth multiple at the precision a reader would check.

    Rounding to the nearest integer printed 1.5152 as 2x, a 32 percent overstatement on any
    short window.
    """
    if not np.isfinite(value):
        return "n/a"
    if value >= 100:
        return f"{value:,.0f}x"
    if value >= 10:
        return f"{value:,.1f}x"
    return f"{value:,.2f}x"


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
) -> go.Figure:
    """Cumulative value of one dollar in each prior-return decile, log scale.

    wide: monthly returns, index month end, columns 1 to 10, already sliced to the window.
    reveal_until truncates the drawn portion without restarting the compounding, which is what
    makes the animated version grow into a fixed frame instead of rescaling.
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
                hovertemplate="%{y:,.2f}x<extra>%{fullData.name}</extra>",
            )
        )

    # Labels ride the end of each line, so an animated reveal carries its own legend and the
    # static version needs no legend box competing with the title.
    last = shown.index[-1]
    for decile, text in ((10, "Top decile"), (1, "Bottom decile")):
        value = float(shown[decile].iloc[-1])
        fig.add_annotation(
            x=last.isoformat(),
            y=float(np.log10(max(value, 1e-6))),
            text=f"  {text} · {_multiple(value)}",
            showarrow=False,
            xanchor="left",
            font={"family": theme.FONT_BODY, "size": label_size, "color": colors[decile - 1]},
        )

    axis_range = y_log_range if y_log_range is not None else log_range(shown)
    decades = axis_range[1] - axis_range[0]
    fig.update_layout(
        title=f"One dollar by formation decile · {horizon_label}" if show_title else None,
        yaxis={
            "type": "log",
            "title": "Value of one dollar, log scale",
            "range": axis_range,
            # Decade ticks are right across a wide span and leave a single gridline across a
            # narrow one, so the choice follows the span.
            "dtick": 1 if decades >= 2.0 else None,
        },
        xaxis={"title": None, "range": x_range},
        hovermode="x unified",
        margin={"l": 64, "r": 165, "t": 56 if show_title else 24, "b": 40},
        height=height,
    )
    return fig


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
        hovertemplate="size Q%{y} · prior Q%{x}<br>%{z:+.2f} points vs window average<extra></extra>",
        showscale=show_colorbar,
        colorbar={
            "title": {
                "text": "points<br>per month",
                "font": {"family": theme.FONT_BODY, "size": 11, "color": theme.FG_MUTED},
            },
            "tickfont": {"family": theme.FONT_MONO, "size": 10, "color": theme.FG_SUBTLE},
            "outlinewidth": 0,
            "thickness": 10,
            "len": 0.55,
            "x": 0.9,
        },
    )


def _scene(bounds: tuple[float, float]) -> dict:
    scene = theme.scene("Prior return", "Size", "Tilt")
    scene["domain"] = {"x": [0.02, 0.9], "y": [0.0, 1.0]}
    scene["xaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": PRIOR_TICKS}
    scene["yaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": SIZE_TICKS}
    scene["zaxis"] |= {"range": list(bounds), "dtick": 0.5}
    # Taller relief and a closer eye than the default, because the whole point of the third
    # dimension here is a difference of about a point a month, and a 3D scene left to itself
    # sits small in the middle of a wide container.
    
    scene["camera"] = {"eye": {"x": 1.15, "y": -1.3, "z": 0.5}}
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

    button = {
        "font": {"family": theme.FONT_BODY, "size": 12, "color": theme.FG},
        "bgcolor": theme.BG_ELEVATED,
        "bordercolor": theme.LINE_STRONG,
        "borderwidth": 1,
    }
    fig.update_layout(
        scene=_scene(bounds),
        height=height,
        margin={"l": 60, "r": 20, "t": 10, "b": 80},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "showactive": False,
                "x": 0,
                "y": -0.02,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"r": 8},
                **button,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        # 3D traces need redraw, otherwise the surface never updates.
                        "args": [
                            None,
                            {
                                "frame": {"duration": 240, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"},
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "x": 0.18,
                "y": -0.02,
                "len": 0.78,
                "yanchor": "top",
                "pad": {"t": 6},
                "bgcolor": theme.LINE,
                "bordercolor": theme.LINE_STRONG,
                "borderwidth": 0,
                "tickcolor": theme.LINE_STRONG,
                "font": {"family": theme.FONT_MONO, "size": 11, "color": theme.FG_SUBTLE},
                "currentvalue": {
                    "prefix": "ten years from ",
                    "font": {"family": theme.FONT_MONO, "size": 13, "color": theme.ACCENT},
                },
                "steps": [
                    {
                        # The step label is also the readout, so it stays short and the
                        # slider prefix carries the meaning. Plotly thins the ticks itself.
                        "label": str(year),
                        "method": "animate",
                        "args": [
                            [label(year)],
                            {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"},
                        ],
                    }
                    for year in starts
                ],
            }
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
            hovertemplate="%{x|%b %Y}<br>%{y:.0%} below peak<extra></extra>",
        )
    )

    # Marks are derived, never hardcoded. Both used to be placed on the global minimum of the
    # monthly series, which put them on the same point with one of the two mislabelled.
    deepest = drawdown.idxmin()
    modern_trough = drawdown.loc["2009":"2012"].idxmin()
    today = drawdown.index[-1]
    marks = [
        (deepest, f"{deepest:%B %Y}, {drawdown.loc[deepest]:.0%} below peak", 46, -46),
        (modern_trough, f"{modern_trough:%B %Y}, {drawdown.loc[modern_trough]:.0%} below peak", 6, 62),
        (today, f"still {drawdown.loc[today]:.0%} below its 2008 peak", -110, -46),
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
        yaxis={"tickformat": ".0%", "title": "Below running peak"},
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
            "Mean %/month": [round(wide[d].mean() * 100, 3) for d in wide.columns],
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
                f"{window.mean() * 100:+.2f}%",
                # Two lines by design. One long line wraps unpredictably across four columns.
                f"{note}<br>n {len(window)} · t {t_statistic:+.2f} · SR {sharpe:+.2f}",
            )
        )
    return tiles
