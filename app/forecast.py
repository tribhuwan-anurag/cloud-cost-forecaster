import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from prophet import Prophet
import os
import warnings
warnings.filterwarnings("ignore")

def build_forecast(daily_df: pd.DataFrame, forecast_days: int = 30) -> tuple:
    """
    Takes a DataFrame with columns [ds, y] (date, cost)
    and returns the trained model + forecast DataFrame.
    """
    print(f"Training Prophet model on {len(daily_df)} days of data...")

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.95
    )

    model.fit(daily_df)

    future = model.make_future_dataframe(periods=forecast_days)
    forecast = model.predict(future)

    print(f"Forecast complete. Predicting {forecast_days} days ahead.")
    return model, forecast


def get_month_end_prediction(forecast: pd.DataFrame) -> dict:
    """
    Extract the predicted spend for the last day of the current month.
    This is the headline number that goes in the report.
    """
    from datetime import datetime
    import calendar

    today = datetime.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    month_end = f"{today.year}-{today.month:02d}-{last_day}"

    row = forecast[forecast["ds"] == month_end]

    if row.empty:
        # fallback to last forecast row
        row = forecast.tail(1)

    result = {
        "date":       str(row["ds"].values[0])[:10],
        "predicted":  round(float(row["yhat"].values[0]), 4),
        "lower":      round(float(row["yhat_lower"].values[0]), 4),
        "upper":      round(float(row["yhat_upper"].values[0]), 4),
    }
    return result


def flag_cost_spikes(forecast: pd.DataFrame, daily_df: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
    """
    Compare actual costs against forecast upper bound.
    Flag any day where actual cost exceeded the upper confidence interval.
    These are your anomalies — unexpected cost spikes.
    """
    merged = pd.merge(
        daily_df.rename(columns={"ds": "date", "y": "actual"}),
        forecast[["ds", "yhat", "yhat_upper"]].rename(columns={"ds": "date"}),
        on="date"
    )

    merged["is_spike"] = merged["actual"] > (merged["yhat_upper"] * threshold)
    spikes = merged[merged["is_spike"]].copy()

    if spikes.empty:
        print("No cost spikes detected.")
    else:
        print(f"Detected {len(spikes)} cost spike(s):")
        print(spikes[["date", "actual", "yhat", "yhat_upper"]].to_string())

    return spikes


def save_forecast_chart(model, forecast: pd.DataFrame, path: str = "data/forecast_chart.png"):
    """Generate and save the forecast chart as a PNG for the report."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 5))

    # Plot actuals
    ax.plot(
        forecast["ds"].iloc[:-30],
        forecast["yhat"].iloc[:-30],
        color="#2196F3",
        linewidth=1.5,
        label="Historical trend"
    )

    # Plot forecast
    ax.plot(
        forecast["ds"].iloc[-30:],
        forecast["yhat"].iloc[-30:],
        color="#FF9800",
        linewidth=2,
        linestyle="--",
        label="Forecast (next 30 days)"
    )

    # Confidence interval
    ax.fill_between(
        forecast["ds"].iloc[-30:],
        forecast["yhat_lower"].iloc[-30:],
        forecast["yhat_upper"].iloc[-30:],
        alpha=0.2,
        color="#FF9800",
        label="95% confidence interval"
    )

    ax.set_title("AWS Daily Cost Forecast", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cost (USD)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Forecast chart saved to {path}")


if __name__ == "__main__":
    from ingest import get_cost_data, get_total_daily_cost, save_raw_data, load_raw_data
    import os

    # Load from cache if available, otherwise fetch fresh
    cache_path = "data/raw_costs.csv"
    if os.path.exists(cache_path):
        print("Loading from cached data...")
        df = load_raw_data(cache_path)
    else:
        df = get_cost_data(days_back=90)
        save_raw_data(df)

    daily = get_total_daily_cost(df)

    model, forecast = build_forecast(daily, forecast_days=30)

    prediction = get_month_end_prediction(forecast)
    print(f"\n--- Month-end prediction ---")
    print(f"Date:      {prediction['date']}")
    print(f"Predicted: ${prediction['predicted']}")
    print(f"Range:     ${prediction['lower']} - ${prediction['upper']}")

    spikes = flag_cost_spikes(forecast, daily)

    save_forecast_chart(model, forecast)
    print("\nforecast.py complete.")