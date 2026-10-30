from __future__ import annotations

from pipeline.etl import aggregate_monthly, load_and_clean, write_processed
from pipeline.forecast import build_forecasts
from pipeline.load_db import load_database


def main() -> None:
    clean, stats = load_and_clean()
    monthly = aggregate_monthly(clean)
    forecasts, metrics = build_forecasts(monthly)
    write_processed(clean, monthly)
    forecasts.to_csv("data/processed/forecasts.csv", index=False, encoding="utf-8")
    metrics.to_csv("data/processed/model_metrics.csv", index=False, encoding="utf-8")
    load_database(clean, monthly, forecasts, metrics, stats)
    print(
        f"ETL complete: raw={stats.raw_rows:,}, clean={stats.clean_rows:,}, "
        f"rejected={stats.rejected_rows:,}, monthly={len(monthly):,}, forecasts={len(forecasts):,}"
    )
    print(metrics.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

