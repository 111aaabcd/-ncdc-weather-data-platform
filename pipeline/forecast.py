from __future__ import annotations

import math

import numpy as np
import pandas as pd


HARMONIC = "harmonic_trend_regression_v1"
MONTH_DUMMY = "month_dummy_trend_regression_v1"
SEASONAL_NAIVE = "seasonal_naive_v1"
BLEND = "harmonic_seasonal_blend_v1"


def _design_matrix(index: np.ndarray) -> np.ndarray:
    radians = 2.0 * np.pi * index / 12.0
    return np.column_stack(
        [
            np.ones(len(index)),
            index,
            np.sin(radians),
            np.cos(radians),
            np.sin(2 * radians),
            np.cos(2 * radians),
        ]
    )


def _fit_predict_harmonic(train: np.ndarray, horizon: int) -> np.ndarray:
    train_index = np.arange(len(train), dtype=float)
    coefficients, *_ = np.linalg.lstsq(_design_matrix(train_index), train, rcond=None)
    predict_index = np.arange(len(train), len(train) + horizon, dtype=float)
    return _design_matrix(predict_index) @ coefficients


def _month_dummy_matrix(index: np.ndarray) -> np.ndarray:
    month = index.astype(int) % 12
    dummies = np.column_stack([(month == value).astype(float) for value in range(1, 12)])
    return np.column_stack([np.ones(len(index)), index, dummies])


def _fit_predict_month_dummy(train: np.ndarray, horizon: int) -> np.ndarray:
    train_index = np.arange(len(train), dtype=float)
    coefficients, *_ = np.linalg.lstsq(_month_dummy_matrix(train_index), train, rcond=None)
    predict_index = np.arange(len(train), len(train) + horizon, dtype=float)
    return _month_dummy_matrix(predict_index) @ coefficients


def _predict_seasonal_naive(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) < 12:
        raise ValueError("Seasonal naive requires at least 12 months")
    repeats = int(math.ceil(horizon / 12))
    return np.tile(train[-12:], repeats)[:horizon]


def _predict(model: str, train: np.ndarray, horizon: int) -> np.ndarray:
    if model == HARMONIC:
        return _fit_predict_harmonic(train, horizon)
    if model == MONTH_DUMMY:
        return _fit_predict_month_dummy(train, horizon)
    if model == SEASONAL_NAIVE:
        return _predict_seasonal_naive(train, horizon)
    if model == BLEND:
        return 0.5 * _fit_predict_harmonic(train, horizon) + 0.5 * _predict_seasonal_naive(train, horizon)
    raise ValueError(f"Unknown model: {model}")


def build_forecasts(monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    forecast_rows = []
    metric_rows = []

    for city, city_frame in monthly.groupby("city"):
        city_frame = city_frame.sort_values(["year", "month"]).copy()
        values = city_frame["avg_temp_c"].to_numpy(dtype=float)
        if len(values) < 36:
            raise ValueError(f"{city} has only {len(values)} months; at least 36 are required")

        # 2019-2022 train, 2023 validation for model choice, 2024 untouched test.
        selection_train = values[:-24]
        validation = values[-24:-12]
        candidates = [HARMONIC, MONTH_DUMMY, SEASONAL_NAIVE, BLEND]
        validation_mae = {
            model: float(np.mean(np.abs(validation - _predict(model, selection_train, 12))))
            for model in candidates
        }
        selected_model = min(validation_mae, key=validation_mae.get)

        test_train = values[:-12]
        actual = values[-12:]
        predicted = _predict(selected_model, test_train, 12)
        seasonal_naive = _predict(SEASONAL_NAIVE, test_train, 12)

        errors = actual - predicted
        mae = float(np.mean(np.abs(errors)))
        rmse = float(math.sqrt(np.mean(np.square(errors))))
        baseline_mae = float(np.mean(np.abs(actual - seasonal_naive)))

        dates = pd.to_datetime(
            city_frame["year"].astype(str) + "-" + city_frame["month"].astype(str).str.zfill(2) + "-01"
        )
        metric_rows.append(
            {
                "city": city,
                "model": selected_model,
                "train_end": dates.iloc[-13].strftime("%Y-%m"),
                "test_start": dates.iloc[-12].strftime("%Y-%m"),
                "test_end": dates.iloc[-1].strftime("%Y-%m"),
                "mae_c": mae,
                "rmse_c": rmse,
                "baseline_mae_c": baseline_mae,
            }
        )

        full_predictions = _predict(selected_model, values, 12)
        last_month = dates.iloc[-1]
        for step, estimate in enumerate(full_predictions, start=1):
            target = last_month + pd.DateOffset(months=step)
            forecast_rows.append(
                {
                    "city": city,
                    "target_month": target.strftime("%Y-%m"),
                    "forecast_temp_c": float(estimate),
                    "model": selected_model,
                }
            )

    return pd.DataFrame(forecast_rows), pd.DataFrame(metric_rows)
