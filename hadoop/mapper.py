#!/usr/bin/env python
"""Hadoop Streaming mapper: daily CSV -> monthly aggregation key/value rows."""

import csv
import sys


def main() -> None:
    reader = csv.DictReader(sys.stdin)
    for row in reader:
        try:
            key = f"{row['city']}|{row['province']}|{row['year']}|{row['month']}"
            has_precip = bool(row["precip_mm"])
            values = [
                float(row["temp_c"]),
                float(row["min_c"]) if row["min_c"] else float(row["temp_c"]),
                float(row["max_c"]) if row["max_c"] else float(row["temp_c"]),
                float(row["precip_mm"]) if has_precip else 0.0,
                1 if has_precip else 0,
            ]
            print(f"{key}\t{values[0]}|{values[1]}|{values[2]}|{values[3]}|{values[4]}")
        except (KeyError, TypeError, ValueError):
            continue


if __name__ == "__main__":
    main()
