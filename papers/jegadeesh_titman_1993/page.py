"""Momentum, Jegadeesh and Titman (1993). The interactive reproduction."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from lab import data, layout
from papers.jegadeesh_titman_1993 import figures

HERE = Path(__file__).resolve().parent
WINDOW_YEARS = 10

paper = layout.load_paper(HERE)
layout.page_header(paper)

canonical = data.deciles("prior_12_2")
layout.stat_tiles(figures.era_stats(canonical))
st.markdown(
    '<p style="font-size:12px;margin-top:10px">Top decile minus bottom decile, '
    "average monthly return, value weighted, gross of costs.</p>",
    unsafe_allow_html=True,
)
st.write("")
st.write("")

# --------------------------------------------------------------- figure 1, the fan
st.markdown('<div class="eyebrow">Figure 1 · the horizon decides the sign</div>', unsafe_allow_html=True)
first, last = data.coverage()
control_left, control_right = st.columns([1.6, 2.4], gap="large")
with control_left:
    horizon = st.segmented_control(
        "Formation horizon",
        options=list(data.HORIZON_LABELS),
        format_func=lambda key: data.HORIZON_LABELS[key],
        default="prior_12_2",
        key="horizon",
    )
with control_right:
    years = st.slider(
        "Window",
        min_value=first.year,
        max_value=last.year,
        value=(1965, 1989),
        key="fan_years",
    )

horizon = horizon or "prior_12_2"
window = data.deciles(horizon).loc[str(years[0]) : str(years[1])]
layout.figure(
    figures.fig_decile_fan(window, horizon_label=data.HORIZON_LABELS[horizon]),
    caption=(
        "Ten value weighted portfolios, sorted every month on the return over the chosen "
        "formation window, then held for one month. Switch the horizon to see the effect "
        "change sign: one month of prior return reverses, a year of it continues, five "
        "years of it reverses again. The paper's own sample is 1965 to 1989."
    ),
    key="fan",
)

# --------------------------------------------------------------- figure 2, the surface
st.markdown('<div class="eyebrow">Figure 2 · where the tilt lives, and when</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _bounds() -> tuple[float, float]:
    """Colour and z bounds shared by every window, so frames stay comparable."""
    return figures.surface_bounds(data.size_prior(), window_years=WINDOW_YEARS)


tidy = data.size_prior()
bounds = _bounds()
start_year = st.slider(
    f"Start of the {WINDOW_YEARS} year window",
    min_value=int(tidy.date.min().year),
    max_value=int(tidy.date.max().year) - WINDOW_YEARS,
    value=1965,
    key="surface_start",
)
end_year = start_year + WINDOW_YEARS
layout.figure(
    figures.fig_size_prior_surface(
        figures.surface_matrix(tidy, f"{start_year}-01-01", f"{end_year}-12-31"),
        title=f"Mean monthly return by size and prior return · {start_year} to {end_year}",
        bounds=bounds,
    ),
    caption=(
        "Twenty five portfolios, split five ways on market capitalisation and five ways on "
        "the prior 2 to 12 month return. The surface rises toward past winners whenever "
        "momentum is paying, and flattens when it is not. The colour and height scales are "
        "fixed across every window, so a flat surface really is flat. Drag the slider "
        "through 2009 and watch the tilt go."
    ),
    key="surface",
)

# --------------------------------------------------------------- figure 3, the caveat
st.markdown('<div class="eyebrow">Figure 3 · the bill comes at once</div>', unsafe_allow_html=True)
layout.figure(
    figures.fig_momentum_crash(data.factors()["mom"]),
    caption=(
        "The cost of the strategy is not a slow bleed, it is a handful of violent reversals "
        "that arrive when the market turns. April 2009 took 34 percent off the factor in a "
        "single month, and the drawdown that began in 2009 has still not been recovered."
    ),
    key="crash",
)

with st.expander("How this reproduction differs from the paper"):
    st.markdown(paper["method_notes"])
    st.markdown(
        "**Claims on this page, and where to check them**\n\n"
        + "\n".join(f"- {c['claim']} `{c['evidence']}`" for c in paper["claims"])
    )

layout.sources_and_disclaimer(paper)
