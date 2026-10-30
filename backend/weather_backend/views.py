import json
import mimetypes
import sqlite3
from pathlib import Path

from django.http import FileResponse, Http404, JsonResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "weather.db"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist" / "client"


def _rows(connection, query, params=()):
    cursor = connection.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def health(_request):
    if not DB_PATH.exists():
        return JsonResponse({"status": "not_ready", "database": False}, status=503)
    with sqlite3.connect(DB_PATH) as connection:
        count = connection.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    return JsonResponse({"status": "ok", "database": True, "observation_rows": count})


def dashboard(_request):
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.exists():
        return JsonResponse(
            {"error": "Frontend build not found. Run npm run build in frontend."},
            status=503,
        )
    return FileResponse(index_path.open("rb"), content_type="text/html; charset=utf-8")


def frontend_asset(_request, asset_path):
    candidate = (FRONTEND_DIST / "assets" / asset_path).resolve()
    assets_root = (FRONTEND_DIST / "assets").resolve()
    if assets_root not in candidate.parents or not candidate.is_file():
        raise Http404("Asset not found")
    content_type, _ = mimetypes.guess_type(candidate.name)
    return FileResponse(candidate.open("rb"), content_type=content_type or "application/octet-stream")


def summary(request):
    if not DB_PATH.exists():
        return JsonResponse({"error": "Database not found. Run the pipeline first."}, status=503)

    city = request.GET.get("city", "北京")
    year = int(request.GET.get("year", "2024"))

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        known = connection.execute(
            "SELECT DISTINCT city FROM monthly_summary ORDER BY city"
        ).fetchall()
        cities = [row[0] for row in known]
        if city not in cities:
            return JsonResponse({"error": f"Unknown city: {city}", "cities": cities}, status=400)

        monthly = _rows(
            connection,
            """
            SELECT month, ROUND(avg_temp_c, 2) AS avg_temp_c,
                   ROUND(min_temp_c, 2) AS min_temp_c,
                   ROUND(max_temp_c, 2) AS max_temp_c,
                   ROUND(precip_mm, 2) AS precip_mm, precip_days, valid_days
            FROM monthly_summary
            WHERE city = ? AND year = ?
            ORDER BY month
            """,
            (city, year),
        )
        rankings = _rows(
            connection,
            """
            SELECT city, province, ROUND(AVG(avg_temp_c), 2) AS avg_temp_c,
                   ROUND(SUM(precip_mm), 2) AS precip_mm,
                   SUM(precip_days) AS precip_days,
                   SUM(valid_days) AS valid_days,
                   ROUND(1.0 * SUM(precip_days) / SUM(valid_days), 3) AS precip_coverage
            FROM monthly_summary
            WHERE year = ?
            GROUP BY city, province
            HAVING SUM(precip_days) >= 0.8 * SUM(valid_days)
               AND SUM(precip_mm) > 0
            ORDER BY avg_temp_c DESC
            """,
            (year,),
        )
        city_points = _rows(
            connection,
            """
            SELECT m.city, m.province, ROUND(AVG(m.avg_temp_c), 2) AS avg_temp_c,
                   ROUND(o.latitude, 4) AS latitude,
                   ROUND(o.longitude, 4) AS longitude
            FROM monthly_summary m
            JOIN (
                SELECT city, AVG(latitude) AS latitude, AVG(longitude) AS longitude
                FROM observations
                WHERE year = ?
                GROUP BY city
            ) o ON o.city = m.city
            WHERE m.year = ?
            GROUP BY m.city, m.province
            ORDER BY m.city
            """,
            (year, year),
        )
        forecast = _rows(
            connection,
            """
            SELECT target_month, ROUND(forecast_temp_c, 2) AS forecast_temp_c
            FROM forecasts WHERE city = ? ORDER BY target_month
            """,
            (city,),
        )
        metric = connection.execute(
            """
            SELECT model, train_end, test_start, test_end,
                   ROUND(mae_c, 3) AS mae_c,
                   ROUND(rmse_c, 3) AS rmse_c,
                   ROUND(baseline_mae_c, 3) AS baseline_mae_c
            FROM model_metrics WHERE city = ?
            """,
            (city,),
        ).fetchone()
        quality = connection.execute(
            """
            SELECT COUNT(*), MIN(date), MAX(date),
                   SUM(CASE WHEN precip_mm IS NULL THEN 1 ELSE 0 END)
            FROM observations WHERE city = ?
            """,
            (city,),
        ).fetchone()
        latest_run = connection.execute(
            "SELECT source, raw_rows, clean_rows, rejected_rows, completed_at FROM etl_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    year_avg = round(sum(row["avg_temp_c"] * row["valid_days"] for row in monthly) / max(1, sum(row["valid_days"] for row in monthly)), 2) if monthly else None
    precip_days = sum(row["precip_days"] for row in monthly)
    valid_days = sum(row["valid_days"] for row in monthly)
    precip_coverage = round(precip_days / valid_days, 3) if valid_days else 0
    precip_values = [row["precip_mm"] for row in monthly if row["precip_mm"] is not None]
    year_precip = round(sum(precip_values), 2) if precip_values and precip_coverage >= 0.8 else None
    hottest = max(monthly, key=lambda row: row["max_temp_c"]) if monthly else None
    coldest = min(monthly, key=lambda row: row["min_temp_c"]) if monthly else None

    return JsonResponse(
        {
            "meta": {
                "source": "NOAA/NCEI Global Summary of the Day",
                "city": city,
                "year": year,
                "cities": cities,
                "years": list(range(2019, 2025)),
                "temperature_unit": "°C",
                "precipitation_unit": "mm",
                "latest_etl": dict(latest_run) if latest_run else None,
            },
            "kpis": {
                "year_avg_temp_c": year_avg,
                "year_precip_mm": year_precip,
                "precip_coverage": precip_coverage,
                "hottest_month": hottest,
                "coldest_month": coldest,
                "valid_days": valid_days,
            },
            "monthly": monthly,
            "rankings": rankings,
            "city_points": city_points,
            "forecast": forecast,
            "model_metric": dict(metric) if metric else None,
            "quality": {
                "rows": quality[0],
                "start_date": quality[1],
                "end_date": quality[2],
                "missing_precipitation": quality[3],
            },
        },
        json_dumps_params={"ensure_ascii": False},
    )
