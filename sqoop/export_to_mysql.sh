#!/usr/bin/env bash
set -euo pipefail

: "${WEATHER_DB_PASSWORD:?Set WEATHER_DB_PASSWORD without putting it in source control}"

sqoop export \
  --connect "jdbc:mysql://127.0.0.1:3306/weather_dw?useUnicode=true&characterEncoding=utf8" \
  --username "${WEATHER_DB_USER:-weather_app}" \
  --password "$WEATHER_DB_PASSWORD" \
  --table city_year_summary \
  --export-dir /user/hive/warehouse/weather_dw.db/city_year_summary \
  --input-fields-terminated-by '\001' \
  --update-mode allowinsert \
  --update-key city,year \
  --num-mappers 1

