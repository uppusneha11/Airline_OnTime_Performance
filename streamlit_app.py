import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_searchbox import st_searchbox

warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

st.set_page_config(page_title="FlightIQ", page_icon="✈", layout="wide")
APP_DIR  = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "analytics_tables"

# ── Constants ─────────────────────────────────────────────────────────────────
C_GOOD    = "#1D9E75"
C_MID     = "#EF9F27"
C_BAD     = "#D85A30"
C_BLUE    = "#378ADD"
C_PRIMARY = "#185FA5"

DAY_MAP  = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
            5: "Friday", 6: "Saturday", 7: "Sunday"}
DAY_NUM  = {v: k for k, v in DAY_MAP.items()}
MONTH_SHORT = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
               7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
MONTH_FULL  = {1: "January", 2: "February", 3: "March", 4: "April",
               5: "May", 6: "June", 7: "July", 8: "August",
               9: "September", 10: "October", 11: "November", 12: "December"}
TIME_ORDER = ["Morning", "Afternoon", "Evening", "Night", "Late Night/Early Morning"]

# Metro area groupings — airports in the same metro are combined for search/filtering
METRO_MAP: Dict[str, str] = {
    # New York (JFK + LGA + EWR)
    "New York, NY":          "New York Area",
    "Newark, NJ":            "New York Area",
    # Los Angeles (LAX + BUR + LGB + ONT + SNA)
    "Los Angeles, CA":       "Los Angeles Area",
    "Burbank, CA":           "Los Angeles Area",
    "Long Beach, CA":        "Los Angeles Area",
    "Ontario, CA":           "Los Angeles Area",
    "Santa Ana, CA":         "Los Angeles Area",
    # Dallas (DFW + DAL)
    "Dallas/Fort Worth, TX": "Dallas Area",
    "Dallas, TX":            "Dallas Area",
    # Miami / South Florida (MIA + FLL)
    "Miami, FL":             "Miami Area",
    "Fort Lauderdale, FL":   "Miami Area",
    # San Francisco Bay Area (SFO + OAK + SJC)
    "San Francisco, CA":     "San Francisco Bay Area",
    "Oakland, CA":           "San Francisco Bay Area",
    "San Jose, CA":          "San Francisco Bay Area",
    # Washington DC (DCA + IAD)
    "Washington, DC":        "Washington DC Area",
    # Houston (IAH + HOU)
    "Houston, TX":           "Houston Area",
}


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> Dict[str, pd.DataFrame]:
    return {
        "airline_perf":  pd.read_csv(DATA_DIR / "airline_performance.csv"),
        "route_perf":    pd.read_csv(DATA_DIR / "route_performance.csv"),
        "route_time_day":pd.read_csv(DATA_DIR / "route_time_day_analysis.csv"),
        "delay_causes":  pd.read_csv(DATA_DIR / "delay_cause_by_airline.csv"),
        "delay_monthly": pd.read_csv(DATA_DIR / "delay_trend_by_month.csv"),
        "airport_dep":   pd.read_csv(DATA_DIR / "airport_departure_delays.csv"),
    }


def extract_city(name) -> str:
    """'New York, NY: JFK International' → 'New York, NY'"""
    if pd.isna(name):
        return ""
    s = str(name)
    idx = s.find(":")
    return s[:idx].strip() if idx >= 0 else s.strip()


def apply_metro(city: str) -> str:
    """Replace individual city name with metro area label if one is defined."""
    return METRO_MAP.get(city, city)


@st.cache_data
def build_route_frames() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pre-compute city columns on route DataFrames — cached on first call."""
    data = load_data()

    rp = data["route_perf"].copy()
    rp["origin_city"] = rp["origin_airport_name"].apply(extract_city).apply(apply_metro)
    rp["dest_city"]   = rp["dest_airport_name"].apply(extract_city).apply(apply_metro)

    rtd = data["route_time_day"].copy()
    rtd["origin_city"] = rtd["origin_airport_name"].apply(extract_city).apply(apply_metro)
    rtd["dest_city"]   = rtd["dest_airport_name"].apply(extract_city).apply(apply_metro)

    return rp, rtd


# ── Pandas helpers ────────────────────────────────────────────────────────────
def wmean(vals: pd.Series, weights: pd.Series) -> float:
    """Weighted mean; falls back to simple mean if total weight is zero."""
    w = weights.fillna(0)
    total = w.sum()
    return float((vals * w).sum() / total) if total > 0 else float(vals.mean())


def wagg_route(g: pd.DataFrame, delay_col: str = "avg_arrival_delay") -> pd.Series:
    w = g["total_flights"]
    return pd.Series({
        "flights":           w.sum(),
        "on_time_rate":      100.0 - wmean(g["delay_rate"], w),
        "avg_delay":         wmean(g[delay_col], w),
        "cancellation_rate": wmean(g["cancellation_rate"], w),
    })


# ── CSV-based data getters ────────────────────────────────────────────────────
def get_airline_stats(
    rp: pd.DataFrame, rtd: pd.DataFrame,
    origin_city: str, dest_city: str,
    day_pref: str, specific_day: str, time_pref: str,
    priority: str,
) -> pd.DataFrame:
    """Return airline comparison DataFrame for the selected route + filters."""
    use_rtd = day_pref == "Specific Day" or time_pref != "Any"

    if use_rtd:
        route = rtd[(rtd["origin_city"] == origin_city) & (rtd["dest_city"] == dest_city)].copy()
        if day_pref == "Specific Day" and specific_day in DAY_NUM:
            route = route[route["day_of_week"] == DAY_NUM[specific_day]]
        if time_pref != "Any":
            route = route[route["time_bucket"] == time_pref]
        delay_col = "avg_delay"
    else:
        route = rp[(rp["origin_city"] == origin_city) & (rp["dest_city"] == dest_city)].copy()
        delay_col = "avg_arrival_delay"

    if route.empty:
        return pd.DataFrame()

    result = (
        route.groupby("airline_name")
        .apply(wagg_route, delay_col=delay_col)
        .reset_index()
        .rename(columns={"airline_name": "airline"})
    )

    sort_col, asc = {
        "On-time performance":   ("on_time_rate",      False),
        "Fewest delays":          ("avg_delay",         True),
        "Low cancellation risk":  ("cancellation_rate", True),
    }.get(priority, ("on_time_rate", False))

    return result.sort_values(sort_col, ascending=asc).reset_index(drop=True)


def get_route_timing(
    rtd: pd.DataFrame, origin_city: str, dest_city: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (by_time, by_day, heatmap) DataFrames for Best Timing tab."""
    route = rtd[(rtd["origin_city"] == origin_city) & (rtd["dest_city"] == dest_city)].copy()
    if route.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def wagg_timing(g: pd.DataFrame) -> pd.Series:
        w = g["total_flights"]
        return pd.Series({
            "flights":    w.sum(),
            "avg_delay":  wmean(g["avg_delay"], w),
            "delay_rate": wmean(g["delay_rate"], w),
        })

    by_time = route.groupby("time_bucket").apply(wagg_timing).reset_index()

    by_day = (
        route.groupby(["day_of_week", "day_name"])
        .apply(wagg_timing)
        .reset_index()
        .sort_values("day_of_week")
    )

    heatmap_df = (
        route.groupby(["day_name", "time_bucket"])
        .apply(lambda g: wmean(g["avg_delay"], g["total_flights"]))
        .reset_index(name="avg_delay")
    )
    day_to_num = {v: k for k, v in DAY_MAP.items()}
    heatmap_df["day_of_week"] = heatmap_df["day_name"].map(day_to_num)

    return by_time, by_day, heatmap_df


def get_monthly_data(dm_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate network-wide delay_trend_by_month across all years, by calendar month."""
    def wagg_monthly(g: pd.DataFrame) -> pd.Series:
        w = g["total_flights"]
        return pd.Series({
            "total_flights": w.sum(),
            "avg_delay":     wmean(g["avg_delay"], w),
            "delay_rate":    wmean(g["delay_rate"], w),
            "on_time_rate":  100.0 - wmean(g["delay_rate"], w),
        })

    monthly = dm_df.groupby("month").apply(wagg_monthly).reset_index()
    monthly["month_name"] = monthly["month"].map(MONTH_SHORT)
    monthly["month_name"] = pd.Categorical(
        monthly["month_name"], categories=list(MONTH_SHORT.values()), ordered=True
    )
    return monthly


def get_causes_data(dc_df: pd.DataFrame, airline_names: List[str]) -> pd.DataFrame:
    """Return causes breakdown for the airlines flying this route."""
    causes = dc_df[dc_df["airline_name"].isin(airline_names)].copy()
    if causes.empty:
        return pd.DataFrame()

    causes = causes.rename(columns={
        "total_carrier_delay_mins":       "carrier_mins",
        "total_late_aircraft_delay_mins": "late_aircraft_mins",
        "total_nas_delay_mins":           "nas_mins",
        "total_weather_delay_mins":       "weather_mins",
        "total_security_delay_mins":      "security_mins",
        "airline_name":                   "airline",
    })

    delay_cols = ["carrier_mins", "late_aircraft_mins", "nas_mins", "weather_mins", "security_mins"]
    total = causes[delay_cols].sum(axis=1).replace(0, float("nan"))
    for col in delay_cols:
        causes[f"pct_{col}"] = (causes[col] / total * 100).round(1).fillna(0)

    keep = ["airline"] + delay_cols + [f"pct_{c}" for c in delay_cols]
    return causes[keep].reset_index(drop=True)


def get_similar_routes(
    rp: pd.DataFrame, origin_city: str, dest_city: str
) -> pd.DataFrame:
    """Top alternative destinations from the same origin."""
    same_origin = rp[(rp["origin_city"] == origin_city) & (rp["dest_city"] != dest_city)].copy()
    if same_origin.empty:
        return pd.DataFrame()

    similar = (
        same_origin.groupby("dest_city")
        .apply(
            lambda g: pd.Series({
                "flights":      g["total_flights"].sum(),
                "on_time_rate": 100.0 - wmean(g["delay_rate"], g["total_flights"]),
                "avg_delay":    wmean(g["avg_arrival_delay"], g["total_flights"]),
            })
        )
        .reset_index()
        .rename(columns={"dest_city": "dest_city_name"})
    )
    return (
        similar[similar["flights"] > 200]
        .sort_values("on_time_rate", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )


# ── Network overview ──────────────────────────────────────────────────────────
def render_network_overview(data: Dict[str, pd.DataFrame]):
    ap = data["airline_perf"]
    ad = data["airport_dep"]
    dm = data["delay_monthly"]
    dc = data["delay_causes"]

    if ap.empty:
        return

    w = ap["total_flights"]
    total_flights    = int(w.sum())
    airlines_covered = len(ap)
    airports_covered = len(ad)
    min_year         = int(dm["year"].min()) if "year" in dm.columns else "—"
    max_year         = int(dm["year"].max()) if "year" in dm.columns else "—"
    avg_delay_rate   = wmean(ap["delay_rate"],        w)
    cancellation_rate= wmean(ap["cancellation_rate"], w)
    avg_delay_time   = wmean(ap["avg_arrival_delay"], w)
    top_name         = ap.sort_values("on_time_rate", ascending=False).iloc[0]["airline_name"]

    # ── 8 KPI metrics ────────────────────────────────────────────────────────
    r1 = st.columns(4)
    r1[0].metric("Total Flights Analyzed",  f"{total_flights:,}")
    r1[1].metric("Airlines Covered",        f"{airlines_covered}")
    r1[2].metric("Airports Covered",        f"{airports_covered}")
    r1[3].metric("Years of Data",           f"{min_year}–{max_year}")

    r2 = st.columns(4)
    r2[0].metric("Avg Network Delay Rate",  f"{avg_delay_rate:.1f}%")
    r2[1].metric("Cancellation Rate",       f"{cancellation_rate:.1f}%")
    r2[2].metric("Avg Delay Time",          f"{avg_delay_time:.0f} min")
    r2[3].metric("Most Reliable Airline",   top_name)

    # ── Charts ────────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        if not dc.empty:
            cause_totals = pd.DataFrame({
                "cause": ["Late Aircraft", "Carrier Issues", "Weather", "NAS / ATC", "Security"],
                "minutes": [
                    dc["total_late_aircraft_delay_mins"].sum(),
                    dc["total_carrier_delay_mins"].sum(),
                    dc["total_weather_delay_mins"].sum(),
                    dc["total_nas_delay_mins"].sum(),
                    dc["total_security_delay_mins"].sum(),
                ],
            })
            fig = px.pie(
                cause_totals, names="cause", values="minutes",
                color="cause",
                color_discrete_map={
                    "Late Aircraft":  C_BLUE,
                    "Carrier Issues": C_BAD,
                    "Weather":        "#7F77DD",
                    "NAS / ATC":      C_MID,
                    "Security":       "#888780",
                },
                title="Delay Causes Across the US Network",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if not ap.empty:
            top15 = ap.sort_values("on_time_rate", ascending=False).head(15).sort_values("on_time_rate")
            fig2 = px.bar(
                top15,
                x="on_time_rate", y="airline_name", orientation="h",
                color="on_time_rate",
                color_continuous_scale=[(0, C_BAD), (0.5, C_MID), (1, C_GOOD)],
                range_color=[60, 90],
                labels={"on_time_rate": "On-Time Rate (%)", "airline_name": ""},
                title="Airline Reliability Ranking (Top 15)",
            )
            fig2.update_layout(
                coloraxis_showscale=False,
                margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ── Tab renderers ─────────────────────────────────────────────────────────────
def render_airlines_tab(route_airline: pd.DataFrame):
    if route_airline.empty:
        st.info("No airline data for this route with the selected filters.")
        return

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            route_airline.sort_values("on_time_rate"),
            x="on_time_rate", y="airline", orientation="h",
            color="on_time_rate",
            color_continuous_scale=[(0, C_BAD), (0.5, C_MID), (1, C_GOOD)],
            range_color=[50, 90],
            labels={"on_time_rate": "On-Time Rate (%)", "airline": ""},
            title="On-Time Rate by Airline",
        )
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=10, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

        if len(route_airline) > 1:
            best  = route_airline.iloc[0]
            worst = route_airline.iloc[-1]
            diff  = best["on_time_rate"] - worst["on_time_rate"]
            st.info(
                f"**{best['airline']}** leads at **{best['on_time_rate']:.1f}%** on-time — "
                f"**{diff:.0f} percentage points** ahead of **{worst['airline']}** "
                f"({worst['on_time_rate']:.1f}%)."
            )

    with c2:
        fig2 = px.bar(
            route_airline.sort_values("avg_delay", ascending=False),
            x="avg_delay", y="airline", orientation="h",
            color="avg_delay",
            color_continuous_scale=[(0, C_GOOD), (0.5, C_MID), (1, C_BAD)],
            range_color=[5, 40],
            labels={"avg_delay": "Avg Delay (min)", "airline": ""},
            title="Average Arrival Delay by Airline",
        )
        fig2.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=10, t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)

        if len(route_airline) > 1:
            best_d  = route_airline.sort_values("avg_delay").iloc[0]
            worst_d = route_airline.sort_values("avg_delay").iloc[-1]
            extra   = worst_d["avg_delay"] - best_d["avg_delay"]
            st.info(
                f"**{best_d['airline']}** averages **{best_d['avg_delay']:.0f} min**. "
                f"**{worst_d['airline']}** averages **{worst_d['avg_delay']:.0f} min** — "
                f"**{extra:.0f} extra minutes** per flight."
            )

    fig3 = px.scatter(
        route_airline,
        x="avg_delay", y="on_time_rate",
        size="flights", color="cancellation_rate",
        hover_name="airline",
        color_continuous_scale=[(0, C_GOOD), (0.5, C_MID), (1, C_BAD)],
        labels={
            "avg_delay":         "Avg Delay (min)",
            "on_time_rate":      "On-Time Rate (%)",
            "cancellation_rate": "Cancellation %",
            "flights":           "Flights Analyzed",
        },
        title="Delay vs On-Time Rate  —  bubble size = flight volume, color = cancellation risk",
    )
    fig3.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig3, use_container_width=True)


def render_timing_tab(
    by_time: pd.DataFrame, by_day: pd.DataFrame, heatmap_df: pd.DataFrame
):
    c1, c2 = st.columns(2)

    with c1:
        if not by_time.empty:
            present = [t for t in TIME_ORDER if t in by_time["time_bucket"].values]
            df_t = by_time.set_index("time_bucket").reindex(present).reset_index()
            fig = px.bar(
                df_t,
                x="avg_delay", y="time_bucket", orientation="h",
                color="avg_delay",
                color_continuous_scale=[(0, C_GOOD), (0.5, C_MID), (1, C_BAD)],
                range_color=[0, 35],
                labels={"avg_delay": "Avg Delay (min)", "time_bucket": ""},
                title="Avg Delay by Departure Time",
            )
            fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=10, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

            best_t  = df_t.sort_values("avg_delay").iloc[0]
            worst_t = df_t.sort_values("avg_delay").iloc[-1]
            st.success(
                f"**Book a {best_t['time_bucket'].lower()} flight** "
                f"({best_t['avg_delay']:.0f} min avg). "
                f"{worst_t['time_bucket']} flights average "
                f"**{worst_t['avg_delay'] - best_t['avg_delay']:.0f} more minutes** of delay."
            )

    with c2:
        if not by_day.empty:
            day_order = list(DAY_MAP.values())
            df_d = by_day.copy()
            df_d["day_name"] = pd.Categorical(df_d["day_name"], categories=day_order, ordered=True)
            df_d = df_d.sort_values("day_name")
            fig2 = px.bar(
                df_d,
                x="avg_delay", y="day_name", orientation="h",
                color="avg_delay",
                color_continuous_scale=[(0, C_GOOD), (0.5, C_MID), (1, C_BAD)],
                range_color=[0, 35],
                labels={"avg_delay": "Avg Delay (min)", "day_name": ""},
                title="Avg Delay by Day of Week",
            )
            fig2.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=10, t=40, b=0))
            st.plotly_chart(fig2, use_container_width=True)

            best_d  = df_d.sort_values("avg_delay").iloc[0]
            worst_d = df_d.sort_values("avg_delay").iloc[-1]
            st.success(
                f"**{best_d['day_name']} is the safest day** ({best_d['avg_delay']:.0f} min avg). "
                f"Avoid **{worst_d['day_name']}** ({worst_d['avg_delay']:.0f} min avg)."
            )

    if not heatmap_df.empty:
        pivot = heatmap_df.pivot_table(
            index="day_name", columns="time_bucket", values="avg_delay", aggfunc="mean"
        )
        row_order = [d for d in DAY_MAP.values() if d in pivot.index]
        col_order = [t for t in TIME_ORDER       if t in pivot.columns]
        pivot = pivot.reindex(index=row_order, columns=col_order)

        fig3 = px.imshow(
            pivot,
            color_continuous_scale=[(0, C_GOOD), (0.4, C_MID), (1, C_BAD)],
            labels={"x": "Time of Day", "y": "Day of Week", "color": "Avg Delay (min)"},
            title="Delay Risk Heatmap — Day × Time of Day  (darker = worse, avoid top-right)",
            aspect="auto",
            text_auto=".0f",
        )
        fig3.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig3, use_container_width=True)


def render_seasonality_tab(monthly: pd.DataFrame, selected_month: int):
    if monthly.empty:
        st.info("No monthly data available.")
        return

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            monthly.sort_values("month"),
            x="month_name", y="avg_delay",
            color="avg_delay",
            color_continuous_scale=[(0, C_GOOD), (0.5, C_MID), (1, C_BAD)],
            range_color=[5, 35],
            labels={"avg_delay": "Avg Delay (min)", "month_name": ""},
            title="Monthly Avg Delay",
        )
        if selected_month > 0:
            sel_label = MONTH_SHORT.get(selected_month, "")
            if sel_label in monthly["month_name"].values:
                fig.add_vline(
                    x=sel_label, line_dash="dash", line_color=C_PRIMARY,
                    annotation_text="Selected month", annotation_position="top right",
                )
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=10, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

        best_m  = monthly.sort_values("avg_delay").iloc[0]
        worst_m = monthly.sort_values("avg_delay").iloc[-1]
        st.info(
            f"**Best month:** {MONTH_FULL.get(int(best_m['month']), '')} "
            f"({best_m['avg_delay']:.0f} min avg).  "
            f"**Worst:** {MONTH_FULL.get(int(worst_m['month']), '')} "
            f"({worst_m['avg_delay']:.0f} min avg)."
        )

    with c2:
        fig2 = px.line(
            monthly.sort_values("month"),
            x="month_name", y="on_time_rate",
            markers=True,
            color_discrete_sequence=[C_PRIMARY],
            labels={"on_time_rate": "On-Time Rate (%)", "month_name": ""},
            title="On-Time Rate by Month",
        )
        fig2.update_layout(margin=dict(l=0, r=10, t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)


def render_causes_tab(causes_df: pd.DataFrame, similar_df: pd.DataFrame, origin_label: str):
    CAUSE_LABELS = {
        "pct_carrier_mins":       "Carrier",
        "pct_late_aircraft_mins": "Late Aircraft",
        "pct_nas_mins":           "NAS / ATC",
        "pct_weather_mins":       "Weather",
        "pct_security_mins":      "Security",
    }
    CAUSE_COLORS = {
        "Carrier":       C_BAD,
        "Late Aircraft": C_BLUE,
        "NAS / ATC":     C_MID,
        "Weather":       "#7F77DD",
        "Security":      "#888780",
    }

    if not causes_df.empty:
        melted = causes_df.melt(
            id_vars="airline",
            value_vars=list(CAUSE_LABELS.keys()),
            var_name="cause_key",
            value_name="pct",
        )
        melted["Cause"] = melted["cause_key"].map(CAUSE_LABELS)

        fig = px.bar(
            melted,
            x="pct", y="airline", color="Cause", orientation="h", barmode="stack",
            color_discrete_map=CAUSE_COLORS,
            labels={"pct": "% of Total Delay Minutes", "airline": ""},
            title="Delay Cause Breakdown by Airline  (% of total delay minutes)",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), legend_title_text="Cause")
        st.plotly_chart(fig, use_container_width=True)

        worst_carrier = causes_df.sort_values("pct_carrier_mins", ascending=False).iloc[0]
        best_carrier  = causes_df.sort_values("pct_carrier_mins").iloc[0]
        st.info(
            f"**{worst_carrier['airline']}** attributes **{worst_carrier['pct_carrier_mins']:.0f}%** "
            f"of their delays to carrier-controllable issues (maintenance, crew, operations) — "
            f"vs **{best_carrier['pct_carrier_mins']:.0f}%** for **{best_carrier['airline']}**. "
            f"Weather is rarely the primary culprit; airline operations matter most."
        )

    if not similar_df.empty:
        st.subheader(f"Alternative destinations from {origin_label}")
        fig2 = px.bar(
            similar_df.sort_values("on_time_rate"),
            x="on_time_rate", y="dest_city_name", orientation="h",
            color="on_time_rate",
            color_continuous_scale=[(0, C_BAD), (0.5, C_MID), (1, C_GOOD)],
            range_color=[50, 90],
            labels={"on_time_rate": "On-Time Rate (%)", "dest_city_name": "Destination"},
            title="On-Time Rate for Alternative Destinations",
        )
        fig2.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)


def render_summary_tab(
    route_airline: pd.DataFrame,
    by_time: pd.DataFrame,
    by_day: pd.DataFrame,
    monthly: pd.DataFrame,
    similar_df: pd.DataFrame,
    origin_label: str,
    dest_label: str,
):
    best       = route_airline.iloc[0]          if not route_airline.empty else None
    best_time  = by_time.sort_values("avg_delay").iloc[0]  if not by_time.empty  else None
    best_day   = by_day.sort_values("avg_delay").iloc[0]   if not by_day.empty   else None
    best_month = monthly.sort_values("avg_delay").iloc[0]  if not monthly.empty  else None

    # ── Header summary card ───────────────────────────────────────────────────
    yr_avg = monthly["avg_delay"].mean() if not monthly.empty else None
    risk_level = "Low"
    risk_color = "green"
    if yr_avg:
        if yr_avg > 22:
            risk_level, risk_color = "High",   "red"
        elif yr_avg > 15:
            risk_level, risk_color = "Medium", "orange"

    with st.container(border=True):
        st.markdown(f"**Route:** {origin_label} → {dest_label}")
        if yr_avg:
            st.markdown(
                f"**Overall delay risk:** :{risk_color}[{risk_level}] &nbsp;·&nbsp; "
                f"Year-round avg delay: **{yr_avg:.0f} min**"
            )

    # ── Recommendations ───────────────────────────────────────────────────────
    recs = []

    if best is not None:
        worst = route_airline.iloc[-1] if len(route_airline) > 1 else None
        tail = (
            f" {(best['on_time_rate'] - worst['on_time_rate']):.0f} percentage points better "
            f"than {worst['airline']}." if worst is not None else "."
        )
        recs.append(("✈", "#E1F5EE",
            f"**Book {best['airline']}.** {best['on_time_rate']:.1f}% on-time rate on this route.{tail}"
        ))

    if best_day is not None and best_time is not None:
        recs.append(("🕗", "#E6F1FB",
            f"**Depart on a {best_day['day_name']} {best_time['time_bucket'].lower()}.** "
            f"This combination averages ~{best_time['avg_delay']:.0f} min delay — "
            f"{best_day['day_name']} is the lowest-delay day on this route."
        ))

    if best_month is not None:
        best_month_name = MONTH_FULL.get(int(best_month["month"]), "")
        recs.append(("📅", "#FAEEDA",
            f"**Best month to fly this route: {best_month_name}.** "
            f"Avg delay is just {best_month['avg_delay']:.0f} min — "
            f"compared to {monthly['avg_delay'].max():.0f} min in the worst month."
        ))

    if best is not None and best["avg_delay"] > 20:
        recs.append(("⚠", "#FAECE7",
            f"**Add at least {int(best['avg_delay']) + 20} min buffer for connections.** "
            f"Even the best airline on this route averages {best['avg_delay']:.0f} min delay."
        ))

    if not similar_df.empty:
        alt = similar_df.iloc[0]
        recs.append(("🗺", "#EEEDFE",
            f"**Alternative: {alt['dest_city_name']}.** "
            f"{alt['on_time_rate']:.1f}% on-time rate from {origin_label} — "
            f"consider it if your final destination is nearby."
        ))

    for icon, bg, text_md in recs:
        cols = st.columns([0.04, 0.96])
        cols[0].markdown(
            f"<div style='background:{bg};border-radius:6px;padding:6px 8px;"
            f"text-align:center;font-size:16px;margin-top:4px'>{icon}</div>",
            unsafe_allow_html=True,
        )
        cols[1].markdown(text_md)
        st.write("")

    st.divider()
    sc1, sc2, sc3 = st.columns(3)
    if best is not None:
        sc1.metric("Best Airline", best["airline"], f"{best['on_time_rate']:.1f}% on-time")
    if best_day is not None and best_time is not None:
        sc2.metric(
            "Optimal Departure",
            f"{best_day['day_name']} {best_time['time_bucket']}",
            f"{best_time['avg_delay']:.0f} min avg delay",
        )
    if yr_avg:
        sc3.metric("Delay Risk", risk_level, f"{yr_avg:.0f} min year-round avg")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    data = load_data()
    rp, rtd = build_route_frames()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;padding-bottom:4px'>"
            f"<div style='background:{C_PRIMARY};border-radius:8px;padding:5px 9px;"
            "color:white;font-size:18px'>✈</div>"
            "<span style='font-size:20px;font-weight:700;color:#111'>FlightIQ</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("Powered by BTS On-Time Performance Data")
        st.divider()

        all_origin_cities: List[str] = sorted(rp["origin_city"].dropna().unique().tolist())

        st.markdown("**Trip Planner**")

        def search_origin(query: str) -> List[str]:
            if not query:
                return all_origin_cities[:50]
            q = query.strip().lower()
            return [c for c in all_origin_cities if q in c.lower()]

        origin_city: Optional[str] = st_searchbox(
            search_origin,
            placeholder="Type city name… e.g. New York, Atlanta",
            label="Origin city",
            key="origin_searchbox",
            default=None,
        )

        reachable: List[str] = sorted(
            rp[rp["origin_city"] == origin_city]["dest_city"].dropna().unique().tolist()
        ) if origin_city else []

        def search_dest(query: str) -> List[str]:
            if not query:
                return reachable[:50]
            q = query.strip().lower()
            return [c for c in reachable if q in c.lower()]

        dest_city: Optional[str] = st_searchbox(
            search_dest,
            placeholder="Type city name… e.g. Miami, Dallas",
            label="Destination city",
            key="dest_searchbox",
            default=None,
        )

        if origin_city and dest_city:
            priority = st.selectbox(
                "Prioritize airlines by",
                ["On-time performance", "Fewest delays", "Low cancellation risk"],
            )
        else:
            priority = "On-time performance"

        selected_month = 0
        day_pref       = "Flexible"
        specific_day   = "Monday"
        time_pref      = "Any"

        st.divider()
        if st.button("Clear cache / Refresh"):
            st.cache_data.clear()
            st.rerun()

        quick_placeholder = st.empty()

    # ── Network overview — always visible ─────────────────────────────────────
    st.markdown("## US Flight Network Overview")
    st.caption("High-level performance statistics across all US domestic flights in the dataset")
    render_network_overview(data)

    st.divider()
    st.markdown("## Route Analyzer")
    st.caption("Select an origin and destination in the sidebar to explore route-specific insights")

    if not (origin_city and dest_city):
        st.info("Use the **Trip Planner** in the sidebar to search and select an origin and destination city.")
        return

    st.divider()


    # ── Fetch route data from CSVs ─────────────────────────────────────────────
    route_airline = get_airline_stats(rp, rtd, origin_city, dest_city, day_pref, specific_day, time_pref, priority)
    by_time, by_day, heatmap_df = get_route_timing(rtd, origin_city, dest_city)
    monthly    = get_monthly_data(data["delay_monthly"])
    similar_df = get_similar_routes(rp, origin_city, dest_city)

    airline_names = route_airline["airline"].tolist() if not route_airline.empty else []
    causes_df  = get_causes_data(data["delay_causes"], airline_names)

    if route_airline.empty:
        st.warning(
            "No flights found for this route with the selected filters. "
            "Try relaxing the day or time filters."
        )
        return

    origin_label = origin_city
    dest_label   = dest_city
    best         = route_airline.iloc[0]

    # ── Fill sidebar quick insights ───────────────────────────────────────────
    best_day_row  = by_day.sort_values("avg_delay").iloc[0]  if not by_day.empty  else None
    best_time_row = by_time.sort_values("avg_delay").iloc[0] if not by_time.empty else None
    with quick_placeholder.container():
        st.markdown("**Quick Insights**")
        st.markdown(f"Best on-time rate: **{best['on_time_rate']:.1f}%**")
        st.markdown(f"Avg route delay: **{best['avg_delay']:.0f} min**")
        if best_day_row is not None:
            st.markdown(f"Safest day: **{best_day_row['day_name']}**")
        if best_time_row is not None:
            st.markdown(f"Safest time: **{best_time_row['time_bucket']}**")

    # ── Page header ───────────────────────────────────────────────────────────
    month_suffix = f" · {MONTH_FULL[selected_month]}" if selected_month > 0 else ""
    st.markdown(
        f"<h2 style='margin-bottom:2px'>{origin_label}  →  {dest_label}</h2>"
        f"<p style='color:gray;font-size:13px'>"
        f"Based on historical BTS data · "
        f"{int(route_airline['flights'].sum()):,} flights analyzed{month_suffix}</p>",
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Route On-Time Rate", f"{best['on_time_rate']:.1f}%")
    k2.metric("Avg Arrival Delay",  f"{best['avg_delay']:.0f} min")
    k3.metric("Best Airline",       best["airline"])
    if best_day_row is not None:
        k4.metric(
            "Best Day to Fly",
            best_day_row["day_name"],
            f"{best_day_row['avg_delay']:.0f} min avg",
        )

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_airlines, tab_timing, tab_seasons, tab_causes, tab_summary = st.tabs(
        ["Airlines", "Best Timing", "Seasonality", "Delay Causes", "Trip Summary"]
    )

    with tab_airlines:
        render_airlines_tab(route_airline)

    with tab_timing:
        render_timing_tab(by_time, by_day, heatmap_df)

    with tab_seasons:
        st.caption("Showing network-wide monthly trend (aggregated across all routes in the dataset)")
        render_seasonality_tab(monthly, 0)

    with tab_causes:
        render_causes_tab(causes_df, similar_df, origin_label)

    with tab_summary:
        render_summary_tab(
            route_airline, by_time, by_day, monthly, similar_df,
            origin_label, dest_label,
        )


if __name__ == "__main__":
    main()
