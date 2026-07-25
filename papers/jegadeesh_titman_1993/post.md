# LinkedIn post, momentum

Asset to upload: `out/momentum-1993.mp4` (native video, autoplays muted in the feed).
Do not upload the GIF. LinkedIn flattens an animated GIF to its first frame.
Link goes in the first comment, not in the post body.

---

## Post

In 1993 Jegadeesh and Titman showed that stocks which had beaten the market over the past
year kept beating it for months afterward.

Sorted into ten portfolios on the prior 2 to 12 month return, the top decile earned 1.63
percent a month more than the bottom decile over their 1965 to 1989 sample. Gross of costs,
one dollar in the top decile became 16,908 dollars by 2026.

Three things about it interest me more than that headline.

The sign of the effect depends entirely on the horizon you sort on. One month of prior
return reverses, at minus 0.78 percent a month. A year of it continues, at plus 1.15
percent. Five years of it reverses again, at minus 0.42 percent. Same data, same sort,
opposite conclusion.

The cost is not a slow bleed. April 2009 took 34 percent off the momentum factor in a single
month, its worst since 1932. Anyone levered into the trade did not get to average their way
out of it.

And it stopped paying the way it used to. Since 2009 the decile spread averages 0.16 percent
a month with a Sharpe ratio of 0.06, against 1.56 percent and 0.71 over 1990 to 2008.

I rebuilt all of this on public Ken French data and put it in an app, so you can move the
horizon and the window yourself rather than take my word for it. There is a surface that
splits the effect by company size as well. Drag the ten year window through 2009 and watch
the tilt disappear.

Link in the first comment. The code that builds every number is public too.

## First comment

The app: APP_URL
The code, including the script that rebuilds the data from scratch: REPO_URL
Data: Kenneth R. French Data Library, value weighted decile portfolios.
Educational reproduction on public data. Not the performance of any Synerqo strategy, and
not investment advice.

## Hashtags

#quantitativefinance #factorinvesting #momentum #financialengineering

## Pre-flight

- [ ] APP_URL and REPO_URL replaced with the real links
- [ ] app pre-warmed, first figure visible in under 10 seconds from a private window
- [ ] MP4 checked in the feed preview on mobile and desktop, muted
- [ ] every number above traced to a claim in paper.yaml
- [ ] published date in paper.yaml matches the day this goes out, manifest regenerated
