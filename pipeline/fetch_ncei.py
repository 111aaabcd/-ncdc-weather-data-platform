"""Download reproducible GSOD CSV files from NOAA/NCEI.

The repository already includes the 2019-2024 sample used by the demo. Run this
script only when refreshing the source files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen

from pipeline.config import RAW_DIR, STATIONS

BASE_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"


def download(years: range, destination: Path = RAW_DIR) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for year in years:
        for station in STATIONS:
            target = destination / f"{station}-{year}.csv"
            url = f"{BASE_URL}/{year}/{station}.csv"
            print(f"GET {url}")
            with urlopen(url, timeout=60) as response:
                target.write_bytes(response.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=2019)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()
    download(range(args.start, args.end + 1))

