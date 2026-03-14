import pandas as pd
from scripts.postgre_utils import get_sqlalchemy_engine
from . import queries
from .config import OUTPUT_DIR


def save_csv(df, name):
    path = OUTPUT_DIR / f"{name}.csv"

    if path.exists():
        path.unlink()   # delete old table

    df.to_csv(path, index=False)

    print(f"Saved {name}.csv")


def run_analytics_pipeline():
    engine = get_sqlalchemy_engine()

    queries_dict = {
        "airline_performance": queries.AIRLINE_PERFORMANCE,
        "airport_departure_delays": queries.AIRPORT_DEPARTURE_DELAYS,
        "airport_arrival_delays": queries.AIRPORT_ARRIVAL_DELAYS,
        "delay_by_day": queries.DELAY_BY_DAY,
        "delay_by_time_bucket": queries.DELAY_BY_TIME_BUCKET,
        "route_performance": queries.ROUTE_PERFORMANCE,
        "route_time_day_analysis": queries.ROUTE_TIME_DAY
    }

    for name, query in queries_dict.items():
        df = pd.read_sql(query, engine)
        save_csv(df, name)

    print("\nAnalytics tables generated successfully.")


if __name__ == "__main__":
    run_analytics_pipeline()