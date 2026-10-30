from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.config import PROCESSED_DIR, RAW_DIR, STATIONS


@dataclass
class EtlStats:
    raw_rows: int
    clean_rows: int
    rejected_rows: int


def fahrenheit_to_celsius(values: pd.Series) -> pd.Series:
    return (values - 32.0) * 5.0 / 9.0


def load_and_clean(raw_dir: Path = RAW_DIR) -> tuple[pd.DataFrame, EtlStats]:
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No NOAA CSV files found in {raw_dir}")

    frames = []
    raw_rows = 0
    for path in files:
        frame = pd.read_csv(path, dtype={"STATION": str})
        raw_rows += len(frame)
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    data["date"] = pd.to_datetime(data["DATE"], errors="coerce")
    for column in ["TEMP", "MAX", "MIN", "PRCP", "LATITUDE", "LONGITUDE"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["TEMP"] = data["TEMP"].mask(data["TEMP"] >= 9999)
    data["MAX"] = data["MAX"].mask(data["MAX"] >= 9999)
    data["MIN"] = data["MIN"].mask(data["MIN"] >= 9999)
    data["PRCP"] = data["PRCP"].mask(data["PRCP"] >= 99)

    data["temp_c"] = fahrenheit_to_celsius(data["TEMP"])
    data["max_c"] = fahrenheit_to_celsius(data["MAX"])
    data["min_c"] = fahrenheit_to_celsius(data["MIN"])
    data["precip_mm"] = data["PRCP"] * 25.4
    data["city"] = data["STATION"].map(lambda value: STATIONS.get(value, {}).get("city"))
    data["province"] = data["STATION"].map(lambda value: STATIONS.get(value, {}).get("province"))

    required = data["date"].notna() & data["city"].notna() & data["temp_c"].between(-80, 60)
    sane_extremes = (
        (data["max_c"].isna() | data["max_c"].between(-80, 65))
        & (data["min_c"].isna() | data["min_c"].between(-90, 60))
        & (data["precip_mm"].isna() | data["precip_mm"].between(0, 1000))
    )
    clean = data.loc[required & sane_extremes].copy()
    clean = clean.drop_duplicates(subset=["STATION", "date"], keep="last")
    clean = clean.sort_values(["city", "date"])

    clean["year"] = clean["date"].dt.year
    clean["month"] = clean["date"].dt.month
    clean["quality_flags"] = np.where(clean["precip_mm"].isna(), "missing_precip", "ok")
    clean = clean.rename(
        columns={"STATION": "station", "LATITUDE": "latitude", "LONGITUDE": "longitude"}
    )
    columns = [
        "station", "city", "province", "date", "year", "month", "latitude", "longitude",
        "temp_c", "min_c", "max_c", "precip_mm", "quality_flags",
    ]
    clean = clean[columns]

    stats = EtlStats(raw_rows=raw_rows, clean_rows=len(clean), rejected_rows=raw_rows - len(clean))
    return clean, stats


def aggregate_monthly(clean: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        clean.groupby(["city", "province", "year", "month"], as_index=False)
        .agg(
            avg_temp_c=("temp_c", "mean"),
            min_temp_c=("min_c", "min"),
            max_temp_c=("max_c", "max"),
            precip_mm=("precip_mm", lambda values: values.sum(min_count=1)),
            precip_days=("precip_mm", "count"),
            valid_days=("temp_c", "count"),
        )
        .sort_values(["city", "year", "month"])
    )
    return monthly


def write_processed(clean: pd.DataFrame, monthly: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    daily = clean.copy()
    daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
    daily.to_csv(PROCESSED_DIR / "weather_daily.csv", index=False, encoding="utf-8")
    monthly.to_csv(PROCESSED_DIR / "monthly_summary.csv", index=False, encoding="utf-8")
