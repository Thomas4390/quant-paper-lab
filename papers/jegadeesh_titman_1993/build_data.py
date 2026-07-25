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

MISSING = (-99.99, -999.0, -99.0)
_MONTH_ROW = re.compile(r"^\s*(\d{6})\s*,")


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


def first_monthly_table(text: str) -> pd.DataFrame:
    """Extract the first monthly table from a Ken French CSV.

    These files stack several tables separated by blank lines: value weighted monthly
    first, then equal weighted, then annual, then firm counts. The first one is the one we
    want. A table is a header line starting with a comma, followed by rows keyed YYYYMM.
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
        header = [c.strip() for c in line.split(",")][1:]
        frame = pd.read_csv(io.StringIO("\n".join(rows)), header=None, index_col=0)
        frame.columns = header[: frame.shape[1]]
        frame.index = pd.to_datetime(frame.index.astype(str), format="%Y%m") + pd.offsets.MonthEnd(0)
        frame.index.name = "date"
        return frame.astype("float64").replace(list(MISSING), float("nan")) / 100.0
    raise ValueError("no monthly table found, the source layout probably changed")


def build_deciles() -> pd.DataFrame:
    """Tidy frame of decile returns: date, horizon, decile (1 to 10), ret."""
    parts = []
    for key, (zip_name, _label) in HORIZONS.items():
        wide = first_monthly_table(fetch(zip_name))
        if wide.shape[1] != 10:
            raise ValueError(f"{key}: expected 10 deciles, got {wide.shape[1]}: {list(wide.columns)}")
        print(f"  {key}: {wide.shape[0]} months, {wide.index[0]:%Y-%m} to {wide.index[-1]:%Y-%m}")
        tidy = wide.set_axis(range(1, 11), axis=1).stack().rename("ret").reset_index()
        tidy.columns = ["date", "decile", "ret"]
        tidy["horizon"] = key
        parts.append(tidy)
    return pd.concat(parts, ignore_index=True)[["date", "horizon", "decile", "ret"]]


def build_size_prior() -> pd.DataFrame:
    """Tidy frame of the 5x5 size by prior-return portfolios: date, size_q, prior_q, ret.

    Ken French orders these columns size-major: the first five are the smallest size
    quintile across prior-return quintiles, and so on. We map by position rather than by
    the inconsistent column labels, and assert the count so a layout change fails loudly.
    """
    wide = first_monthly_table(fetch(SIZE_PRIOR))
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
    return pd.concat(parts, ignore_index=True)


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
