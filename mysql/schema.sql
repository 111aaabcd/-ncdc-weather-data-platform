CREATE DATABASE IF NOT EXISTS weather_dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE weather_dw;

CREATE TABLE IF NOT EXISTS city_year_summary (
  city VARCHAR(32) NOT NULL,
  province VARCHAR(32) NOT NULL,
  year INT NOT NULL,
  annual_avg_temp_c DECIMAL(6,2) NOT NULL,
  annual_precip_mm DECIMAL(10,2) NOT NULL,
  valid_days INT NOT NULL,
  PRIMARY KEY (city, year)
);

