import os
import io
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load .env from project root (works when run from scripts/ or project root)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    return {
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
    }


def connect_to_postgres():
    """Returns psycopg2 connection for COPY and raw SQL operations."""
    params = get_connection()
    return psycopg2.connect(**params)


def get_sqlalchemy_engine():
    """Returns SQLAlchemy engine for pandas read_sql (avoids deprecation warning)."""
    params = get_connection()
    user = quote_plus(params["user"])
    password = quote_plus(params["password"])
    uri = f"postgresql://{user}:{password}@{params['host']}:{params['port']}/{params['dbname']}"
    return create_engine(uri)

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


def rebuild_dim_city_airports():
    """
    Builds a city-to-airport dimension table used by the dashboard.
    Includes metro overrides (e.g., NYC = New York + Newark airports).
    """
    conn = connect_to_postgres()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dim_city_airports (
            city_code TEXT NOT NULL,
            city_name TEXT NOT NULL,
            state_abr TEXT NOT NULL,
            airport_id INTEGER PRIMARY KEY
        )
        """
    )

    cur.execute("TRUNCATE TABLE dim_city_airports")

    cur.execute(
        """
        WITH airports AS (
            SELECT DISTINCT
                origin_airport_id AS airport_id,
                origin_city_name AS city_name,
                origin_state_abr AS state_abr
            FROM fact_flights
            UNION
            SELECT DISTINCT
                dest_airport_id AS airport_id,
                dest_city_name AS city_name,
                dest_state_abr AS state_abr
            FROM fact_flights
        ),
        normalized AS (
            SELECT
                airport_id,
                TRIM(SPLIT_PART(city_name, ',', 1)) || ', ' || UPPER(state_abr) AS city_name_norm,
                UPPER(state_abr) AS state_abr_norm,
                CASE
                    WHEN LOWER(city_name) IN ('new york, ny', 'newark, nj') THEN 'NYC'
                    WHEN LOWER(city_name) = 'chicago, il' THEN 'CHI'
                    WHEN LOWER(city_name) = 'washington, dc' THEN 'WAS'
                    WHEN LOWER(city_name) IN ('dallas, tx', 'dallas/fort worth, tx') THEN 'DFW'
                    WHEN LOWER(city_name) = 'los angeles, ca' THEN 'LAX'
                    WHEN LOWER(city_name) = 'san francisco, ca' THEN 'SFO'
                    ELSE UPPER(SUBSTRING(REGEXP_REPLACE(SPLIT_PART(city_name, ',', 1), '[^A-Za-z]', '', 'g') FROM 1 FOR 3))
                END AS city_code
            FROM airports
            WHERE airport_id IS NOT NULL
              AND city_name IS NOT NULL
              AND state_abr IS NOT NULL
        )
        INSERT INTO dim_city_airports (city_code, city_name, state_abr, airport_id)
        SELECT city_code, city_name_norm, state_abr_norm, airport_id
        FROM normalized
        """
    )

    conn.commit()
    print("dim_city_airports refreshed")

    cur.close()
    conn.close()