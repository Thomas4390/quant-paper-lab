"""Figures and summary numbers for the momentum reproduction.

This module is the single source of visual truth. The Streamlit page imports it, and so
does animate.py when it renders the video. Nothing here knows about either one, and nothing
here reads a file: callers pass data in.

Encoding choices, so they are not re-litigated per figure:
  Decile rank is ordered, so the ten lines take an ordered ramp, amber for the bottom decile
  through neutral gray to emerald for the top. Only the two extremes get a label, because
  the reader is asked to see a fan, not to identify decile six.
  Mean return can flip sign, so the surface uses the diverging scale anchored at zero.
  Drawdown is one measure, so it gets one axis and no legend.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from lab import theme

PRIOR_TICKS = ["Q1<br>losers", "Q2", "Q3", "Q4", "Q5<br>winners"]
SIZE_TICKS = ["Q1<br>small", "Q2", "Q3", "Q4", "Q5<br>large"]


def _rank_colors(n: int = 10) -> list[str]:
    """Ordered colors for rank, bottom to top."""
    return sample_colorscale(theme.DIVERGING, list(np.linspace(0.0, 1.0, n)))


# --------------------------------------------------------------------------- deciles


def wealth_curves(wide: pd.DataFrame) -> pd.DataFrame:
    """Value of one dollar per decile. Compounded once, so a reveal can slice it later."""
    return (1.0 + wide).cumprod()


def log_range(wealth: pd.DataFrame, *, pad: float = 0.12) -> list[float]:
    """Fixed y bounds in log10 units, so an animated reveal never rescales mid flight."""
    low = float(np.log10(max(wealth.min().min(), 1e-4)))
    high = float(np.log10(wealth.max().max()))
    reach = (high - low) * pad
    return [low - reach, high + reach]


def fig_decile_fan(
    wide: pd.DataFrame,
    *,
    horizon_label: str,
    reveal_until: pd.Timestamp | None = None,
    x_range: list | None = None,
    y_log_range: list[float] | None = None,
    height: int = 460,
    label_size: int = 12,
) -> go.Figure:
    """Cumulative value of one dollar in each prior-return decile, log scale.

    wide: monthly returns, index month end, columns 1 to 10, already sliced to the window.
    reveal_until truncates the drawn portion without restarting the compounding, which is
    what makes the animated version grow into a fixed frame instead of rescaling.
    """
    wealth = wealth_curves(wide)
    shown = wealth.loc[:reveal_until] if reveal_until is not None else wealth
    colors = _rank_colors(10)
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
                opacity=1.0 if extreme else 0.5,
                showlegend=extreme,
                hoverinfo="x+y+name" if extreme else "skip",
                hovertemplate=None if not extreme else "%{y:,.1f}x<extra>%{fullData.name}</extra>",
            )
        )

    # Labels ride the end of each line, so an animated reveal carries its own legend.
    last = shown.index[-1]
    for decile, text in ((10, "Top decile"), (1, "Bottom decile")):
        value = shown[decile].iloc[-1]
        fig.add_annotation(
            x=last.isoformat(),
            y=float(np.log10(max(value, 1e-6))),
            text=f"  {text} · {value:,.0f}x" if value >= 1 else f"  {text} · {value:.3f}x",
            showarrow=False,
            xanchor="left",
            font={"family": theme.FONT_BODY, "size": label_size, "color": colors[decile - 1]},
        )

    fig.update_layout(
        title=f"One dollar, compounded by formation decile · {horizon_label}",
        yaxis={
            "type": "log",
            "title": "Value of one dollar, log scale",
            "range": y_log_range,
            "dtick": 1,  # decades only, the minor log ticks are noise at this span
        },
        xaxis={"title": None, "range": x_range},
        hovermode="x unified",
        margin={"l": 64, "r": 150, "t": 56, "b": 40},
        height=height,
    )
    return fig


# --------------------------------------------------------------------------- surface


def surface_matrix(tidy: pd.DataFrame, start: str | pd.Timestamp, end: str | pd.Timestamp) -> np.ndarray:
    """Mean monthly return in percent for the 5 by 5 size and prior-return grid.

    Rows are size quintiles 1 to 5, columns are prior-return quintiles 1 to 5.
    """
    window = tidy[(tidy.date >= pd.Timestamp(start)) & (tidy.date <= pd.Timestamp(end))]
    grid = window.pivot_table(index="size_q", columns="prior_q", values="ret", aggfunc="mean") * 100.0
    return grid.reindex(index=range(1, 6), columns=range(1, 6)).to_numpy(dtype="float64")


def surface_bounds(tidy: pd.DataFrame, *, window_years: int, step_months: int = 12) -> tuple[float, float]:
    """Symmetric colour and z bounds across every rolling window.

    The animation must not rescale between frames, otherwise a flat surface and a steep one
    look identical. Compute the bounds once, over all windows, and reuse them everywhere.
    """
    dates = pd.DatetimeIndex(sorted(tidy.date.unique()))
    span = pd.DateOffset(years=window_years)
    lo, hi = np.inf, -np.inf
    cursor = dates[0]
    while cursor + span <= dates[-1]:
        values = surface_matrix(tidy, cursor, cursor + span)
        lo, hi = min(lo, np.nanmin(values)), max(hi, np.nanmax(values))
        cursor = cursor + pd.DateOffset(months=step_months)
    reach = max(abs(lo), abs(hi))
    return -reach, reach


def fig_size_prior_surface(
    matrix: np.ndarray,
    *,
    title: str,
    bounds: tuple[float, float],
    show_colorbar: bool = True,
) -> go.Figure:
    """The size by prior-return surface for one window, on a fixed diverging scale."""
    fig = go.Figure(
        go.Surface(
            x=list(range(1, 6)),
            y=list(range(1, 6)),
            z=matrix,
            colorscale=theme.DIVERGING,
            cmid=0.0,
            cmin=bounds[0],
            cmax=bounds[1],
            lighting={"ambient": 0.88, "diffuse": 0.35, "specular": 0.04, "roughness": 1.0},
            contours={
                "z": {"show": True, "color": theme.LINE, "width": 1, "usecolormap": False},
            },
            hovertemplate="size Q%{y} · prior Q%{x}<br>%{z:+.2f} %/month<extra></extra>",
            colorbar={
                "title": {
                    "text": "%/month",
                    "font": {"family": theme.FONT_BODY, "size": 11, "color": theme.FG_MUTED},
                },
                "tickfont": {"family": theme.FONT_MONO, "size": 10, "color": theme.FG_SUBTLE},
                "outlinewidth": 0,
                "thickness": 10,
                "len": 0.62,
                "y": 0.5,
            }
            if show_colorbar
            else None,
            showscale=show_colorbar,
        )
    )
    scene = theme.scene("Prior return", "Size", "%/month")
    scene["xaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": PRIOR_TICKS}
    scene["yaxis"] |= {"tickmode": "array", "tickvals": list(range(1, 6)), "ticktext": SIZE_TICKS}
    scene["zaxis"] |= {"range": list(bounds)}
    fig.update_layout(title=title, scene=scene, height=560, margin={"l": 0, "r": 0, "t": 56, "b": 0})
    return fig


# --------------------------------------------------------------------------- the crash


def fig_momentum_crash(mom: pd.Series) -> go.Figure:
    """Drawdown of the momentum factor, with the two historic unwinds marked."""
    wealth = (1.0 + mom.dropna()).cumprod()
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

    worst_month = mom.idxmin()
    for stamp, note in (
        (pd.Timestamp("1932-08-31"), f"1932 reversal, {mom.loc['1932-08-31']:.0%} in one month"),
        (worst_month, f"April 2009, {mom.loc[worst_month]:.0%} in one month"),
    ):
        if stamp in drawdown.index:
            fig.add_annotation(
                x=stamp.isoformat(),
                y=drawdown.loc[stamp],
                text=note,
                showarrow=True,
                arrowhead=0,
                arrowwidth=1,
                arrowcolor=theme.LINE_STRONG,
                ax=30,
                ay=40,
                font={"family": theme.FONT_BODY, "size": 11, "color": theme.FG_MUTED},
            )

    fig.update_layout(
        title="Momentum factor drawdown, monthly",
        yaxis={"tickformat": ".0%", "title": "Below running peak"},
        xaxis={"title": None},
        height=380,
    )
    return fig


# --------------------------------------------------------------------------- numbers


ERAS = [
    ("1927-1964", "1927-01-01", "1964-12-31", "before publication"),
    ("1965-1989", "1965-01-01", "1989-12-31", "the paper's sample"),
    ("1990-2008", "1990-01-01", "2008-12-31", "after publication"),
    ("2009 to now", "2009-01-01", "2100-12-31", "after the crash"),
]


def era_stats(wide: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Top minus bottom decile per era, formatted for the stat tiles."""
    spread = (wide[10] - wide[1]).dropna()
    tiles = []
    for label, start, end, note in ERAS:
        window = spread.loc[start:end]
        if window.empty:
            continue
        sharpe = window.mean() / window.std() * np.sqrt(12)
        tiles.append((label, f"{window.mean() * 100:+.2f}%", f"{note} · Sharpe {sharpe:+.2f}"))
    return tiles
