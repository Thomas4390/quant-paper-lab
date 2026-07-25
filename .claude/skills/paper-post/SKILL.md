---
name: paper-post
description: Use when producing a LinkedIn post from a research paper in this repo, from picking the paper to the pre-flight before publishing. Covers the data licence gate, the reproduction check, statistical honesty, the app page, the animation, the MP4 render and the copy. Trigger on "new paper", "next post", "prepare the momentum post", or any work inside papers/.
---

# One paper, one post

The pipeline turns a paper into three artifacts: a page in the app, an MP4 for the feed, and
the copy. They ship together or not at all. Work the steps in order. Each has a gate that can
send you back, and the earliest gate is the cheapest.

Everything below that reads like a rule was learned by getting it wrong once.

## Step 1. Pick the paper, then try to kill it

Before writing any code: **can this be reproduced on data that may live in a public repo?**

- Free and fine: Kenneth R. French Data Library, FRED, Stooq, Yahoo, public CBOE files.
- Never here: CRSP, WRDS, OptionMetrics, or anything under a vendor licence. That includes the
  491 GB of option chains on the local volume. A derived aggregate from licensed data may be
  publishable, but only after reading that vendor's terms, and the answer goes in `paper.yaml`.
- **The survivorship trap.** A current-listings universe cannot reproduce a cross-sectional
  sort. The bottom decile of any loser portfolio is full of names that later delisted. If the
  only universe available is a present-day snapshot, the paper is out.

A reproduction on the wrong data is worse than no post. This audience will find it.

## Step 2. Scaffold and declare the claims first

Run `/new-paper <slug_with_underscores>`, then fill `paper.yaml` before touching a figure.

`claims` is the contract. Every number that will appear in the post goes there, tied to the
thing in the app that shows it. Two failure modes to avoid, both found in review:

- A claim pointing at a figure that does not display that number. If the claim is a mean and
  the figure is a compounded curve, the reader cannot check it.
- A claim the app cannot show at all, because the control it depends on does not exist yet.

If a claim has no home in the app, either build the home or drop the claim.

`method_notes` states how the reproduction differs from the original. There is always a
difference. Naming it is what separates a reproduction from a hand wave.

## Step 3. Build the data offline

`build_data.py` downloads, computes and writes parquet to `data/`. It runs by hand, never at
request time. Raw downloads go to `data/raw/`, which git ignores.

**Never select a source table by position.** Ken French files stack several tables with the
same monthly shape: value weighted returns, equal weighted returns, firm counts, average firm
size. Taking the first one that parses works until the day it does not, and the failure is
silent. Match the title, loosely, because the titles are not uniform and one of them contains
a typo in the source (`Aerage Value Weighted Returns`).

**Assert the mapping you cannot key on.** Where columns have to be mapped by position, find a
statistical property that a transposition would break and assert it at build time. For the 25
size by prior portfolios it is that volatility falls monotonically with size. Without that
check, swapping the two axes passes every test in the suite.

## Step 4. Reproduce the paper's own construction, not the convenient one

The lesson that changed this repo's first post: our value weighted spread came out at 1.63
percent a month against 1.31 published, and the method notes blamed the holding period. The
real cause was in the same file all along. Jegadeesh and Titman used **equal weighted**
portfolios, and the equal weighted table gives 1.332 percent, within 0.03 points of the paper.

So: find out how the paper weighted, sampled and rebalanced, and reproduce **that** first.
Publish the modern convention next to it if it is interesting, and say which is which. An
unexplained gap to the published number reads as a failed reproduction. An explained one is
the most convincing thing on the page.

## Step 5. Check the numbers before drawing anything

Write the assertions first, in `tests/`, split into two kinds:

- **Invariants**: shapes, units, orderings, mappings. Never relaxed.
- **Golden values**: what the repo publishes, with a tolerance wide enough for a source
  revision and narrow enough to catch the wrong table. When the source revises, regenerate
  them deliberately in a commit that says so. Do not widen them quietly.

Then interrogate your own headline like an opponent would:

- **Put an interval on every claim of change.** "It stopped working" needed a t of 1.74 and a
  p of 0.08. That is not a finding, it is a point estimate with a wide interval, and saying so
  is more impressive than hiding it.
- **Check the sensitivity to a handful of observations.** The post-2009 average of 0.16
  percent becomes 0.57 percent without March and April 2009. Two months out of 209.
- **Do not mix arithmetic and geometric to suit the story.** Compounding the flattering number
  and averaging the awkward one is the single most attackable thing you can do. Pick one, or
  give both. The same spread that "averages 0.16 percent a month" lost 47 percent compounded.
- **Benchmark the compounded figures.** One dollar becoming 16,908 means little until you say
  the market did 535 over the same window.
- **Price the frictions.** A monthly rebalanced decile sort dies at roughly 1.6 percent a
  month of round trip cost. Give the sensitivity, do not let the reader assume it is small.
- **Report n and t next to every Sharpe.** Annualising by the square root of 12 on a series
  with skew of -2.1 is optimistic, and saying so costs nothing.
- **Check monotonicity before implying a gradient.** "Weakest in the largest, 0.59 against
  0.88 for the smallest" invites the reader to infer a size gradient that does not exist. The
  strongest quintile was the second smallest.

## Step 6. Figures, then the page

`figures.py` returns Plotly figures and knows nothing about Streamlit or video. It is the
single source of visual truth, which keeps the app and the MP4 from drifting.

Encoding rules, already decided:

- Ordered dimensions take the ordered ramp, amber through neutral gray to emerald.
- Anything that can flip sign uses `theme.DIVERGING` with `cmid=0`.
- One measure, one axis. Never two y scales.
- Two or more series get a legend, or direct labels on the ones that matter.
- A number read once is a stat tile, not a chart.

**A fixed scale has to be computed on the windows that will actually be displayed.** Fixing
the scale is right, since a scale that rescales between frames lies about the data. But a
scale set by the most extreme window in the sample flattens every other one. Measure the share
of the axis a typical window occupies. Absolute returns gave 21 percent, which is why every
modern surface looked like a plate. Removing the window's own mean and showing the tilt gave
43 percent and asked the better question. If bounds and display use two nearly identical
window definitions, they will disagree the day one of them changes.

**Rank is ordered, not signed.** Ten deciles take a single hue ramp, dark to light, with one
accent reserved for the bottom. Sampling the diverging scale for rank put four of the ten
lines under 3:1 against the background and gave deciles 5 and 6 the same lightness, which is
a grey smear where the fan should be. Diverging belongs to quantities that cross zero.

**Validate the ramp instead of trusting it.** `dataviz/scripts/validate_palette.js` takes the
hex list and the surface. Its categorical checks do not apply to an ordered ramp, but its
contrast column does, and that is the one that failed.

**Format numbers at the precision the reader will check.** `,.0f` printed 1.5152 as `2x`.

**Streamlit overwrites the figure theme unless told not to.** `st.plotly_chart(...)` defaults
to `theme="streamlit"`, which replaces the typography of every figure with its own. The
template still applies in the offline render, so the app and the video drift apart silently.
Pass `theme=None`. It is a correctness setting, not a preference.

**Fonts belong in `.streamlit/config.toml`, never in injected CSS.** A rule in an injected
stylesheet loses the cascade to Streamlit's own class selectors, and since webfonts load
lazily, a family that never wins a rule is never even downloaded. Playfair was absent from
every heading for exactly that reason, with no error anywhere. Verify in the browser with
`document.fonts.check(...)`, not by reading the CSS.

**Look at the figure.** Export a PNG and open it. Do not judge a chart from its code.

## Step 7. Animate only where time is the point

An animation earns its place when the variable being animated cannot be seen any other way. A
ten year window rolling through the century qualifies, because the third dimension is time. A
curve redrawing itself does not, because the reader can already see the whole curve.

Technique, in the app: Plotly frames plus `updatemenus` and a `sliders` block. Play and scrub
then happen entirely in the browser, with no Streamlit rerun and no server work per step. For
a 5 by 5 surface, ninety frames cost about 84 KB.

Traps, all real:

- 3D traces need `redraw: True` in the frame args, or nothing updates.
- Set the camera once on the base figure and never inside a frame, otherwise the view snaps
  back on every step.
- Freeze `cmin`, `cmax` and the z range across all frames, and derive them from all frames.
- Style `updatemenus` and `sliders` explicitly. Their defaults ignore the template and land as
  white browser chrome on a graphite page.
- Honour `prefers-reduced-motion` by not autoplaying. Let the reader press play.

## Step 8. Render the video, not a GIF

**LinkedIn does not animate GIFs in the feed.** An uploaded animated GIF is flattened to its
first frame. The asset is a native MP4. The GIF `animate.py` also writes is for the README,
for X and for the site.

Targets: 1200 by 1200, 12 fps, 10 to 15 seconds, no audio track, every label burned in,
readable on a phone. Iterate with `--preview <year>` on one frame before rendering the clip.

## Step 9. Every control must degrade, never raise

An exception in a Streamlit page does not blank the chart, it blanks **the page**, including
the legal disclaimer at the bottom. That is how ten of five thousand reachable slider
positions once took the whole notice down with them.

- Bound a control by the data it actually selects. Three formation horizons with three
  different start dates cannot share one slider range taken from the middle one.
- An empty selection returns a figure that says it is empty, never an exception.
- Guard the degenerate shapes: a single point, a constant series, a zero length window, a
  value of zero under a logarithm.
- `st.columns(0)` raises. Any row built from a list can receive an empty list.
- Set `showErrorDetails = "none"` in `.streamlit/config.toml`. A public page must not ship
  absolute server paths to whoever trips an error.
- Cover it with `AppTest` driving the widgets through their extremes, and assert the
  disclaimer is still on the page.

## Step 10. Verify what a visitor sees

Static exports check figures. They do not check vertical rhythm, line length, or whether a
control wrapped onto two lines. Run the app and screenshot it:

```bash
uv run --group dev --group render streamlit run streamlit_app.py --server.port 8511 --server.headless true &
uv run --group dev --group render python tools/shoot.py --out /tmp/shots --animate momentum-1993
```

Then open the images. Use the same `uv` group set for the server and for the tools, and be
aware that Streamlit scrolls inside its own container, so a full page capture needs a tall
viewport rather than `full_page=True`.

**Pin the stack that the deployment will run.** pandas 3.0.5 with pyarrow 25 segfaulted the
server on the third browser session, inside `pivot_table`, with no Python traceback. Found
only by loading the page repeatedly. `PYTHONFAULTHANDLER=1` gives the native trace. The app
gains nothing from the newest major, and a public page that dies on the third visitor is not a
page. Pinned to pandas 2.

## Step 11. Pre-flight

Nothing ships until all of this is true:

- [ ] `uv run --group dev pytest -q` green
- [ ] every claim in the post traced to `paper.yaml`, and every claim visible in the app
- [ ] intervals, n and t published next to every headline number
- [ ] cost sensitivity stated
- [ ] data licence checked and named in `paper.yaml`
- [ ] disclaimer visible, and still visible at every extreme of every control
- [ ] `published` set in `paper.yaml`, then `uv run python -m lab.manifest`
- [ ] MP4 probed: square, no audio, 10 to 15 seconds
- [ ] MP4 watched once, muted, at phone size
- [ ] app deployed and pre-warmed, first figure under 10 seconds from a private window
- [ ] links in the first comment resolve

Cold start is the one that gets forgotten. Community Cloud sleeps an idle app, and the worst
moment for a wake-up spinner is the first minute after posting.

## Cadence, honestly

One heavy piece a week, with three in reserve before the first goes out. A piece is four to
eight hours once the reproduction is checked, and the review above is most of that time.
