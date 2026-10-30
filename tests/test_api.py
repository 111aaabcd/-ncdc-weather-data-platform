import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weather_backend.settings")

import django

django.setup()
from django.test import Client


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_health(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["observation_rows"], 15000)

    def test_summary(self):
        response = self.client.get("/api/summary/", {"city": "北京", "year": 2024})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["monthly"]), 12)
        self.assertGreaterEqual(len(payload["rankings"]), 5)
        self.assertTrue(all(item["precip_coverage"] >= 0.8 for item in payload["rankings"]))
        self.assertEqual(len(payload["forecast"]), 12)
        self.assertEqual(payload["meta"]["source"], "NOAA/NCEI Global Summary of the Day")


if __name__ == "__main__":
    unittest.main()
