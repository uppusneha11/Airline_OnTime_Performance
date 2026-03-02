from cleaning import clean_flights
from normalization import normalize_flights
from s3_utils import read_from_s3, write_to_s3
from postgre_utils import connect_to_postgres
import io

BUCKET = "airline-analytics-raw-data"

def load_to_postgres(df):
    conn = connect_to_postgres()
    cur = conn.cursor()

    buffer = io.StringIO()
    df.columns = df.columns.str.lower()

    df = df[[
        "fl_date",
        "op_unique_carrier",
        "op_carrier_fl_num",
        "origin_airport_id",
        "origin_city_name",
        "origin_state_abr",
        "dest_airport_id",
        "dest_city_name",
        "dest_state_abr",
        "crs_dep_time",
        "dep_time",
        "dep_delay_new",
        "dep_del15",
        "crs_arr_time",
        "arr_time",
        "arr_delay_new",
        "arr_del15",
        "cancelled",
        "cancellation_code",
        "diverted",
        "distance",
        "distance_group",
        "carrier_delay",
        "weather_delay",
        "nas_delay",
        "security_delay",
        "late_aircraft_delay",
        "div_airport_landings",
        "div_reached_dest",
        "div_arr_delay" ,
        "div_distance",
        "div1_airport",
        "div2_airport",
        "year",
        "quarter",
        "month",
        "day_of_month",
        "day_of_week",
        "sch_dep_hour",
        "sch_arr_hour",
        "dep_hour",
        "arr_hour",
        "time_bucket"
    ]]

    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    cur.copy_expert(
        """
        COPY fact_flights
        FROM STDIN
        WITH (FORMAT CSV)
        """,
        buffer
    )

    conn.commit()
    cur.close()
    conn.close()


def process_month(year, month):
    raw_key = f"raw/{year}/{month}.csv"
    cleaned_key = f"cleaned/{year}/{month}.parquet"
    normalized_key = f"normalized/{year}/{month}.parquet"

    print(f"Processing {year}-{month}")

    df_raw = read_from_s3(BUCKET, raw_key)

    df_clean = clean_flights(df_raw)
    write_to_s3(df_clean, BUCKET, cleaned_key)

    df_norm = normalize_flights(df_clean)
    write_to_s3(df_norm, BUCKET, normalized_key)

    load_to_postgres(df_norm)

    print(f"Finished {year}-{month}")


def run_pipeline():
    months = ["01","02","03","04","05","06","07","08","09","10"]

    for month in months:
        process_month("2025", month)


if __name__ == "__main__":
    run_pipeline()