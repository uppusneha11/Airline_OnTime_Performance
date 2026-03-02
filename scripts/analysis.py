import pandas as pd
import os

# This function calculates the average delay or cancellation rate for the flights by airline
def route_airline_summary(df):
    summary = (
        df.groupby(["ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID", "OP_UNIQUE_CARRIER"])
        .agg(
            total_flights=("FL_DATE", "count"),
            delay_rate=("ARR_DEL15", "mean"),
            cancellation_rate=("CANCELLED", "mean"),
            avg_arrival_delay=("ARR_DELAY_NEW", "mean")
        )
        .reset_index()
    )

    summary["delay_rate"] *= 100
    summary["cancellation_rate"] *= 100

    return summary

# This function calculates the delay summary for the flights by day of the week
def route_day_summary(df):
    summary = (
        df.groupby(["ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID", "DAY_OF_WEEK"])
        .agg(
            total_flights=("FL_DATE", "count"),
            delay_rate=("ARR_DEL15", "mean")
        )
        .reset_index()
    )

    summary["delay_rate"] *= 100

    return summary

# This function calculates the delay summary for the flights by hour of the day
def route_hour_summary(df):
    summary = (
        df.groupby(["ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID", "DEP_HOUR"])
        .agg(
            total_flights=("FL_DATE", "count"),
            delay_rate=("ARR_DEL15", "mean")
        )
        .reset_index()
    )

    summary["delay_rate"] *= 100

    return summary


def run_analysis(input_path, output_dir):
    df = pd.read_parquet(input_path)

    route_summary = route_airline_summary(df)
    day_summary = route_day_summary(df)
    hour_summary = route_hour_summary(df)

    os.makedirs(output_dir, exist_ok=True)

    route_summary.to_csv(os.path.join(output_dir, "route_airline_summary.csv"), index=False)
    day_summary.to_csv(os.path.join(output_dir, "route_day_summary.csv"), index=False)
    hour_summary.to_csv(os.path.join(output_dir, "route_hour_summary.csv"), index=False)