"""Momentum, Jegadeesh and Titman (1993). The interactive reproduction."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab import data, layout
from papers.jegadeesh_titman_1993 import figures

HERE = Path(__file__).resolve().parent

paper = layout.load_paper(HERE)
layout.page_header(paper)

# ------------------------------------------------------------------ controls, once, at the top
layout.section(
    "The sort",
    "Choose how the portfolios are formed",
    "Everything below follows these two choices. The window applies to the compounding in "
    "figure 1 and to the table above it.",
)

horizon = st.segmented_control(
    "Formation horizon",
    options=list(data.HORIZON_LABELS),
    format_func=lambda key: data.HORIZON_LABELS[key].replace("Prior ", ""),
    default="prior_12_2",
    key="horizon",
) or "prior_12_2"

weighting_column, window_column = st.columns([1.1, 2.9], gap="large")
with weighting_column:
    weighting = st.segmented_control(
        "Weighting",
        options=list(data.WEIGHTINGS),
        format_func=lambda key: data.WEIGHTINGS[key].replace(" weighted", ""),
        default="vw",
        key="weighting",
    ) or "vw"
with window_column:
    # Bounded by the chosen horizon, not by a fixed range. Sorting on the prior 13 to 60
    # months cannot start before 1931, and a window outside a horizon's coverage used to take
    # the whole page down.
    first, last = data.coverage(horizon)
    # The key stays stable so the reader keeps their window when switching horizon, and the
    # stored value is pulled back inside the new coverage rather than left out of range.
    if isinstance(st.session_state.get("fan_years"), tuple):
        low, high = st.session_state["fan_years"]
        st.session_state["fan_years"] = (
            min(max(low, first.year), last.year),
            min(max(high, first.year), last.year),
        )
    years = st.slider(
        "Window",
        min_value=first.year,
        max_value=last.year,
        value=(max(1965, first.year), min(1989, last.year)),
        key="fan_years",
    )

window = slice(str(years[0]), str(years[1]))
wide = data.deciles(horizon, weighting).loc[window]
full = data.deciles(horizon, weighting)
# The y scale spans all three horizons over the same window, so switching horizon compares
# like with like instead of rescaling the axis under the reader.
shared_y = figures.shared_log_range(
    data.deciles(key, weighting).loc[window] for key in data.HORIZON_LABELS
)

# ------------------------------------------------------------------ the numbers
layout.stat_tiles(figures.era_stats(full))
layout.caption(
    f"Top decile minus bottom decile, average monthly return, {data.WEIGHTINGS[weighting].lower()}, "
    f"gross of costs, on {data.HORIZON_LABELS[horizon].lower()} of prior return. "
    "Eras are fixed so they stay comparable as you change the sort."
)

# ------------------------------------------------------------------ figure 1, the fan
layout.section(
    "Figure 1",
    "The horizon decides the sign",
    "Ten portfolios, sorted every month on the return over the chosen "
    "formation window, then held for one month. Switch the horizon and the effect changes "
    "sign: one month of prior return reverses, a year of it continues, five years of it "
    "reverses again.",
)
layout.figure(
    figures.fig_decile_fan(
        wide,
        horizon_label=data.HORIZON_LABELS[horizon],
        show_title=False,
        y_log_range=shared_y,
        x_range=[wide.index[0], wide.index[-1]] if not wide.empty else None,
    ),
    note=(
        f"{data.WEIGHTINGS[weighting]} deciles, {years[0]} to {years[1]}. Compounding restarts "
        "at the left edge of the window, so the multiples are for that window only. The "
        "paper's own sample is 1965 to 1989."
    ),
    key="fan",
)

# ------------------------------------------------------------------ figure 2, the surface
layout.section(
    "Figure 2",
    "Where the tilt lives, and when",
    "Twenty five portfolios, split five ways on market capitalisation and five ways on the "
    "prior 2 to 12 month return. Height is each portfolio's average monthly return minus the "
    "average of its own ten year window, so what you see is the tilt and not the level of the "
    "market at the time. Prior return runs from the biggest losers on the left to the "
    "biggest winners on the right, size from the smallest companies to the largest. Press "
    "play, or drag the handle through 2009.",
)
dates, cube = data.size_prior_cube()
layout.figure(
    figures.fig_size_prior_animation(dates, cube, bounds=figures.tilt_bounds(dates, cube)),
    note=(
        "Colour and height are fixed across every window, so a flat surface really is flat. "
        "This panel always uses value weighted portfolios and the prior 2 to 12 month sort, "
        "whatever is selected above."
    ),
    key="surface",
)

# ------------------------------------------------------------------ figure 3, the caveat
layout.section(
    "Figure 3",
    "The bill comes at once",
    "The cost of the strategy is not a slow bleed, it is a handful of violent reversals that "
    "arrive when the market turns. April 2009 took 34 percent off the factor in one month, "
    "its worst since 1932. It is not even the deepest hole on record.",
)
layout.figure(
    figures.fig_momentum_crash(data.factors()["mom"], show_title=False),
    note=(
        "Drawdown of the Ken French momentum factor, gross of costs. The factor last made a "
        "new high in November 2008."
    ),
    key="crash",
)

with st.expander("How this reproduction differs from the paper, and what the numbers do not say"):
    st.markdown(paper["method_notes"])
    st.markdown("**Figure 1, decile by decile**")
    st.dataframe(
        figures.decile_table(wide),
        width="stretch",
        hide_index=True,
    )
    st.markdown("**Claims on this page, and where to check them**")
    st.markdown("\n".join(f"- {claim['claim']} `{claim['evidence']}`" for claim in paper["claims"]))

layout.sources_and_disclaimer(paper)
