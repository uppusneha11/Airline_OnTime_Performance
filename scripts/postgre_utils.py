import os
import io
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load .env from project root (works when run from scripts/ or project root)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def connect_to_postgres():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
         host = 'localhost',
        port = '5432'
    )

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


def delete_existing_data(year, month):
    conn = connect_to_postgres()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM fact_flights
        WHERE year = %s AND month = %s
        """,
        (year, int(month))
    )

    count = cur.fetchone()[0]

    if count > 0:
        print(f"Month {year}-{month} already exists in the database. Deleting old data.")
    
    cur.execute(
        """
        DELETE FROM fact_flights
        WHERE year = %s AND month = %s
        """,
        (year, int(month))
    )

    conn.commit()
    print(f"Old data for {year}-{month} deleted")

    cur.close()
    conn.close()