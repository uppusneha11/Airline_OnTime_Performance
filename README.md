# Airline On-Time Performance Analysis

## Live App

**[FlightIQ — Streamlit Dashboard](https://flightiq.streamlit.app/)**

## Project Overview

This project creates an automated pipeline to analyze airline on-time performance data and provide users with detailed insights about flight delays. When a user is booking a flight, they can enter their origin and destination to view comprehensive delay statistics for that route.

### Key Features
- **AWS S3 Integration**: Raw data is stored in S3; pipeline reads from and writes cleaned/normalized data to S3
- **PostgreSQL Database**: Normalized flight data is loaded into a PostgreSQL database for querying and analytics
- **Automated Data Pipeline**: Reads raw CSV from S3, cleans, normalizes, and loads into PostgreSQL
- **Analytics Export Pipeline**: Generates 9 pre-aggregated CSV tables from the database for Tableau reporting
- **Interactive Streamlit Dashboard**: Visualizes route-level delay/cancellation risk and network-wide business insights — deployed at [flightiq.streamlit.app](https://flightiq.streamlit.app/)
- **Tableau Dashboard**: Published interactive dashboard with delay heatmaps, maps, trend lines, and airline comparisons

### Problem Statement
Users booking flights need to understand the likelihood and patterns of delays on their chosen route. This project provides actionable insights such as:
- What times of day flights typically experience delays
- Which days of the week have higher delay rates
- Which airlines have the worst/best on-time performance
- Historical delay patterns for specific routes
- Why airlines are delayed (carrier issues vs. weather vs. air traffic control)

---

## Tableau Dashboard

**[View the published Tableau Dashboard](https://public.tableau.com/app/profile/sneha.uppu/viz/AirlineOn-TimePerformance_17736107336330/Dashboard#1)**

The Tableau dashboard is built from the analytics tables exported by this pipeline and includes:
- Airline reliability ranking and on-time rate comparison
- Airport delay map (departure and arrival delays plotted by lat/lon)
- Delay cause breakdown — stacked bar showing % of delay attributed to carrier, weather, NAS, late aircraft, and security
- Month-over-month delay trend — seasonality line chart
- Day-of-week and time-of-day delay heatmap
- Route-level performance by airline, day, and time bucket

> **Note on geographic data:** The airport latitude/longitude coordinates used for the map visualization were sourced from a separate BTS dataset — the [Master Coordinate table (T_MASTER_CORD)](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FLL) — which provides airport coordinates, city names, state codes, and timezone information. This was joined to the analytics tables on `airport_id` during the enrichment step.

---

## Data Source

All data is sourced from the **Bureau of Transportation Statistics (BTS)**:
- **Source**: [BTS On-Time Reporting](https://www.transtats.bts.gov/Tables.asp?QO_VQ=EFD&QO_anzr=Nv4yv0r%FDb0-gvzr%FDcr4s14zn0pr%FDQn6n&QO_fu146_anzr=b0-gvzr)
- **Dataset**: T_ONTIME_REPORTING (On-Time Reporting of U.S. Airlines)
- **Storage**: Raw data is stored in AWS S3 bucket `airline-analytics-raw-data`

---

## Project Structure

```
Airline_OnTime_Performance/
├── README.md
├── .env                                # Environment variables (not committed)
├── requirements.txt
├── run_pipeline.py                     # Orchestrates data + analytics pipeline
├── streamlit_app.py                    # Interactive Streamlit route analyzer
├── PostgreSQL_code.sql                 # Table creation SQL
│
├── scripts/
│   ├── main.py                         # Full pipeline: S3 → clean → normalize → PostgreSQL
│   ├── cleaning.py                     # Column selection, null/dup removal, type conversion
│   ├── normalization.py                # Date dimensions, time buckets, delay corrections
│   ├── s3_utils.py                     # S3 read/write utilities
│   ├── postgre_utils.py                # PostgreSQL connection + dim_city_airports builder
│   └── upload_raw_data.py              # Upload local CSVs to S3
│
├── analytics/
│   ├── queries.py                      # All SQL queries (one per analytics table)
│   ├── enrichment.py                   # Lookup loading + post-query data enrichment
│   ├── run_analytics.py                # Thin orchestrator — runs all queries and saves CSVs
│   └── config.py                       # Output directory path config
│
├── analytics_tables/                   # Generated CSVs (Tableau data source)
│   ├── airline_performance.csv
│   ├── airport_departure_delays.csv    # Includes lat/lon for map
│   ├── airport_arrival_delays.csv      # Includes lat/lon for map
│   ├── delay_by_day.csv
│   ├── delay_by_time_bucket.csv
│   ├── route_performance.csv
│   ├── route_time_day_analysis.csv
│   ├── delay_cause_by_airline.csv      # Delay cause % breakdown per airline
│   └── delay_trend_by_month.csv        # Month-over-month trend with cause breakdown
│
├── ipynb_files/
│   ├── clean.ipynb                     # Exploratory cleaning notebook
│   └── normalize.ipynb                 # Exploratory normalization notebook
│
└── Data/
    ├── Data Dictionary.csv             # Field descriptions for T_ONTIME_REPORTING
    ├── Airport Info.csv                # Airport coordinates (lat/lon) from BTS
    └── LookUp_Tables/                  # BTS reference/dimension tables
```

---

## Pipeline Flow

### 1. Data in S3
- **Raw data**: `s3://airline-analytics-raw-data/raw/{year}/{month}.csv`
- **Cleaned data**: `s3://airline-analytics-raw-data/cleaned/{year}/{month}.parquet`
- **Normalized data**: `s3://airline-analytics-raw-data/normalized/{year}/{month}.parquet`

### 2. Data Pipeline Stages
1. **Read from S3** — Fetches raw CSV for each month
2. **Cleaning** — Column selection, null/duplicate removal, type conversion, string standardization
3. **Normalization** — Date dimensions, time buckets, delay flag corrections
4. **Write to S3** — Saves cleaned and normalized Parquet files
5. **Load to PostgreSQL** — Copies normalized data into `fact_flights` table

### 3. Analytics Export Stages
After the data pipeline completes, the analytics pipeline:
1. **Runs SQL queries** against `fact_flights` (defined in `analytics/queries.py`)
2. **Enriches results** with human-readable names and coordinates (defined in `analytics/enrichment.py`):
   - Airport names from `L_AIRPORT_ID.csv`
   - Airline names from `L_UNIQUE_CARRIERS.csv`
   - Latitude/longitude from `Airport Info.csv` (filtered to current airports only)
   - Day names, month names, delay cause percentages
3. **Exports 9 CSVs** to `analytics_tables/` for use in Tableau

### 4. Running the Full Pipeline
```bash
python run_pipeline.py
```

### 5. Launching the Streamlit Dashboard
```bash
streamlit run streamlit_app.py
```

---

## Streamlit Dashboard

**Live:** [flightiq.streamlit.app](https://flightiq.streamlit.app/)

The Streamlit app (`streamlit_app.py`) reads directly from the pre-aggregated CSVs in `analytics_tables/` — no database connection required. It has two main sections:

**US Flight Network Overview** — Always-visible network-wide KPIs:
- Total flights analyzed, airlines and airports covered, years of data
- Average delay rate, cancellation rate, and average delay time
- Most reliable airline
- Delay cause breakdown pie chart (carrier, weather, NAS, late aircraft, security)
- Airline reliability ranking bar chart

**Route Analyzer** — Activated when an origin and destination are selected:
- City search with metro area grouping (e.g., "New York Area" combines JFK, LGA, and EWR)
- **Airlines tab** — On-time rate, avg delay, and cancellation risk comparison by airline, sortable by priority
- **Best Timing tab** — Avg delay by time of day, day of week, and a day × time heatmap
- **Seasonality tab** — Network-wide month-over-month delay trend
- **Delay Causes tab** — Stacked bar of delay cause breakdown by airline; alternative destinations
- **Trip Summary tab** — Personalized recommendations (best airline, best day, best month, connection buffer advice)

---

## Analytics Tables Reference

| CSV File | Description | Key Columns |
|---|---|---|
| `airline_performance` | Per-airline delay/cancellation summary | `airline_name`, `delay_rate`, `on_time_rate`, `cancellation_rate` |
| `airport_departure_delays` | Departure delay stats per airport | `airport_name`, `iata_code`, `latitude`, `longitude`, `avg_departure_delay` |
| `airport_arrival_delays` | Arrival delay stats per airport | `airport_name`, `iata_code`, `latitude`, `longitude`, `avg_arrival_delay` |
| `delay_by_day` | Delay patterns by day of week | `day_name`, `delay_rate`, `avg_delay` |
| `delay_by_time_bucket` | Delay patterns by time of day | `time_bucket`, `delay_rate`, `avg_delay` |
| `route_performance` | Per-route per-airline delay summary | `origin_airport_name`, `dest_airport_name`, `airline_name`, `delay_rate` |
| `route_time_day_analysis` | Route delay by airline, day, and time bucket | `day_name`, `time_bucket`, `delay_rate` |
| `delay_cause_by_airline` | Delay cause breakdown per airline | `airline_name`, `pct_carrier_delay`, `pct_weather_delay`, `pct_nas_delay`, `pct_late_aircraft_delay`, `pct_security_delay` |
| `delay_trend_by_month` | Month-over-month delay trend | `year_month`, `avg_delay`, `delay_rate`, avg per cause |

> Note: `airport_departure_delays` and `airport_arrival_delays` share a common `airport_id` column for joining in Tableau.

---

## AWS S3 Setup

1. Create an S3 bucket (e.g., `airline-analytics-raw-data`)
2. Configure AWS credentials (see Environment Setup below)
3. Upload raw data using the upload script:
   ```bash
   python scripts/upload_raw_data.py
   ```
   - Expects local files: `Data/01_2025.csv`, `Data/02_2025.csv`, etc.
   - Uploads to `raw/2025/{month}.csv` in the bucket

---

## PostgreSQL Setup

1. Create a database named `airline_analytics`
2. Run `PostgreSQL_code.sql` to create the `fact_flights` and `dim_city_airports` tables
3. Add credentials to `.env` (see Environment Setup)

---

## Environment Setup

Create a `.env` file in the project root (never commit this file):

```env
# PostgreSQL
PGDATABASE=airline_analytics
PGUSER=your_username
PGPASSWORD=your_password

# AWS (for S3 access)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

**Credential options for AWS:**
- **Option A**: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to `.env`
- **Option B**: Run `aws configure` and store credentials in `~/.aws/credentials`

---

## Technology Stack

- **Data Processing**: Python, Pandas, NumPy
- **Cloud Storage**: AWS S3 (boto3)
- **Database**: PostgreSQL (psycopg2, SQLAlchemy)
- **Streamlit Dashboard**: Streamlit, Plotly
- **Tableau Dashboard**: Tableau Public
- **Notebooks**: Jupyter
- **Data Formats**: CSV (raw/export), Parquet (cleaned/normalized)

---

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` with your PostgreSQL and AWS credentials
4. Set up PostgreSQL: run `PostgreSQL_code.sql`
5. Upload raw data to S3 (or place monthly CSVs in `Data/` and run `scripts/upload_raw_data.py`)
6. Run the full pipeline: `python run_pipeline.py`
7. Launch the Streamlit dashboard: `streamlit run streamlit_app.py`
8. Open Tableau and connect to the CSVs in `analytics_tables/` for the Tableau dashboard

---

## Scripts Reference

| File | Purpose |
|---|---|
| `run_pipeline.py` | Entry point — runs data pipeline then analytics export |
| `scripts/main.py` | Full data pipeline: S3 → clean → normalize → PostgreSQL |
| `scripts/cleaning.py` | Data cleaning logic |
| `scripts/normalization.py` | Feature engineering (date dims, time buckets, delay corrections) |
| `scripts/s3_utils.py` | Read/write data to/from S3 |
| `scripts/postgre_utils.py` | PostgreSQL connection + `dim_city_airports` dimension table builder |
| `scripts/upload_raw_data.py` | Upload local monthly CSVs to S3 |
| `analytics/queries.py` | SQL query strings for all 9 analytics tables |
| `analytics/enrichment.py` | Lookup loading + post-query enrichment (names, coordinates, percentages) |
| `analytics/run_analytics.py` | Orchestrates analytics queries and CSV exports |
| `analytics/config.py` | Output directory configuration |
| `streamlit_app.py` | Interactive Streamlit route analyzer and delay dashboard |

---

## Key Metrics

The analysis focuses on the following metrics:
- **Departure Delay**: Minutes late from scheduled departure
- **Arrival Delay**: Minutes late from scheduled arrival
- **On-Time Performance**: % of flights arriving on-time (within 15 minutes)
- **Cancellation Rate**: % of flights cancelled
- **Delay by Carrier**: Performance comparison across airlines
- **Route Statistics**: Delay patterns by origin/destination pair
- **Delay Causes**: Breakdown by carrier, weather, NAS, late aircraft, and security

---

## Data Dictionary

See `Data/Data Dictionary.csv` for detailed field descriptions of the T_ONTIME_REPORTING dataset.

---

## License

This project uses publicly available data from the Bureau of Transportation Statistics.

## Author

Sneha Uppu
