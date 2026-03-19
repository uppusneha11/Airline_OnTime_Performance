import pandas as pd
from .config import BASE_DIR


WEEKDAY_MAP = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}

MONTH_MAP = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def load_lookups():
    lookup_dir = BASE_DIR / "Data" / "LookUp_Tables"

    airport_df = pd.read_csv(lookup_dir / "L_AIRPORT_ID.csv", dtype=str)
    airport_map = dict(zip(airport_df["Code"], airport_df["Description"]))

    carrier_df = pd.read_csv(lookup_dir / "L_UNIQUE_CARRIERS.csv", dtype=str)
    carrier_map = dict(zip(carrier_df["Code"], carrier_df["Description"]))

    # Filter to AIRPORT_IS_LATEST=1 to avoid duplicate rows from
    # historical/closed airport records (20 229 total → 6 850 current)
    airport_info = pd.read_csv(BASE_DIR / "Data" / "Airport Info.csv", dtype=str)
    airport_info = airport_info[airport_info["AIRPORT_IS_LATEST"] == "1"][
        ["AIRPORT_ID", "AIRPORT", "LATITUDE", "LONGITUDE"]
    ].copy()
    airport_info["AIRPORT_ID"] = airport_info["AIRPORT_ID"].astype(int)
    airport_info["LATITUDE"] = airport_info["LATITUDE"].astype(float)
    airport_info["LONGITUDE"] = airport_info["LONGITUDE"].astype(float)
    airport_info = airport_info.rename(columns={
        "AIRPORT_ID": "airport_id",
        "AIRPORT": "iata_code",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
    })

    return airport_map, carrier_map, airport_info


def _merge_coordinates(df, airport_info, id_col):
    df = df.merge(
        airport_info[["airport_id", "iata_code", "latitude", "longitude"]],
        left_on=id_col,
        right_on="airport_id",
        how="left",
    )
    if id_col != "airport_id":
        df = df.drop(columns=["airport_id"])
    return df


def enrich(df, name, airport_map, carrier_map, airport_info):
    if name == "airline_performance":
        df["airline_name"] = df["carrier"].map(carrier_map)

    elif name == "airport_departure_delays":
        df["airport_id"] = df["origin_airport_id"]
        df["airport_name"] = df["origin_airport_id"].astype(str).map(airport_map)
        df = _merge_coordinates(df, airport_info, "airport_id")

    elif name == "airport_arrival_delays":
        df["airport_id"] = df["dest_airport_id"]
        df["airport_name"] = df["dest_airport_id"].astype(str).map(airport_map)
        df = _merge_coordinates(df, airport_info, "airport_id")

    elif name == "delay_by_day":
        df["day_name"] = df["day_of_week"].map(WEEKDAY_MAP)

    elif name == "route_performance":
        df["origin_airport_name"] = df["origin_airport_id"].astype(str).map(airport_map)
        df["dest_airport_name"] = df["dest_airport_id"].astype(str).map(airport_map)
        df["airline_name"] = df["op_unique_carrier"].map(carrier_map)

    elif name == "route_time_day_analysis":
        df["origin_airport_name"] = df["origin_airport_id"].astype(str).map(airport_map)
        df["dest_airport_name"] = df["dest_airport_id"].astype(str).map(airport_map)
        df["airline_name"] = df["op_unique_carrier"].map(carrier_map)
        df["day_name"] = df["day_of_week"].map(WEEKDAY_MAP)

    elif name == "delay_cause_by_airline":
        df["airline_name"] = df["carrier"].map(carrier_map)
        total = (
            df["total_carrier_delay_mins"]
            + df["total_weather_delay_mins"]
            + df["total_nas_delay_mins"]
            + df["total_late_aircraft_delay_mins"]
            + df["total_security_delay_mins"]
        )
        df["pct_carrier_delay"]       = (df["total_carrier_delay_mins"]        / total * 100).round(2)
        df["pct_weather_delay"]       = (df["total_weather_delay_mins"]        / total * 100).round(2)
        df["pct_nas_delay"]           = (df["total_nas_delay_mins"]            / total * 100).round(2)
        df["pct_late_aircraft_delay"] = (df["total_late_aircraft_delay_mins"]  / total * 100).round(2)
        df["pct_security_delay"]      = (df["total_security_delay_mins"]       / total * 100).round(2)

    elif name == "delay_trend_by_month":
        df["month_name"] = df["month"].map(MONTH_MAP)
        df["year_month"] = df["year"].astype(str) + " - " + df["month_name"]

    return df
