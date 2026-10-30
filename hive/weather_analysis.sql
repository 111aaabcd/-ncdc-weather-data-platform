CREATE DATABASE IF NOT EXISTS weather_dw;
USE weather_dw;

CREATE EXTERNAL TABLE IF NOT EXISTS monthly_weather_raw (
  city STRING,
  province STRING,
  year INT,
  month INT,
  avg_temp_c DOUBLE,
  min_temp_c DOUBLE,
  max_temp_c DOUBLE,
  precip_mm DOUBLE,
  precip_days INT,
  valid_days INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '|'
STORED AS TEXTFILE
LOCATION '/weather/output/monthly_hive';

CREATE TABLE IF NOT EXISTS city_year_summary
STORED AS ORC
AS
SELECT
  city,
  province,
  year,
  ROUND(AVG(avg_temp_c), 2) AS annual_avg_temp_c,
  ROUND(SUM(precip_mm), 2) AS annual_precip_mm,
  SUM(valid_days) AS valid_days
FROM monthly_weather_raw
GROUP BY city, province, year;

CREATE TABLE IF NOT EXISTS city_month_extremes
STORED AS ORC
AS
SELECT city, province, year, month, min_temp_c, max_temp_c
FROM monthly_weather_raw;
