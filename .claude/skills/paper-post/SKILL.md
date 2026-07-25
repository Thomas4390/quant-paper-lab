---
name: paper-post
description: Use when producing a LinkedIn post from a research paper in this repo, from picking the paper to the pre-flight before publishing. Covers the data licence gate, the reproduction check, the app page, the MP4 render and the copy. Trigger on "new paper", "next post", "prepare the momentum post", or any work inside papers/.
---

# One paper, one post

The pipeline turns a paper into three artifacts: a page in the app, an MP4 for the feed, and
the copy. They ship together or not at all. Work the steps in order. Each one has a gate that
can send you back to step one, and the earliest gate is the cheapest.

## Step 1. Pick the paper, then kill it early

Before writing any code, answer one question: **can this be reproduced on data that may live
in a public repo?**

- Free and fine: Kenneth R. French Data Library, FRED, Stooq, Yahoo, public CBOE files.
- Never in this repo: CRSP, WRDS, OptionMetrics, or anything under a vendor licence. That
  includes the 491 GB of option chains on the local volume. Derived aggregates from licensed
  data may be publishable, but only after reading that vendor's terms, and the burden of
  proof is on the paper, not on the reader.
- The survivorship trap: a current-listings universe cannot reproduce a cross-sectional sort.
  The bottom decile of any loser portfolio is full of names that later delisted. If the only
  available universe is a present-day snapshot, the paper is out.

If the answer is no, pick another paper. A reproduction on the wrong data is worse than no
post, because a quant audience will find it.

## Step 2. Scaffold and declare

Run `/new-paper <slug_with_underscores>`, then fill `paper.yaml` completely. The `claims`
list is the contract: **every number that will appear in the post has to be there, tied to
the figure or the stat tile that shows it.** Write the claims before the figures. It stops
the post from drifting into things the data does not support.

`method_notes` states how the reproduction differs from the original construction. There is
always a difference. Naming it is what separates a reproduction from a hand wave.

## Step 3. Build the data offline

`build_data.py` downloads, computes and writes parquet into `data/`. It runs by hand, never
at request time. Raw downloads go to `data/raw/`, which git ignores. Only derived series are
committed, and they stay small.

Run it, then read the printed diagnostics. A layout change at the source should raise, not
silently produce a shorter table.

## Step 4. Check the reproduction before drawing anything

Add the assertions to `tests/` first: sign, order of magnitude against the published table,
coverage. Wide bounds, because Ken French revises history and an exact figure would go red
every month. If a test is red, the pipeline is wrong. Do not move the threshold.

Then look at the numbers by hand once. The interesting story is usually not the headline
result. For momentum it was the sign flipping with the horizon and the premium dying after
2009, neither of which is the abstract of the paper.

## Step 5. Figures, then the page

`figures.py` returns Plotly figures and knows nothing about Streamlit or about video. It is
the single source of visual truth, which is what keeps the app and the MP4 from drifting.

Encoding rules, already decided, do not re-litigate per paper:

- Rank and other ordered dimensions take the ordered ramp, amber to gray to emerald.
- Anything that can flip sign uses `theme.DIVERGING` with `cmid=0`.
- One measure means one axis. Never two y scales.
- Two or more series get a legend, or direct labels on the ones that matter.
- A number that only needs to be read once is a stat tile, not a chart.

Verify by exporting a PNG and looking at it. `fig.write_image(...)` with the render group
installed. Do not judge a figure from the code.

## Step 6. Render the video, not a GIF

**LinkedIn does not animate GIFs in the feed.** An uploaded animated GIF is flattened to its
first frame. The asset is a native MP4. The GIF that `animate.py` also writes is for the
README, for X and for the site.

Targets: 1200 by 1200, 12 fps, 10 to 15 seconds, no audio track, all labels burned in,
readable on a phone. Axes fixed from the first frame, colour and height scales frozen across
frames. An animation whose axis rescales is a lie about the data.

Iterate with `--preview <year>` on a single frame before rendering the whole clip.

## Step 7. Copy

Write `post.md`. Hook in the first two lines, before the fold. Numbers straight from the
claims. The caveat is not buried, it is the part that earns trust with this audience.

House voice: sober, precise, warm without being chatty. No buzzwords. **No em-dashes and no
semicolons**, in the post and in anything the app displays. Pass the draft through the
`humanize-writing` skill. Link goes in the first comment, not the body.

## Step 8. Pre-flight, then publish

Nothing ships until all of this is true:

- [ ] `uv run --group dev pytest -q` green
- [ ] every claim in the post traced to `paper.yaml`
- [ ] data licence checked and named in `paper.yaml`
- [ ] disclaimer visible on the page
- [ ] `published` set in `paper.yaml`, then `uv run python -m lab.manifest`
- [ ] MP4 probed: square, no audio, 10 to 15 seconds
- [ ] MP4 watched once, muted, at phone size
- [ ] app deployed and pre-warmed, first figure under 10 seconds from a private window
- [ ] links in the first comment resolve

Cold start is the one that gets forgotten. Community Cloud sleeps an idle app, and the worst
possible moment for a wake-up spinner is the first minute after posting.

## Cadence, honestly

One heavy piece a week is the sustainable rate, with three in reserve before the first one
goes out. A piece is four to eight hours once the reproduction is checked. Batch the
production, publish on a schedule, and keep light posts for the weeks in between.
