# Data sources, and what may be published

The gate that decides whether a paper can become a post. Answer it before writing code.

## Cleared for this repo

| Source | Covers | Notes |
| --- | --- | --- |
| [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | Factor returns, portfolios sorted on size, book to market, prior returns, investment, profitability. Monthly back to 1926, daily for most series | Free. Only derived series are committed, with the rebuild script beside them |
| [FRED](https://fred.stlouisfed.org/) | Rates, inflation, unemployment, spreads | Free, terms allow redistribution of derived series |
| [Stooq](https://stooq.com/) and Yahoo Finance | Daily index and ETF prices | Free tier, adequate for illustration, not for a cross-sectional sort |
| [CBOE public data](https://www.cboe.com/us/options/market_statistics/) | Volume, put to call ratios, VIX history | The free files only, not DataShop products |

## Not usable here

**Anything under a vendor licence.** CRSP, WRDS, OptionMetrics, DataShop and equivalents.
Redistribution is prohibited, and a public repo is redistribution.

**The local research volume.** `/run/media/thomas/New Volume/Datasets` holds roughly 491 GB
of option chains (SPX, SPY, QQQ, NVDA, TSLA, GLD, IWM, VIX, partitioned by month) plus minute
bars and a US ticker universe. It is the right data for private research and the wrong data
for this repo. Two separate reasons:

1. Licence. The chains were acquired under terms that almost certainly forbid
   redistribution. A derived aggregate that cannot be inverted back to the raw quotes may be
   publishable, but that has to be checked against the actual terms first, per source, and
   written into the paper's `paper.yaml`.
2. Survivorship. `Equities/Other/us_tickers_full_cleaned.h5` is a present-day snapshot. A
   cross-sectional sort built on it would put only surviving names in the loser decile, which
   is exactly the bias that destroys a momentum or reversal reproduction. Ken French's
   portfolios are built on the full historical universe, delistings included, which is why
   they are the source for the momentum paper and not the local data.

## Consequence for the roadmap

Papers on options microstructure, 0DTE and gamma exposure are the closest to Synerqo's actual
work and the hardest to publish. Three honest routes, in order of preference:

1. Find a public equivalent. Some option level results can be shown on VIX and on published
   CBOE aggregates.
2. Ship an explicitly labelled model. Simulate under a stated process, show the mechanism,
   and never present it as an empirical result.
3. Skip the paper. A reproduction on the wrong data is worse than no post.
