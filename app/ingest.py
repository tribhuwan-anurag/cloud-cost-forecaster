import boto3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json

load_dotenv()

def get_cost_data(days_back: int = 90) -> pd.DataFrame:
    """
    Pull daily cost data from AWS Cost Explorer for the last N days.
    Groups by SERVICE so we can see which service costs what each day.
    """
    client = boto3.client(
        "ce",
        region_name="us-east-1"
    )

    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    print(f"Fetching cost data from {start_date} to {end_date}...")

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End":   end_date
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key":  "SERVICE"
            }
        ]
    )

    rows = []
    for day in response["ResultsByTime"]:
        date = day["TimePeriod"]["Start"]
        for group in day["Groups"]:
            service = group["Keys"][0]
            cost    = float(group["Metrics"]["UnblendedCost"]["Amount"])
            rows.append({
                "date":    date,
                "service": service,
                "cost":    round(cost, 6)
            })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    print(f"Pulled {len(df)} rows across {df['service'].nunique()} services.")
    return df


def get_total_daily_cost(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse the per-service breakdown into a single total cost per day.
    This is what we feed into the forecasting model.
    """
    daily = (
        df.groupby("date")["cost"]
        .sum()
        .reset_index()
        .rename(columns={"date": "ds", "cost": "y"})
    )
    return daily


def save_raw_data(df: pd.DataFrame, path: str = "data/raw_costs.csv"):
    """Save raw cost data to CSV for caching — avoids repeated API calls."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved raw data to {path}")


def load_raw_data(path: str = "data/raw_costs.csv") -> pd.DataFrame:
    """Load previously saved data instead of hitting the API again."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


if __name__ == "__main__":
    # Run this file directly to test the ingestion
    df = get_cost_data(days_back=90)

    print("\n--- Sample of raw data ---")
    print(df.head(10).to_string())

    print("\n--- Top 5 most expensive services (total) ---")
    top = df.groupby("service")["cost"].sum().sort_values(ascending=False).head(5)
    print(top.to_string())

    save_raw_data(df)

    daily = get_total_daily_cost(df)
    print("\n--- Daily totals (first 5 rows) ---")
    print(daily.head().to_string())