from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pandas as pd

from pipeline.config import DB_PATH, SOURCE
from pipeline.etl import EtlStats


SCHEMA = """
PRAGMA journal_mode=WAL;
DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS monthly_summary;
DROP TABLE IF EXISTS forecasts;
DROP TABLE IF EXISTS model_metrics;
DROP TABLE IF EXISTS etl_runs;

CREATE TABLE observations (
    station TEXT NOT NULL,
    city TEXT NOT NULL,
    province TEXT NOT NULL,
    date TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    temp_c REAL NOT NULL,
    min_c REAL,
    max_c REAL,
    precip_mm REAL,
    quality_flags TEXT NOT NULL,
    PRIMARY KEY (station, date)
);
CREATE INDEX idx_observations_city_date ON observations(city, date);

CREATE TABLE monthly_summary (
    city TEXT NOT NULL,
    province TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    avg_temp_c REAL NOT NULL,
    min_temp_c REAL,
    max_temp_c REAL,
    precip_mm REAL,
    precip_days INTEGER NOT NULL,
    valid_days INTEGER NOT NULL,
    PRIMARY KEY (city, year, month)
);

CREATE TABLE forecasts (
    city TEXT NOT NULL,
    target_month TEXT NOT NULL,
    forecast_temp_c REAL NOT NULL,
    model TEXT NOT NULL,
    PRIMARY KEY (city, target_month, model)
);

CREATE TABLE model_metrics (
    city TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    train_end TEXT NOT NULL,
    test_start TEXT NOT NULL,
    test_end TEXT NOT NULL,
    mae_c REAL NOT NULL,
    rmse_c REAL NOT NULL,
    baseline_mae_c REAL NOT NULL
);

CREATE TABLE etl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    raw_rows INTEGER NOT NULL,
    clean_rows INTEGER NOT NULL,
    rejected_rows INTEGER NOT NULL,
    completed_at TEXT NOT NULL
);
"""


def load_database(
    clean: pd.DataFrame,
    monthly: pd.DataFrame,
    forecasts: pd.DataFrame,
    metrics: pd.DataFrame,
    stats: EtlStats,
) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA)
        daily = clean.copy()
        daily["date"] = daily["date"].dt.strftime("%Y-%m-%d")
        daily.to_sql("observations", connection, if_exists="append", index=False)
        monthly.to_sql("monthly_summary", connection, if_exists="append", index=False)
        forecasts.to_sql("forecasts", connection, if_exists="append", index=False)
        metrics.to_sql("model_metrics", connection, if_exists="append", index=False)
        connection.execute(
            "INSERT INTO etl_runs(source, raw_rows, clean_rows, rejected_rows, completed_at) VALUES (?, ?, ?, ?, ?)",
            (
                SOURCE,
                stats.raw_rows,
                stats.clean_rows,
                stats.rejected_rows,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
