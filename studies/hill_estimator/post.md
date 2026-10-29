# LinkedIn post, Hill estimator

Asset to upload: `out/hill/hill-sp500.mp4` (native video, autoplays muted in the feed).
Do not upload the GIF. LinkedIn flattens an animated GIF to its first frame.
The GIF `out/hill/hill-sp500.gif` is for the site, the README and X.
Link goes in the first comment, not in the post body.

Every number below comes from `python tail_numbers.py`, except the two normal-law
comparisons, which come from the check quoted under "Sources of the numbers".

---

## Post (English)

Since 1980, the S&P 500 has lost more than 5% in a single day 27 times.

A bell curve with the same volatility says it should have happened 0.05 times.

That gap has a name, a fat tail. It also has a number, the tail index α, and a 50-year-old way
to estimate it: the Hill estimator.

The idea fits in one line. Double the size of a loss, and its probability is divided by 2^α.

With α = 3, a loss twice as large is 8 times rarer.
With a bell curve, going from a 3-sigma day to a 6-sigma day makes it 1.4 million times rarer.

So lower α means a fatter tail, and more room for extreme days. Note that α measures the shape
of the losses, not their size. Double every return and α does not move.

The animation computes α on every 4-year window from 1984 to today.
→ Left to right: time.
→ Height: α. Lower is fatter.
→ Depth: how many of the worst days you call "the tail", from 2% to 10%.
The white line follows the worst 5%.

What I take from it.

1. Over the whole period, α sits between 2.6 and 2.9, depending on whether the tail is the worst
1%, 2.5% or 5% of days. Close to 3, the "cubic law" found on many equity markets.

2. Calm is not safety. In the 4 years to June 2007, α was 4.06, far above its median of 2.80.
Seventeen months later it was 1.65, the fattest tail of the whole sample. The drop holds
wherever the tail starts, from the worst 2% to the worst 10% of days.

3. Some answers depend on where the tail starts. For the 4 years to December 2019, the worst 2%
of days give α = 3.73, a thinner tail than usual. The worst 10% give 1.60, a fatter one. Same
window, opposite reading.

4. Today, α is 3.44, with a band of 2.48 to 4.39. The band includes the median, and the
comparison flips sign along the depth axis. Not a signal.

Three caveats, because they matter more than the chart.

• The band is wide. With the worst 50 days of a 4-year window, ±0.95 is the floor, and the
true uncertainty is larger since bad days cluster. Small wiggles in the line mean nothing.

• Every crash leaves the window 4 years later, and α jumps that day. When Black Monday dropped
out in October 1991, α went from 2.49 to 2.78 overnight. The tail did not change. The window did.

• Part of the fat tail is volatility clustering. Scale each day by its recent volatility and
the median α rises from 2.80 to 3.02. The animation shows raw returns.

Why 3D? Because the depth axis is the honest part. The estimate depends on where you decide
the tail starts. Showing every choice at once stops anyone from picking the one that tells
their story.

If you run a risk process, would you read a falling α as a warning, or only feed it into
stress tests?

## Post (français)

Depuis 1980, le S&P 500 a perdu plus de 5 % en une seule séance 27 fois.

Une courbe en cloche de même volatilité en prévoit 0,05.

Cet écart a un nom, une queue épaisse, et un chiffre, l'indice de queue α, que mesure
l'estimateur de Hill (1975).

L'idée tient en une ligne. Doublez la taille d'une perte, et sa probabilité est divisée par 2^α.

Avec α = 3, une perte deux fois plus grande est 8 fois plus rare.
Avec une courbe en cloche, passer d'une séance à 3 sigmas à une séance à 6 sigmas la rend
1,4 million de fois plus rare.

Un α plus bas signifie donc une queue plus épaisse, et plus de place pour les séances extrêmes.
α mesure la forme des pertes, pas leur taille. Doublez tous les rendements, α ne bouge pas.

L'animation calcule α sur chaque fenêtre de 4 ans, de 1984 à aujourd'hui.
→ De gauche à droite : le temps.
→ La hauteur : α. Plus bas, plus épais.
→ La profondeur : combien des pires séances on appelle « la queue », de 2 % à 10 %.
La ligne blanche suit les 5 % pires séances.

Ce que j'en retiens.

1. Sur toute la période, α se situe entre 2,6 et 2,9, selon que la queue désigne les 1 %, 2,5 %
ou 5 % pires séances. Proche de 3, la « loi cubique » observée sur de nombreux marchés actions.

2. Le calme n'est pas la sécurité. Sur les 4 ans finissant en juin 2007, α valait 4,06, bien
au-dessus de sa médiane de 2,80. Dix-sept mois plus tard, il valait 1,65, la queue la plus
épaisse de tout l'échantillon. La chute tient quel que soit le début de la queue, des 2 % aux
10 % pires séances.

3. Certaines réponses dépendent du début de la queue. Sur les 4 ans finissant en décembre 2019,
les 2 % pires séances donnent α = 3,73, une queue plus fine que d'habitude. Les 10 % pires
donnent 1,60, une queue plus épaisse. Même fenêtre, lecture opposée.

4. Aujourd'hui, α vaut 3,44, avec une bande de 2,48 à 4,39. La bande contient la médiane, et la
comparaison change de sens le long de l'axe de profondeur. Ce n'est pas un signal.

Trois limites, parce qu'elles comptent plus que le graphique.

• La bande est large. Avec les 50 pires séances d'une fenêtre de 4 ans, ±0,95 est un minimum,
et l'incertitude réelle est plus grande, car les mauvaises séances arrivent en grappes.

• Chaque krach sort de la fenêtre 4 ans plus tard, et α saute ce jour-là. Quand le Lundi noir
est sorti en octobre 1991, α est passé de 2,49 à 2,78 en une séance. La queue n'a pas changé.
La fenêtre, si.

• Une partie de la queue épaisse vient du regroupement de la volatilité. Divisez chaque séance
par sa volatilité récente et la médiane de α passe de 2,80 à 3,02. L'animation montre les
rendements bruts.

Pourquoi la 3D ? Parce que l'axe de profondeur est la partie honnête. L'estimation dépend de
l'endroit où l'on fait commencer la queue. Montrer tous les choix d'un coup empêche de choisir
celui qui raconte la bonne histoire.

Dans un dispositif de risque, liriez-vous un α en baisse comme une alerte, ou comme une
simple entrée de stress test ?

## First comment

Code, data download and every number: REPO_URL
Method: Hill (1975) on daily S&P 500 log losses, rolling 1,000 trading days, k from 20 to 100
worst days. The band is α ± 1.96 α/√k, which assumes independent days, so it understates the
true uncertainty.
Data: Yahoo Finance, ^GSPC daily closes, 1980 to October 2026.
Educational illustration on public data. Not investment advice.

## Hashtags

#quantitativefinance #riskmanagement #extremevaluetheory #fattails

## Sources of the numbers

| Number in the post | Value | Where it comes from |
| --- | --- | --- |
| Days with a loss above 5% since 1980 | 27 | simple return < -5%, 11,801 days |
| Expected under a normal law | 0.05 | 11,801 × P(Z > 0.05 / 0.0112) = 0.047 |
| 6-sigma vs 3-sigma rarity | 1.4 million | P(Z>3) / P(Z>6) = 1 / 7.31e-7 |
| Full-sample α, worst 1%, 2.5%, 5% (k = 118, 295, 590) | 2.84, 2.91, 2.58 | `tail_numbers.py` |
| α, window ending 2007-06-29, k = 20, 50, 100 | 5.97, 4.06, 2.96 | `tail_numbers.py` |
| Lowest α at k = 50, window ending 2008-12-01, k = 20, 50, 100 | 1.98, 1.65, 1.61 | `tail_numbers.py` |
| Median rolling α at k = 20, 100 | 3.50, 2.18 | `tail_numbers.py` |
| Median rolling α, k = 50 | 2.80 | `tail_numbers.py` |
| α, window ending 2019-12-31, k = 20, 100 | 3.73, 1.60 | `tail_numbers.py` |
| Latest α, window ending 2026-10-28, k = 20, 50, 100 | 2.94, 3.44 [2.48 to 4.39], 2.62 | `tail_numbers.py` |
| Black Monday drop-out, 1991-10-02 | 2.49 to 2.78 | `tail_numbers.py` |
| EWMA-standardised median α | 3.02 | `tail_numbers.py`, λ = 0.94 |

## Pre-flight

- [ ] REPO_URL replaced, or the line removed if the code stays private
- [ ] MP4 checked in the feed preview on mobile and desktop, muted
- [ ] `out/hill/hill-sp500-poster.png` set as the custom video thumbnail, since the MP4's
      first frame is a nearly empty chart
- [ ] GIF and MP4 labels are in English. Posting the French copy calls for a French re-render
- [ ] numbers re-run with `python tail_numbers.py` on the day of posting, since the last
      window moves every day
- [ ] no semicolon anywhere in the copy (the author's rule)
