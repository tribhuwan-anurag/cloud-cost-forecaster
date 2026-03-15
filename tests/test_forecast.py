import pandas as pd
import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from forecast import get_month_end_prediction, flag_cost_spikes, build_forecast
from classify import classify_services


def make_daily_df(days: int = 60, base_cost: float = 0.05) -> pd.DataFrame:
    """Helper — create a synthetic daily cost DataFrame."""
    dates = [datetime.today() - timedelta(days=i) for i in range(days, 0, -1)]
    costs = [base_cost + (i % 7) * 0.01 for i in range(days)]
    return pd.DataFrame({"ds": pd.to_datetime(dates), "y": costs})


def make_service_df() -> pd.DataFrame:
    """Helper — create a synthetic per-service DataFrame."""
    dates = pd.date_range(end=datetime.today(), periods=30)
    rows = []
    for d in dates:
        rows.append({"date": d, "service": "EC2", "cost": 0.05})
        rows.append({"date": d, "service": "S3", "cost": 0.001})
        rows.append({"date": d, "service": "Idle Service", "cost": 0.0})
    return pd.DataFrame(rows)


def test_build_forecast_returns_correct_shape():
    daily = make_daily_df(60)
    model, forecast = build_forecast(daily, forecast_days=30)
    assert len(forecast) == 60 + 30
    assert "yhat" in forecast.columns
    assert "yhat_lower" in forecast.columns
    assert "yhat_upper" in forecast.columns


def test_month_end_prediction_keys():
    daily = make_daily_df(60)
    _, forecast = build_forecast(daily, forecast_days=30)
    result = get_month_end_prediction(forecast)
    assert "predicted" in result
    assert "lower" in result
    assert "upper" in result
    assert "date" in result


def test_month_end_prediction_is_positive():
    daily = make_daily_df(60)
    _, forecast = build_forecast(daily, forecast_days=30)
    result = get_month_end_prediction(forecast)
    assert result["predicted"] >= 0


def test_flag_cost_spikes_returns_dataframe():
    daily = make_daily_df(60)
    _, forecast = build_forecast(daily, forecast_days=30)
    spikes = flag_cost_spikes(forecast, daily)
    assert isinstance(spikes, pd.DataFrame)


def test_classify_services_statuses():
    df = make_service_df()
    result = classify_services(df)
    assert set(result.columns) >= {"service", "status", "total_cost"}
    statuses = set(result["status"].unique())
    assert statuses.issubset({"active", "idle", "rising", "falling", "stable"})


def test_classify_idle_service():
    df = make_service_df()
    result = classify_services(df)
    idle = result[result["service"] == "Idle Service"]
    assert len(idle) == 1
    assert idle.iloc[0]["status"] == "idle"