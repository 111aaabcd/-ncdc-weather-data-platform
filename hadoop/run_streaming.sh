#!/usr/bin/env bash
set -euo pipefail

: "${HADOOP_HOME:?Set HADOOP_HOME first}"

INPUT="${1:-/weather/input/weather_daily.csv}"
OUTPUT="${2:-/weather/output/monthly_summary}"
STREAMING_JAR="$(find "$HADOOP_HOME" -name 'hadoop-streaming-*.jar' | head -n 1)"

hdfs dfs -rm -r -f "$OUTPUT" >/dev/null 2>&1 || true
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.job.name=ncdc-weather-monthly-etl \
  -files hadoop/mapper.py,hadoop/reducer.py \
  -input "$INPUT" \
  -output "$OUTPUT" \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py"

