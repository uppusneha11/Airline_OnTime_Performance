from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from scripts.postgre_utils import get_sqlalchemy_engine, rebuild_dim_city_airports


st.set_page_config(page_title="Smart Flight Route Analyzer", page_icon=":airplane:", layout="wide")
APP_DIR = Path(__file__).resolve().parent


@st.cache_resource
def get_engine():
    return get_sqlalchemy_engine()


def query_df(sql: str, params: Optional[Dict] = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


@st.cache_data
def fetch_carrier_map() -> Dict[str, str]:
    path = APP_DIR / "Data" / "LookUp_Tables" / "L_UNIQUE_CARRIERS.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str).rename(columns={"Code": "code", "Description": "name"})
    df = df.dropna(subset=["code", "name"])
    return dict(zip(df["code"], df["name"]))


def ensure_dim_table() -> bool:
    try:
        query_df("SELECT 1 FROM dim_city_airports LIMIT 1")
        return True
    except Exception:
        try:
            rebuild_dim_city_airports()
            return True
        except Exception:
            return False


@st.cache_data
def fetch_city_code_dim() -> pd.DataFrame:
    return query_df(
        """
        SELECT
            city_code,
            STRING_AGG(DISTINCT city_name, ' / ' ORDER BY city_name) AS city_names
        FROM dim_city_airports
        GROUP BY city_code
        ORDER BY city_code
        """
    )


@st.cache_data
def fetch_code_edges() -> pd.DataFrame:
    return query_df(
        """
        SELECT DISTINCT
            o.city_code AS origin_code,
            d.city_code AS dest_code
        FROM fact_flights f
        JOIN dim_city_airports o ON f.origin_airport_id = o.airport_id
        JOIN dim_city_airports d ON f.dest_airport_id = d.airport_id
        WHERE o.city_code IS NOT NULL
          AND d.city_code IS NOT NULL
        """
    )


def code_label(code: str, code_to_names: Dict[str, str]) -> str:
    names = code_to_names.get(code, "")
    return f"{code} - {names}" if names else code


def filter_codes_by_query(codes: List[str], code_to_names: Dict[str, str], query: str) -> List[str]:
    q = (query or "").strip().lower()
    if not q:
        return codes
    return [code for code in codes if q in code_label(code, code_to_names).lower()]


def get_reachable_codes(origin_code: str, edges_df: pd.DataFrame) -> List[str]:
    adjacency: Dict[str, Set[str]] = {}
    for _, row in edges_df.iterrows():
        src = str(row["origin_code"])
        dst = str(row["dest_code"])
        adjacency.setdefault(src, set()).add(dst)

    visited: Set[str] = set()
    q: deque = deque([origin_code])
    while q:
        node = q.popleft()
        if node in visited:
            continue
        visited.add(node)
        for nxt in adjacency.get(node, set()):
            if nxt not in visited:
                q.append(nxt)

    visited.discard(origin_code)
    return sorted(visited)


def build_route_filter(origin_code: str, dest_code: str, day_pref: str, specific_day: str, time_pref: str) -> Tuple[str, Dict]:
    where_parts = [
        "origin_airport_id IN (SELECT airport_id FROM dim_city_airports WHERE city_code = :origin_code)",
        "dest_airport_id IN (SELECT airport_id FROM dim_city_airports WHERE city_code = :dest_code)",
    ]
    params: Dict = {"origin_code": origin_code, "dest_code": dest_code}

    day_map = {"Sunday": 7, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
    if day_pref == "Specific Day":
        where_parts.append("day_of_week = :day_of_week")
        params["day_of_week"] = day_map[specific_day]

    if time_pref != "Any":
        where_parts.append("time_bucket = :time_bucket")
        params["time_bucket"] = time_pref

    return " AND ".join(where_parts), params


def render_global_landscape(carrier_map: Dict[str, str]):
    st.header("📊 US Flight Delay Landscape")
    st.caption("Understanding airline reliability across the US")

    metrics = query_df(
        """
        SELECT
            COUNT(*) AS total_flights,
            COUNT(DISTINCT op_unique_carrier) AS airlines_covered,
            (SELECT COUNT(*) FROM (
                SELECT origin_airport_id AS airport_id FROM fact_flights
                UNION
                SELECT dest_airport_id AS airport_id FROM fact_flights
            ) a) AS airports_covered,
            MIN(year) AS min_year,
            MAX(year) AS max_year,
            AVG(arr_del15) * 100 AS avg_delay_rate,
            AVG(cancelled) * 100 AS cancellation_rate,
            AVG(COALESCE(arr_delay_new, 0)) AS avg_delay_time
        FROM fact_flights
        """
    )
    if metrics.empty:
        return

    reliable = query_df(
        """
        SELECT op_unique_carrier AS carrier, AVG(CASE WHEN arr_del15 = 0 THEN 1 ELSE 0 END) * 100 AS on_time_rate
        FROM fact_flights
        GROUP BY op_unique_carrier
        ORDER BY on_time_rate DESC
        LIMIT 1
        """
    )

    m = metrics.iloc[0]
    top_reliable = reliable.iloc[0]["carrier"] if not reliable.empty else "-"
    top_reliable_name = carrier_map.get(top_reliable, top_reliable)

    r1 = st.columns(4)
    r1[0].metric("Total Flights Analyzed", f"{int(m['total_flights']):,}")
    r1[1].metric("Airlines Covered", f"{int(m['airlines_covered'])}")
    r1[2].metric("Airports Covered", f"{int(m['airports_covered'])}")
    r1[3].metric("Years of Data", f"{int(m['min_year'])}-{int(m['max_year'])}")

    r2 = st.columns(4)
    r2[0].metric("Average Delay Rate", f"{m['avg_delay_rate']:.1f}%")
    r2[1].metric("Cancellation Rate", f"{m['cancellation_rate']:.1f}%")
    r2[2].metric("Average Delay Time", f"{m['avg_delay_time']:.0f} min")
    r2[3].metric("Most Reliable Airline", top_reliable_name)

    cause_df = query_df(
        """
        SELECT
            SUM(COALESCE(late_aircraft_delay, 0)) AS late_aircraft,
            SUM(COALESCE(carrier_delay, 0)) AS carrier_issues,
            SUM(COALESCE(weather_delay, 0)) AS weather,
            SUM(COALESCE(nas_delay, 0)) AS nas,
            SUM(COALESCE(security_delay, 0)) AS security
        FROM fact_flights
        """
    )
    reliability = query_df(
        """
        SELECT op_unique_carrier AS carrier, AVG(CASE WHEN arr_del15 = 0 THEN 1 ELSE 0 END) * 100 AS on_time_rate
        FROM fact_flights
        GROUP BY op_unique_carrier
        ORDER BY on_time_rate DESC
        """
    )
    reliability["airline"] = reliability["carrier"].map(lambda code: carrier_map.get(code, code))

    c1, c2 = st.columns(2)
    with c1:
        if not cause_df.empty:
            row = cause_df.iloc[0]
            causes = pd.DataFrame(
                {
                    "cause": ["Late Aircraft", "Carrier Issues", "Weather", "NAS", "Security"],
                    "minutes": [row["late_aircraft"], row["carrier_issues"], row["weather"], row["nas"], row["security"]],
                }
            )
            st.plotly_chart(px.pie(causes, names="cause", values="minutes", title="Delay Causes Across the US"), use_container_width=True)
    with c2:
        if not reliability.empty:
            st.plotly_chart(px.bar(reliability.head(15), x="airline", y="on_time_rate", title="Airline Reliability Ranking"), use_container_width=True)


def main():
    st.title("✈ Smart Flight Route Analyzer")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    if not ensure_dim_table():
        st.error("Could not create/read `dim_city_airports`. Run `python run_pipeline.py` and try again.")
        return

    try:
        carrier_map = fetch_carrier_map()
        city_dim = fetch_city_code_dim()
        code_edges = fetch_code_edges()
    except Exception as exc:
        st.error("Unable to connect to PostgreSQL. Check DB status and `.env` credentials.")
        st.exception(exc)
        return

    if city_dim.empty:
        st.error("`dim_city_airports` is empty. Run `python run_pipeline.py` first.")
        return

    code_to_names = dict(zip(city_dim["city_code"], city_dim["city_names"]))
    all_codes = sorted(city_dim["city_code"].tolist())

    render_global_landscape(carrier_map)
    st.divider()

    st.header("✈ Route Analyzer")
    st.caption("Choose metro origin and destination (e.g., NYC includes JFK/LGA/EWR), then set day/time preferences.")

    s1, s2 = st.columns(2)
    with s1:
        origin_query = st.text_input("Search Origin (strict)", placeholder="e.g., nyc or new york")
    with s2:
        dest_query = st.text_input("Search Destination (strict)", placeholder="e.g., aus or austin")

    filtered_origins = filter_codes_by_query(all_codes, code_to_names, origin_query)
    if not filtered_origins:
        st.warning("No origin options match your search.")
        return

    u1, u2, u3, u4 = st.columns(4)
    with u1:
        origin_code = st.selectbox("Origin", filtered_origins, format_func=lambda c: code_label(c, code_to_names))
    with u2:
        reachable = get_reachable_codes(origin_code, code_edges)
        filtered_dest = filter_codes_by_query(reachable, code_to_names, dest_query)
        if not filtered_dest:
            st.warning("No reachable destination options match your search.")
            return
        dest_code = st.selectbox("Destination", filtered_dest, format_func=lambda c: code_label(c, code_to_names))
    with u3:
        day_pref = st.selectbox("Travel Day", ["Flexible", "Specific Day"])
        specific_day = st.selectbox("Specific Day", ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], disabled=(day_pref != "Specific Day"))
    with u4:
        time_pref = st.selectbox("Preferred Time", ["Any", "Morning", "Afternoon", "Evening", "Late Night/Early Morning"])

    where_clause, params = build_route_filter(origin_code, dest_code, day_pref, specific_day, time_pref)
    route_clause = (
        "origin_airport_id IN (SELECT airport_id FROM dim_city_airports WHERE city_code = :origin_code) "
        "AND dest_airport_id IN (SELECT airport_id FROM dim_city_airports WHERE city_code = :dest_code)"
    )
    route_params = {"origin_code": origin_code, "dest_code": dest_code}

    route_airline = query_df(
        f"""
        SELECT
            op_unique_carrier AS carrier,
            COUNT(*) AS flights,
            AVG(CASE WHEN arr_del15 = 0 THEN 1 ELSE 0 END) * 100 AS on_time_rate,
            AVG(COALESCE(arr_delay_new, 0)) AS avg_delay,
            AVG(cancelled) * 100 AS cancellation_rate
        FROM fact_flights
        WHERE {where_clause}
        GROUP BY op_unique_carrier
        ORDER BY on_time_rate DESC, avg_delay ASC
        """,
        params,
    )
    if route_airline.empty:
        st.warning("No matching flights found for selected filters.")
        return

    route_airline["airline"] = route_airline["carrier"].map(lambda x: carrier_map.get(x, x))
    best = route_airline.iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Best Airline", f"{best['airline']}")
    k2.metric("On-Time Rate", f"{best['on_time_rate']:.1f}%")
    k3.metric("Expected Delay", f"{best['avg_delay']:.0f} minutes")
    k4.metric("Cancellation Risk", f"{best['cancellation_rate']:.1f}%")

    st.subheader("Route Performance")
    st.plotly_chart(px.bar(route_airline, x="airline", y=["on_time_rate", "avg_delay", "cancellation_rate"], barmode="group", title=f"Airline Performance: {origin_code} → {dest_code}"), use_container_width=True)
    st.dataframe(route_airline[["airline", "flights", "on_time_rate", "avg_delay", "cancellation_rate"]], use_container_width=True)

    st.subheader("Route Reliability History")
    route_history = query_df(
        f"""
        SELECT month, AVG(arr_del15) * 100 AS delay_rate
        FROM fact_flights
        WHERE {route_clause}
        GROUP BY month
        ORDER BY month
        """,
        route_params,
    )
    if not route_history.empty:
        month_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        route_history["month_name"] = route_history["month"].map(month_map)
        route_history["month_name"] = pd.Categorical(route_history["month_name"], categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], ordered=True)
        st.plotly_chart(px.line(route_history.sort_values("month"), x="month_name", y="delay_rate", markers=True, title="Month vs Delay Rate"), use_container_width=True)


if __name__ == "__main__":
    main()
