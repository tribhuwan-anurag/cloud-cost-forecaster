import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add app directory to path so imports work regardless of where you run from
sys.path.insert(0, os.path.dirname(__file__))

from ingest import get_cost_data, get_total_daily_cost, save_raw_data, load_raw_data
from forecast import build_forecast, get_month_end_prediction, flag_cost_spikes, save_forecast_chart
from classify import classify_services
from report import build_report


def run_pipeline(use_cache: bool = False):
    """
    Full pipeline:
    1. Ingest billing data from AWS Cost Explorer
    2. Run Prophet forecast
    3. Classify services
    4. Generate HTML report
    """
    start_time = datetime.now()
    print("=" * 50)
    print("  AWS Cloud Cost Forecaster")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Paths — always relative to project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir     = os.path.join(project_root, "data")
    cache_path   = os.path.join(data_dir, "raw_costs.csv")
    chart_path   = os.path.join(data_dir, "forecast_chart.png")
    report_path  = os.path.join(data_dir, "report.html")

    os.makedirs(data_dir, exist_ok=True)

    # Step 1 — Ingest
    print("\n[1/4] Ingesting cost data...")
    if use_cache and os.path.exists(cache_path):
        print("  Using cached data (pass use_cache=False to refresh)")
        df = load_raw_data(cache_path)
    else:
        df = get_cost_data(days_back=90)
        save_raw_data(df, cache_path)

    daily = get_total_daily_cost(df)

    # Step 2 — Forecast
    print("\n[2/4] Running forecast...")
    model, forecast  = build_forecast(daily, forecast_days=30)
    prediction       = get_month_end_prediction(forecast)
    spikes           = flag_cost_spikes(forecast, daily)
    save_forecast_chart(model, forecast, chart_path)

    print(f"  Month-end prediction: ${prediction['predicted']:.4f}")
    print(f"  Range: ${prediction['lower']:.4f} - ${prediction['upper']:.4f}")

    # Step 3 — Classify
    print("\n[3/4] Classifying services...")
    classified = classify_services(df)
    idle_count    = len(classified[classified["status"] == "idle"])
    rising_count  = len(classified[classified["status"] == "rising"])
    print(f"  {len(classified)} services | {idle_count} idle | {rising_count} rising")

    # Step 4 — Report
    print("\n[4/4] Generating report...")
    account_id = os.getenv("AWS_ACCOUNT_ID", "unknown")
    build_report(
        classified_df=classified,
        forecast_df=forecast,
        prediction=prediction,
        spikes_df=spikes,
        chart_path=chart_path,
        output_path=report_path,
        account_id=account_id
    )

    elapsed = (datetime.now() - start_time).seconds
    print("\n" + "=" * 50)
    print(f"  Pipeline complete in {elapsed}s")
    print(f"  Report: {report_path}")
    print("=" * 50)

    return report_path


if __name__ == "__main__":
    # Pass --cache flag to skip API call and use existing data
    use_cache = "--cache" in sys.argv
    run_pipeline(use_cache=use_cache)