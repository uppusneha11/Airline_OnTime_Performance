import pandas as pd
from scripts.postgre_utils import get_sqlalchemy_engine
from .config import OUTPUT_DIR
from . import queries
from .enrichment import load_lookups, enrich


def save_csv(df, name):
    path = OUTPUT_DIR / f"{name}.csv"
    if path.exists():
        path.unlink()
    df.to_csv(path, index=False)
    print(f"Saved {name}.csv")


def run_analytics_pipeline():
    engine = get_sqlalchemy_engine()
    airport_map, carrier_map, airport_info = load_lookups()

    queries_dict = {
        "airline_performance":      queries.AIRLINE_PERFORMANCE,
        "airport_departure_delays": queries.AIRPORT_DEPARTURE_DELAYS,
        "airport_arrival_delays":   queries.AIRPORT_ARRIVAL_DELAYS,
        "delay_by_day":             queries.DELAY_BY_DAY,
        "delay_by_time_bucket":     queries.DELAY_BY_TIME_BUCKET,
        "route_performance":        queries.ROUTE_PERFORMANCE,
        "route_time_day_analysis":  queries.ROUTE_TIME_DAY,
        "delay_cause_by_airline":   queries.DELAY_CAUSE_BY_AIRLINE,
        "delay_trend_by_month":     queries.DELAY_TREND_BY_MONTH,
    }

    for name, query in queries_dict.items():
        df = pd.read_sql(query, engine)
        df = enrich(df, name, airport_map, carrier_map, airport_info)
        save_csv(df, name)

    print("\nAnalytics tables generated successfully.")


if __name__ == "__main__":
    run_analytics_pipeline()
