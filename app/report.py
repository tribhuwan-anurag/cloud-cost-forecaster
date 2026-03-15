import pandas as pd
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import base64


def build_report(
    classified_df: pd.DataFrame,
    forecast_df:   pd.DataFrame,
    prediction:    dict,
    spikes_df:     pd.DataFrame,
    chart_path:    str = "data/forecast_chart.png",
    output_path:   str = "data/report.html",
    account_id:    str = "unknown"
) -> str:
    """
    Render the Jinja2 HTML template with all the data we've collected
    and save it as a standalone HTML report.
    """

    # Embed chart as base64 so the HTML file is fully self-contained
    chart_b64 = ""
    if os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            chart_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode()

    # Build template context
    services = classified_df.to_dict(orient="records")

    spikes = []
    if not spikes_df.empty:
        spikes = spikes_df[["date", "actual", "yhat", "yhat_upper"]].copy()
        spikes["date"] = spikes["date"].astype(str).str[:10]
        spikes = spikes.to_dict(orient="records")

    context = {
        "report_date":   datetime.today().strftime("%B %d, %Y"),
        "account_id":    account_id,
        "total_cost":    classified_df["total_cost"].sum(),
        "service_count": len(classified_df),
        "prediction":    prediction,
        "spike_count":   len(spikes),
        "services":      services,
        "spikes":        spikes,
        "chart_path":    chart_b64,
    }

    # Load and render template
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html.j2")
    html = template.render(**context)

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Report saved to {output_path}")
    return output_path


if __name__ == "__main__":
    from ingest import load_raw_data, get_total_daily_cost
    from forecast import build_forecast, get_month_end_prediction, flag_cost_spikes, save_forecast_chart
    from classify import classify_services

    import os
    account_id = os.getenv("AWS_ACCOUNT_ID", "unknown")

    print("Loading data...")
    df = load_raw_data("data/raw_costs.csv")
    daily = get_total_daily_cost(df)

    print("Running forecast...")
    model, forecast = build_forecast(daily, forecast_days=30)
    prediction = get_month_end_prediction(forecast)
    spikes = flag_cost_spikes(forecast, daily)
    save_forecast_chart(model, forecast)

    print("Classifying services...")
    classified = classify_services(df)

    print("Building report...")
    build_report(
        classified_df=classified,
        forecast_df=forecast,
        prediction=prediction,
        spikes_df=spikes,
        account_id=account_id
    )
    print("Done.")