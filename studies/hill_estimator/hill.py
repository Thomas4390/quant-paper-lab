"""Hill (1975) tail index, on one sample or on every rolling window of a series.

For losses X sorted in decreasing order, X_(1) >= X_(2) >= ...,

    alpha_hat(k) = k / sum_{i=1..k} log(X_(i) / X_(k+1))

P(X > x) decays like x^-alpha in the tail. A lower alpha means a fatter tail: a crash of a given
size is more likely. Under iid data the estimator is asymptotically normal with standard error
alpha / sqrt(k). Daily returns cluster in volatility, which leaves the estimator consistent but
widens its true interval, so that standard error is a floor, not the real uncertainty.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _hill_from_top(top: np.ndarray, ks: np.ndarray) -> np.ndarray:
    """alpha for each k, given the k_max + 1 largest values of each row, sorted descending."""
    if np.any(top[..., ks] <= 0):
        raise ValueError(
            "k too large: the threshold X_(k+1) must be a strictly positive loss"
        )
    logs = np.log(top)
    csum = np.cumsum(logs, axis=-1)
    return ks / (csum[..., ks - 1] - ks * logs[..., ks])


def hill_alpha(x: np.ndarray, ks) -> np.ndarray:
    """Hill alpha of one sample of losses, for each k in ks."""
    ks = np.asarray(ks)
    top = np.sort(np.asarray(x, dtype=float))[::-1][: ks.max() + 1]
    return _hill_from_top(top, ks)


def rolling_hill(x: np.ndarray, window: int, ks, chunk: int = 2_000) -> np.ndarray:
    """Hill alpha on every window of `window` consecutive values, shape (n - window + 1, len(ks)).

    Each window keeps only its k_max + 1 largest values (np.partition, linear time), then
    sorts those few. Windows are processed in chunks so the copy stays near chunk * window floats.
    """
    ks = np.asarray(ks)
    m = ks.max() + 1
    views = sliding_window_view(np.asarray(x, dtype=float), window)
    out = np.empty((len(views), len(ks)))
    for s in range(0, len(views), chunk):
        neg = -views[s : s + chunk]
        top = -np.sort(np.partition(neg, m - 1, axis=1)[:, :m], axis=1)
        out[s : s + chunk] = _hill_from_top(top, ks)
    return out


def ewma_standardise(r: np.ndarray, lam: float = 0.94, warmup: int = 250) -> np.ndarray:
    """Returns divided by a RiskMetrics EWMA volatility known the evening before.

    sigma2[t] = lam * sigma2[t-1] + (1 - lam) * r[t-1]^2, seeded with the variance of the
    first `warmup` days. Day t is scaled by information up to t - 1 only.
    """
    r = np.asarray(r, dtype=float)
    s2 = np.empty_like(r)
    s2[0] = r[:warmup].var()
    for t in range(1, len(r)):
        s2[t] = lam * s2[t - 1] + (1 - lam) * r[t - 1] ** 2
    return r / np.sqrt(s2)
