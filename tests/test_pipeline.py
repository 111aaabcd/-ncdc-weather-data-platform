import csv
import io
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.config import DB_PATH, PROCESSED_DIR
from pipeline.etl import aggregate_monthly, load_and_clean
from pipeline.forecast import build_forecasts


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean, cls.stats = load_and_clean()
        cls.monthly = aggregate_monthly(cls.clean)

    def test_clean_data_has_expected_coverage(self):
        self.assertGreater(self.stats.clean_rows, 15000)
        self.assertEqual(self.clean["city"].nunique(), 8)
        self.assertEqual(int(self.clean["year"].min()), 2019)
        self.assertEqual(int(self.clean["year"].max()), 2024)
        self.assertTrue(self.clean["temp_c"].between(-80, 60).all())

    def test_monthly_grain_is_unique(self):
        self.assertFalse(self.monthly.duplicated(["city", "year", "month"]).any())
        self.assertGreaterEqual(len(self.monthly), 8 * 12 * 5)

    def test_forecast_has_backtest_metrics(self):
        forecasts, metrics = build_forecasts(self.monthly)
        self.assertEqual(len(forecasts), 8 * 12)
        self.assertEqual(len(metrics), 8)
        self.assertTrue(np.isfinite(metrics["mae_c"]).all())
        self.assertTrue((metrics["mae_c"] < 5.0).all())

    def test_streaming_mapper_reducer_matches_monthly_sample(self):
        sample = self.clean[(self.clean["city"] == "北京") & (self.clean["year"] == 2024)].copy()
        sample["date"] = sample["date"].dt.strftime("%Y-%m-%d")
        buffer = io.StringIO()
        sample.to_csv(buffer, index=False)
        mapper = subprocess.run(
            [sys.executable, str(ROOT / "hadoop" / "mapper.py")],
            input=buffer.getvalue(), text=True, capture_output=True, check=True,
        )
        sorted_map = "\n".join(sorted(mapper.stdout.splitlines())) + "\n"
        reducer = subprocess.run(
            [sys.executable, str(ROOT / "hadoop" / "reducer.py")],
            input=sorted_map, text=True, capture_output=True, check=True,
        )
        self.assertEqual(len(reducer.stdout.strip().splitlines()), 12)
        self.assertIn("北京|北京|2024|1", reducer.stdout)


class DatabaseTests(unittest.TestCase):
    def test_database_created_by_pipeline(self):
        self.assertTrue(DB_PATH.exists())
        with sqlite3.connect(DB_PATH) as connection:
            observation_count = connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            forecast_count = connection.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
        self.assertGreater(observation_count, 15000)
        self.assertEqual(forecast_count, 96)


if __name__ == "__main__":
    unittest.main()

