#!/usr/bin/env python
"""Hadoop Streaming reducer: aggregate average/min/max temperature and precipitation."""

import sys


def emit(key, values):
    if key is None or not values:
        return
    avg_temp = sum(item[0] for item in values) / len(values)
    min_temp = min(item[1] for item in values)
    max_temp = max(item[2] for item in values)
    precipitation = sum(item[3] for item in values)
    precip_days = sum(item[4] for item in values)
    print(f"{key}\t{avg_temp:.4f}|{min_temp:.4f}|{max_temp:.4f}|{precipitation:.4f}|{precip_days:.0f}|{len(values)}")


def main() -> None:
    current_key = None
    bucket = []
    for line in sys.stdin:
        try:
            key, raw = line.rstrip("\n").split("\t", 1)
            values = tuple(float(value) for value in raw.split("|"))
        except ValueError:
            continue
        if current_key is not None and key != current_key:
            emit(current_key, bucket)
            bucket = []
        current_key = key
        bucket.append(values)
    emit(current_key, bucket)


if __name__ == "__main__":
    main()
