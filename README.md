# Airline On-Time Performance Analysis

## 📋 Project Overview

This project creates an automated pipeline to analyze airline on-time performance data and provide users with detailed insights about flight delays. When a user is booking a flight, they can enter their origin and destination to view comprehensive delay statistics for that route.

### Key Features
- **AWS S3 Integration**: Raw data is stored in S3; pipeline reads from and writes cleaned/normalized data to S3
- **PostgreSQL Database**: Normalized flight data is loaded into a PostgreSQL database for querying and analytics
- **Automated Data Pipeline**: Reads raw CSV from S3, cleans, normalizes, and loads into PostgreSQL
- **Data Cleaning & Processing**: Transforms raw data into analysis-ready format
- **Delay Analytics**: Analyzes patterns in flight delays across multiple dimensions
- **Interactive Streamlit Dashboard**: Visualizes route-level delay/cancellation risk and business insights

### Problem Statement
Users booking flights need to understand the likelihood and patterns of delays on their chosen route. This project provides actionable insights such as:
- What times of day flights typically experience delays
- Which days of the week have higher delay rates
- Which airlines have the worst/best on-time performance
- Historical delay patterns for specific routes

## 📊 Data Source

All data is sourced from the **Bureau of Transportation Statistics (BTS)**:
- **Source**: [https://www.transtats.bts.gov/Tables.asp?QO_VQ=EFD&QO_anzr=Nv4yv0r%FDb0-gvzr%FDcr4s14zn0pr%FDQn6n&QO_fu146_anzr=b0-gvzr](https://www.transtats.bts.gov/Tables.asp?QO_VQ=EFD&QO_anzr=Nv4yv0r%FDb0-gvzr%FDcr4s14zn0pr%FDQn6n&QO_fu146_anzr=b0-gvzr)
- **Dataset**: T_ONTIME_REPORTING (On-Time Reporting of U.S. Airlines)
- **Storage**: Raw data is stored in AWS S3 bucket `airline-analytics-raw-data`

## 📁 Project Structure

```
Airline_OnTime_Performance/
├── README.md
├── .env                            # Environment variables
├── requirements.txt
├── streamlit_app.py                # Streamlit dashboard app
├── run_pipeline.py                 # Runs data + analytics pipeline
├── ipynb_files/
│   ├── clean.ipynb                 # Data cleaning notebook
│   └── normalize.ipynb             # Data normalization notebook
├── scripts/
│   ├── main.py                     # Main pipeline (S3 → clean → normalize → PostgreSQL)
│   ├── cleaning.py                 # Data cleaning logic
│   ├── normalization.py            # Data normalization logic
│   ├── analysis.py                 # Route/airline delay analysis
│   ├── s3_utils.py                 # S3 read/write utilities
│   ├── postgre_utils.py            # PostgreSQL connection utilities
│   └── upload_raw_data.py          # Script to upload local CSV files to S3
└── Data/
    ├── Data Dictionary.csv         # Field descriptions for the dataset
    └── LookUp_Tables/              # Reference tables (optional)
```

## 🔄 Pipeline Flow

### 1. **Data in S3**
- **Raw data**: `s3://airline-analytics-raw-data/raw/{year}/{month}.csv`
- **Cleaned data**: `s3://airline-analytics-raw-data/cleaned/{year}/{month}.parquet`
- **Normalized data**: `s3://airline-analytics-raw-data/normalized/{year}/{month}.parquet`

### 2. **Pipeline Stages**
1. **Read from S3**: Fetches raw CSV for each month
2. **Cleaning**: Column selection, null/duplicate removal, type conversion, string standardization
3. **Normalization**: Date dimensions, time buckets, delay flag corrections
4. **Write to S3**: Saves cleaned and normalized Parquet files
5. **Load to PostgreSQL**: Copies normalized data into `fact_flights` table

### 3. **Running the Pipeline**
```bash
python run_pipeline.py
```

### 4. **Launching the Dashboard**
```bash
streamlit run streamlit_app.py
```


## ☁️ AWS S3 Setup

1. Create an S3 bucket (e.g., `airline-analytics-raw-data`)
2. Configure AWS credentials (see Environment Setup below)
3. Upload raw data using the upload script:
   ```bash
   python scripts/upload_raw_data.py
   ```
   - Expects local files: `Data/01_2025.csv`, `Data/02_2025.csv`, etc.
   - Uploads to `raw/2025/{month}.csv` in the bucket

## 🐘 PostgreSQL Setup

1. Create a database named `airline_analytics`
2. Create the `fact_flights` table with columns matching the normalized schema (see `scripts/main.py` for column list)
3. Add credentials to `.env` (see Environment Setup)

## 🔐 Environment Setup

Create a `.env` file in the project root (do not commit this file):

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

## 🛠️ Technology Stack

- **Data Processing**: Python, Pandas, NumPy
- **Cloud Storage**: AWS S3 (boto3)
- **Database**: PostgreSQL (psycopg2, SQLAlchemy)
- **Dashboard**: Streamlit, Plotly
- **Notebooks**: Jupyter
- **Data Formats**: CSV (raw), Parquet (cleaned/normalized)

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` with your PostgreSQL and AWS credentials
4. Set up PostgreSQL database and `fact_flights` table
5. Upload raw data to S3 (or place monthly CSVs in `Data/` and run `upload_raw_data.py`)
6. Run the pipeline: `python run_pipeline.py`
7. Launch dashboard: `streamlit run streamlit_app.py`

## 📝 Scripts Reference

| Script | Purpose |
|--------|---------|
| `main.py` | Full pipeline: S3 → clean → normalize → PostgreSQL |
| `cleaning.py` | Data cleaning (select cols, null/dup removal, type conversion) |
| `normalization.py` | Feature engineering (date dims, time buckets, delay corrections) |
| `s3_utils.py` | Read/write data to/from S3 |
| `postgre_utils.py` | PostgreSQL connection using credentials from `.env` |
| `upload_raw_data.py` | Upload local monthly CSVs to S3 |
| `analysis.py` | Route/airline/day/hour delay summaries |
| `run_pipeline.py` | Orchestrates data pipeline + analytics generation |
| `streamlit_app.py` | User + business dashboard with route filters and insights |

## 📚 Data Dictionary

See `Data/Data Dictionary.csv` for detailed field descriptions of the T_ONTIME_REPORTING dataset.

## 📈 Key Metrics

The analysis focuses on the following metrics:
- **Departure Delay**: Minutes late from scheduled departure
- **Arrival Delay**: Minutes late from scheduled arrival
- **On-Time Performance**: % of flights arriving on-time
- **Cancellation Rate**: % of flights cancelled
- **Delay by Carrier**: Performance comparison across airlines
- **Route Statistics**: Delay patterns by origin/destination pair

## 🔜 Next Steps (Planned)

1. **Analyze the business for 2025 and validate** — Run analysis on 2025 data and validate the pipeline, S3, and PostgreSQL connections are working correctly
2. **Load more data into S3** — Upload additional months/years of data to S3 for broader analysis
3. **Expand dashboard capabilities** — Add advanced business KPI views, route benchmarking, and stakeholder-focused pages
4. **Automate monthly data loading** — Implement automated extraction of next month's data from BTS and load it into S3 and the database

## 📄 License

This project uses publicly available data from the Bureau of Transportation Statistics.

## 👤 Author

Sneha Uppu

---
