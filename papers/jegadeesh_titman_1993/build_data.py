"""Build the derived series for the momentum reproduction. Run offline, never at runtime.

Source: the Kenneth R. French Data Library at Dartmouth, which is public and free.
    https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

What lands in data/ is derived and small: monthly returns for the portfolios we plot, plus
the factor series. Raw zips stay in data/raw/, which git ignores. Nothing here is a vendor
redistribution, and the app can be rebuilt from scratch by anyone running this script.

    uv run --group dev python -m papers.jegadeesh_titman_1993.build_data
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

# Formation horizons, as Ken French names them. The three together tell the story the
# single momentum sort cannot: the sign of the prior-return effect flips with the horizon.
HORIZONS = {
    "prior_1_0": ("10_Portfolios_Prior_1_0_CSV.zip", "Prior 1 month"),
    "prior_12_2": ("10_Portfolios_Prior_12_2_CSV.zip", "Prior 2 to 12 months"),
    "prior_60_13": ("10_Portfolios_Prior_60_13_CSV.zip", "Prior 13 to 60 months"),
}
SIZE_PRIOR = "25_Portfolios_ME_Prior_12_2_CSV.zip"
FACTORS = "F-F_Research_Data_Factors_CSV.zip"
MOMENTUM = "F-F_Momentum_Factor_CSV.zip"

MISSING = (-99.99, -999.0)
_MONTH_ROW = re.compile(r"^\s*(\d{6})\s*,")

# Ken French's own table titles are not uniform and contain at least one typo
# ("Aerage Value Weighted Returns"), so the label match has to be loose. It still has to
# happen: the same files also carry "Number of Firms in Portfolios" and "Average Firm Size"
# tables with the same monthly shape, and picking one of those by position would produce
# silently wrong data.
_WEIGHTING = {
    "vw": re.compile(r"value\s*weight.*monthly", re.I),
    "ew": re.compile(r"equal\s*weight.*monthly", re.I),
}


def fetch(name: str) -> str:
    """Download a Ken French zip once and return the text of the CSV inside."""
    RAW.mkdir(parents=True, exist_ok=True)
    local = RAW / name
    if not local.exists():
        print(f"  downloading {name}")
        resp = requests.get(f"{BASE}/{name}", timeout=60, headers={"User-Agent": "quant-paper-lab"})
        resp.raise_for_status()
        local.write_bytes(resp.content)
    with zipfile.ZipFile(io.BytesIO(local.read_bytes())) as zf:
        inner = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return zf.read(inner).decode("latin-1")


def monthly_blocks(text: str):
    """Yield (title, frame) for every monthly table in a Ken French CSV.

    These files stack several tables separated by blank lines. A table is a title line, a
    header line starting with a comma, then rows keyed YYYYMM.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith(","):
            continue
        rows = []
        for row in lines[i + 1 :]:
            if not _MONTH_ROW.match(row):
                break
            rows.append(row)
        if len(rows) < 120:  # a real monthly table spans decades, not a stray match
            continue

        title = next((lines[j] for j in range(i - 1, max(i - 4, -1), -1) if lines[j].strip()), "")
        header = [c.strip() for c in line.split(",")][1:]
        frame = pd.read_csv(io.StringIO("\n".join(rows)), header=None, index_col=0)
        frame.columns = header[: frame.shape[1]]
        frame.index = pd.to_datetime(frame.index.astype(str), format="%Y%m") + pd.offsets.MonthEnd(0)
        frame.index.name = "date"
        yield title, frame.astype("float64").replace(list(MISSING), float("nan")) / 100.0


def monthly_tables(text: str) -> dict[str, pd.DataFrame]:
    """The return tables of a portfolio file, keyed by weighting.

    Portfolio files carry value weighted returns, equal weighted returns, firm counts and
    average firm size, several of them with the same monthly shape. Selecting by position
    works until the source reorders and then fails silently, so each table is matched on its
    own title instead.
    """
    found: dict[str, pd.DataFrame] = {}
    for title, frame in monthly_blocks(text):
        weighting = next((key for key, pattern in _WEIGHTING.items() if pattern.search(title)), None)
        if weighting is not None and weighting not in found:
            found[weighting] = frame
    if "vw" not in found:
        raise ValueError(f"no value weighted monthly table found, layout changed: {sorted(found)}")
    return found


def first_monthly_table(text: str) -> pd.DataFrame:
    """The single monthly table of a factor file, which carries no weighting title."""
    return next(frame for _title, frame in monthly_blocks(text))


def build_deciles() -> pd.DataFrame:
    """Tidy decile returns: date, horizon, weighting, decile (1 to 10), ret.

    Both weightings are kept. Jegadeesh and Titman formed equal weighted portfolios, so the
    equal weighted series is the one that compares with their published table, while value
    weighted is the modern convention and less driven by microcaps. Publishing only one of
    them would misattribute the difference between the two.
    """
    parts = []
    for key, (zip_name, _label) in HORIZONS.items():
        tables = monthly_tables(fetch(zip_name))
        for weighting, wide in tables.items():
            if wide.shape[1] != 10:
                raise ValueError(
                    f"{key}/{weighting}: expected 10 deciles, got {wide.shape[1]}: {list(wide.columns)}"
                )
            tidy = wide.set_axis(range(1, 11), axis=1).stack().rename("ret").reset_index()
            tidy.columns = ["date", "decile", "ret"]
            tidy["horizon"] = key
            tidy["weighting"] = weighting
            parts.append(tidy)
        span = tables["vw"]
        print(
            f"  {key}: {span.shape[0]} months, {span.index[0]:%Y-%m} to {span.index[-1]:%Y-%m}, "
            f"weightings {sorted(tables)}"
        )
    return pd.concat(parts, ignore_index=True)[["date", "horizon", "weighting", "decile", "ret"]]


def build_size_prior() -> pd.DataFrame:
    """Tidy frame of the 5x5 size by prior-return portfolios: date, size_q, prior_q, ret.

    Ken French orders these columns size-major: the first five are the smallest size
    quintile across prior-return quintiles, and so on. We map by position rather than by
    the inconsistent column labels, and assert the count so a layout change fails loudly.
    """
    wide = monthly_tables(fetch(SIZE_PRIOR))["vw"]
    if wide.shape[1] != 25:
        raise ValueError(f"expected 25 portfolios, got {wide.shape[1]}")
    print(f"  size x prior: {wide.shape[0]} months, columns {list(wide.columns[:3])} ...")
    parts = []
    for pos, col in enumerate(wide.columns):
        parts.append(
            pd.DataFrame(
                {
                    "date": wide.index,
                    "size_q": pos // 5 + 1,
                    "prior_q": pos % 5 + 1,
                    "ret": wide[col].to_numpy(),
                }
            )
        )
    tidy = pd.concat(parts, ignore_index=True)
    _assert_size_major(tidy)
    return tidy


def _assert_size_major(tidy: pd.DataFrame) -> None:
    """Catch a silent size and prior transposition.

    The positional mapping is the heaviest assumption in this file and the column labels are
    too irregular to key on. Volatility falls monotonically with market capitalisation and is
    U shaped across prior return, so a transposition breaks the monotonicity. Cheap check,
    and it fires on exactly the mistake that would otherwise pass every test.
    """
    by_size = tidy.groupby("size_q").ret.std()
    if not by_size.is_monotonic_decreasing:
        raise ValueError(
            "volatility is not decreasing in size_q, the 25 portfolios are probably "
            f"transposed or reordered upstream: {by_size.round(4).to_dict()}"
        )


def build_factors() -> pd.DataFrame:
    """Market, size, value, risk-free and the momentum factor, monthly."""
    ff = first_monthly_table(fetch(FACTORS))
    ff.columns = [c.lower().replace("-", "_") for c in ff.columns]
    mom = first_monthly_table(fetch(MOMENTUM))
    mom.columns = ["mom"]
    out = ff.join(mom, how="outer")
    print(f"  factors: {out.shape[0]} months, {out.index[0]:%Y-%m} to {out.index[-1]:%Y-%m}")
    return out.reset_index()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("building momentum data from the Ken French Data Library")
    for name, frame in (
        ("deciles.parquet", build_deciles()),
        ("size_prior_25.parquet", build_size_prior()),
        ("factors.parquet", build_factors()),
    ):
        path = OUT / name
        frame.to_parquet(path, index=False)
        print(f"  wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:.0f} KB, {len(frame)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
