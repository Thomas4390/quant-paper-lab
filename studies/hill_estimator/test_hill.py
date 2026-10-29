"""Checks on the Hill estimator before anything is drawn from it."""

import numpy as np
import pytest

from hill import ewma_standardise, hill_alpha, rolling_hill


def naive_hill(x, k):
    """Textbook form: k / sum_{i<=k} log(X_(i) / X_(k+1)), on one sample."""
    s = np.sort(x)[::-1]
    return k / np.log(s[:k] / s[k]).sum()


def test_recovers_a_known_pareto_tail():
    rng = np.random.default_rng(0)
    x = rng.pareto(3.0, 200_000) + 1.0  # exact Pareto, alpha = 3
    k = 2_000
    a = hill_alpha(x, [k])[0]
    # Asymptotic standard error is alpha / sqrt(k), so 4 standard errors is about 0.27.
    assert abs(a - 3.0) < 4 * 3.0 / np.sqrt(k)


def test_matches_the_textbook_formula():
    rng = np.random.default_rng(1)
    x = np.abs(rng.standard_t(3, 1_000))
    ks = np.array([10, 37, 100])
    assert np.allclose(hill_alpha(x, ks), [naive_hill(x, k) for k in ks])


def test_rolling_matches_a_loop_over_windows():
    rng = np.random.default_rng(2)
    x = rng.standard_t(4, 1_500) * 0.01
    window, ks = 400, np.array([10, 25, 40])
    got = rolling_hill(x, window, ks, chunk=97)  # odd chunk exercises the seams
    want = np.array(
        [hill_alpha(x[i : i + window], ks) for i in range(len(x) - window + 1)]
    )
    assert got.shape == (len(x) - window + 1, len(ks))
    assert np.allclose(got, want)


def test_alpha_ignores_the_scale_of_the_data():
    rng = np.random.default_rng(3)
    x = np.abs(rng.standard_t(3, 2_000))
    assert np.allclose(hill_alpha(x, [50, 150]), hill_alpha(7.5 * x, [50, 150]))


def test_refuses_a_threshold_that_is_not_a_loss():
    x = np.r_[
        np.linspace(0.01, 0.05, 20), np.zeros(80)
    ]  # only 20 strictly positive losses
    with pytest.raises(ValueError, match="k too large"):
        hill_alpha(x, [25])


def test_ewma_uses_only_past_information():
    rng = np.random.default_rng(4)
    r = rng.normal(0, 0.01, 600)
    z = ewma_standardise(r)
    shocked = r.copy()
    shocked[400] = 0.5
    z2 = ewma_standardise(shocked)
    # A shock on day 400 cannot change the volatility used on or before day 400.
    assert np.allclose(z[:400], z2[:400])
    assert z2[400] > 10 * abs(z[400])
