"""Every number quoted in the post, computed from the cached S&P 500 closes.

Run: uv run --no-project --with numpy --with pandas --with pyarrow python tail_numbers.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hill import ewma_standardise, hill_alpha, rolling_hill

ROOT = Path(__file__).resolve().parents[2]
WINDOW = 1_000  # trading days, about four years
KS = np.arange(20, 101)  # the worst 2 to 10 percent of the window's days
K_READ = 50  # the worst 5 percent, the slice the post reads


def load_losses() -> pd.Series:
    close = pd.read_parquet(ROOT / "data/raw/gspc_daily.parquet")["close"]
    return -np.log(close).diff().dropna()  # daily log loss, gains are negative losses


def rolling_frame(loss: pd.Series, ks=KS, window=WINDOW) -> pd.DataFrame:
    """alpha per window, indexed by the last day of the window, one column per k."""
    a = rolling_hill(loss.to_numpy(), window, ks)
    return pd.DataFrame(a, index=loss.index[window - 1 :], columns=ks)


def main() -> None:
    loss = load_losses()
    print(
        f"days {len(loss)}  from {loss.index[0]:%Y-%m-%d} to {loss.index[-1]:%Y-%m-%d}"
    )

    for k in (118, 295, 590):  # 1, 2.5 and 5 percent of the full sample
        a = hill_alpha(loss.to_numpy(), [k])[0]
        print(
            f"full sample k={k}  alpha {a:.2f}  iid 95% CI {a - 1.96 * a / k**0.5:.2f} to {a + 1.96 * a / k**0.5:.2f}"
        )

    raw = rolling_frame(loss)
    a = raw[K_READ]
    se = a / np.sqrt(K_READ)
    print(
        f"\nrolling W={WINDOW} k={K_READ}: median {a.median():.2f}  iid SE at median {a.median() / K_READ**0.5:.2f}"
    )
    print(f"lowest  {a.min():.2f} on window ending {a.idxmin():%Y-%m-%d}")
    print(f"highest {a.max():.2f} on window ending {a.idxmax():%Y-%m-%d}")
    print(
        f"latest  {a.iloc[-1]:.2f} [{a.iloc[-1] - 1.96 * se.iloc[-1]:.2f} to {a.iloc[-1] + 1.96 * se.iloc[-1]:.2f}] on {a.index[-1]:%Y-%m-%d}"
    )
    print(f"surface range over all k: {raw.min().min():.2f} to {raw.max().max():.2f}")
    print(f"share of windows with alpha<3 at k={K_READ}: {(a < 3).mean():.0%}")

    for d in (
        "1991-12-31",
        "1999-12-31",
        "2007-06-29",
        "2009-06-30",
        "2012-12-31",
        "2017-12-29",
        "2019-12-31",
        "2020-06-30",
        "2023-12-29",
        "2024-03-28",
        "2025-06-30",
    ):
        print(f"  {d}  alpha(k={K_READ}) {a.asof(pd.Timestamp(d)):.2f}")

    # The drop-out cliff: the day 1987-10-19 leaves the window.
    i = loss.index.get_loc(pd.Timestamp("1987-10-19"))
    out_day = loss.index[i + WINDOW]
    print(
        f"\n1987-10-19 leaves the window on {out_day:%Y-%m-%d}: alpha {a.loc[:out_day].iloc[-2]:.2f} -> {a.loc[out_day]:.2f}"
    )
    i = loss.index.get_loc(pd.Timestamp("2020-03-16"))
    out_day = loss.index[i + WINDOW]
    print(
        f"2020-03-16 leaves the window on {out_day:%Y-%m-%d}: alpha {a.loc[:out_day].iloc[-2]:.2f} -> {a.loc[out_day]:.2f}"
    )

    # Robustness: the same estimate on returns scaled by yesterday's EWMA volatility.
    z = pd.Series(ewma_standardise(-loss.to_numpy()), index=loss.index).iloc[250:]
    zf = rolling_frame(-z)[K_READ]
    print(
        f"\nEWMA-standardised k={K_READ}: median {zf.median():.2f}  range {zf.min():.2f} to {zf.max():.2f}"
    )
    print(
        f"full sample standardised k=295: {hill_alpha((-z).to_numpy(), [295])[0]:.2f}"
    )


if __name__ == "__main__":
    main()
