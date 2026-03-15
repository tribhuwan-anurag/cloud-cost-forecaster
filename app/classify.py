import pandas as pd
from datetime import datetime, timedelta


def classify_services(df: pd.DataFrame, idle_threshold: float = 0.01, idle_days: int = 7) -> pd.DataFrame:
    """
    Classify each service as:
      - active:       spending meaningfully in the last 7 days
      - idle:         tiny or zero spend for 7+ days (candidate for shutdown)
      - new:          only appeared recently
      - rising:       cost trending up week over week
      - falling:      cost trending down week over week
    """
    today = df["date"].max()
    last_7  = today - timedelta(days=7)
    last_14 = today - timedelta(days=14)

    results = []

    for service, group in df.groupby("service"):
        group = group.sort_values("date")

        total_cost     = group["cost"].sum()
        recent_7_days  = group[group["date"] >= last_7]["cost"].sum()
        prior_7_days   = group[(group["date"] >= last_14) & (group["date"] < last_7)]["cost"].sum()
        avg_daily_cost = group["cost"].mean()
        last_seen      = group[group["cost"] > 0]["date"].max()

        # Determine trend
        if prior_7_days == 0 and recent_7_days > 0:
            trend = "new"
        elif prior_7_days == 0:
            trend = "stable"
        else:
            change_pct = ((recent_7_days - prior_7_days) / prior_7_days) * 100
            if change_pct > 20:
                trend = "rising"
            elif change_pct < -20:
                trend = "falling"
            else:
                trend = "stable"

        # Determine status
        if recent_7_days <= idle_threshold:
            status = "idle"
        elif trend == "rising":
            status = "rising"
        else:
            status = "active"

        results.append({
            "service":        service,
            "status":         status,
            "trend":          trend,
            "total_cost":     round(total_cost, 4),
            "last_7d_cost":   round(recent_7_days, 4),
            "prior_7d_cost":  round(prior_7_days, 4),
            "avg_daily_cost": round(avg_daily_cost, 6),
            "last_seen":      str(last_seen)[:10] if pd.notna(last_seen) else "never",
        })

    result_df = pd.DataFrame(results).sort_values("total_cost", ascending=False)
    return result_df


def get_idle_services(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Return only the services flagged as idle — these are shutdown candidates."""
    return classified_df[classified_df["status"] == "idle"].copy()


def get_rising_services(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Return services with rising costs — these need attention."""
    return classified_df[classified_df["status"] == "rising"].copy()


def print_classification_report(classified_df: pd.DataFrame):
    """Print a human-readable summary to the terminal."""
    print("\n=== Service Classification Report ===")
    print(f"Total services tracked: {len(classified_df)}")
    print(f"Active:  {len(classified_df[classified_df['status'] == 'active'])}")
    print(f"Idle:    {len(classified_df[classified_df['status'] == 'idle'])}")
    print(f"Rising:  {len(classified_df[classified_df['status'] == 'rising'])}")
    print()

    for _, row in classified_df.iterrows():
        status_icon = {
            "active":  "✓",
            "idle":    "⚠",
            "rising":  "↑",
            "falling": "↓",
        }.get(row["status"], "-")

        print(
            f"{status_icon} {row['service']:<45} "
            f"${row['total_cost']:>8.4f} total  |  "
            f"${row['last_7d_cost']:>7.4f} last 7d  |  "
            f"{row['status']}"
        )


if __name__ == "__main__":
    from ingest import load_raw_data

    df = load_raw_data("data/raw_costs.csv")
    classified = classify_services(df)

    print_classification_report(classified)

    idle = get_idle_services(classified)
    if not idle.empty:
        print(f"\n--- Idle services (shutdown candidates) ---")
        print(idle[["service", "last_7d_cost", "last_seen"]].to_string())

    rising = get_rising_services(classified)
    if not rising.empty:
        print(f"\n--- Rising cost services (need attention) ---")
        print(rising[["service", "last_7d_cost", "prior_7d_cost"]].to_string())

    classified.to_csv("data/classified_services.csv", index=False)
    print("\nSaved classification to data/classified_services.csv")