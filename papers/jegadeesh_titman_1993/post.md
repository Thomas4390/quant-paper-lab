# LinkedIn post, momentum

Asset to upload: `out/momentum-1993.mp4` (native video, autoplays muted in the feed).
Do not upload the GIF. LinkedIn flattens an animated GIF to its first frame.
Link goes in the first comment, not in the post body.

---

## Post

Jegadeesh and Titman reported in 1993 that stocks which had beaten the market over the past
year kept beating it for months afterward. They measured 1.31 percent a month between the top
and bottom deciles, on their 1965 to 1989 sample.

I rebuilt it on public Ken French data. Equal weighted, the construction they used, it comes
back at 1.33 percent a month. Value weighted, the modern convention, it comes back at 1.63
percent. That gap is the weighting, not the method, and it is the kind of thing you only see
by running both.

Three things about the result interest me more than the headline.

The sign depends on the horizon you sort on. Over the common 1931 to 2026 window, one month of
prior return reverses at minus 0.85 percent a month. A year of it continues at plus 1.03
percent. Five years of it reverses again at minus 0.42 percent. Same data, same sort, opposite
conclusion. And the one month reversal is itself a pre-1990 phenomenon. It has had the
opposite sign for the last 35 years.

The cost is not a slow bleed. April 2009 took 34 percent off the momentum factor in a single
month, its worst since 1932. And 2009 is not even the deepest hole. September 1939 was, at 78
percent below the running peak. The factor last made a new high in November 2008.

Whether it still works is a weaker claim than it looks. Since 2009 the spread averages 0.16
percent a month, against 1.56 percent over 1990 to 2008. That looks decisive until you put an
interval on it. The 95 percent interval for the recent period runs from minus 1.07 to plus
1.39, the difference between the two eras carries a p value of 0.08, and dropping March and
April 2009 alone lifts the recent average to 0.57 percent. Seventeen years is not enough data
to call it. Compounded rather than averaged, though, the long short spread has lost 47 percent
of its capital since 2009, which is the number I would actually trade against.

None of this survives costs, by the way. Charge 1.6 percent a month of round trip cost against
the 1965 to 1989 spread and it goes to zero.

I put all of it in an app so you can move the horizon, the weighting and the window yourself,
and watch the size and momentum surface deform through time. The code that builds every number
is public.

Link in the first comment.

## First comment

The app: APP_URL
The code, including the script that rebuilds the data from scratch: REPO_URL
Data: Kenneth R. French Data Library, decile portfolios, both weightings.
Educational reproduction on public data. Not the performance of any Synerqo strategy, and not
investment advice.

## Hashtags

#quantitativefinance #factorinvesting #momentum #financialengineering

## Pre-flight

- [ ] APP_URL and REPO_URL replaced with the real links
- [ ] app pre-warmed, first figure visible in under 10 seconds from a private window
- [ ] MP4 checked in the feed preview on mobile and desktop, muted
- [ ] every number above traced to a claim in paper.yaml, and every claim visible in the app
- [ ] published date in paper.yaml matches the day this goes out, manifest regenerated
