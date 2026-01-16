# Airline On-Time Performance Analysis

## 📋 Project Overview

This project creates an automated pipeline to analyze airline on-time performance data and provide users with detailed insights about flight delays. When a user is booking a flight, they can enter their origin and destination to view comprehensive delay statistics for that route.

### Key Features
- **Automatic Data Pipeline**: Downloads the latest airline performance data from official sources
- **Data Cleaning & Processing**: Transforms raw data into analysis-ready format
- **Delay Analytics**: Analyzes patterns in flight delays across multiple dimensions
- **Interactive Dashboard**: Visualizes delay patterns and insights (in development)

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

## 📁 Project Structure

```
Airline_OnTime_Performance/
├── README.md                          # Project documentation
├── clean.ipynb                        # Data cleaning and preprocessing notebook
├── Data/
│   ├── Data Dictionary.csv            # Field descriptions for the dataset
│   ├── T_ONTIME_REPORTING.csv         # Main airline performance data (not tracked in git)
│   └── LookUp_Tables/
│       ├── L_AIRLINE_ID.csv
│       ├── L_AIRPORT_ID.csv
│       ├── L_AIRPORT_SEQ_ID.csv
│       ├── L_AIRPORT.csv
│       ├── L_CANCELLATION.csv
│       ├── L_CARRIER_HISTORY.csv
│       ├── L_CITY_MARKET_ID.csv
│       ├── L_DEPARRBLK.csv
│       ├── L_DISTANCE_GROUP_250.csv
│       ├── L_DIVERSIONS.csv
│       ├── L_MONTHS.csv
│       ├── L_ONTIME_DELAY_GROUPS.csv
│       ├── L_QUARTERS.csv
│       ├── L_STATE_ABR_AVIATION.csv
│       ├── L_STATE_FIPS.csv
│       ├── L_UNIQUE_CARRIERS.csv
│       ├── L_WEEKDAYS.csv
│       ├── L_WORLD_AREA_CODES.csv
│       └── L_YESNO_RESP.csv
```

## 🔄 Pipeline Stages (Planned)

### 1. **Data Download**
- Automated script to fetch latest data from BTS
- Scheduled updates

### 2. **Data Cleaning & Preprocessing** 
- Handle missing values
- Standardize formats
- Join with lookup tables
- Create derived features (delay indicators, time periods, etc.)

### 3. **Data Analysis**
- Temporal analysis (time of day, day of week patterns)
- Airline performance analysis
- Route-specific statistics
- Seasonal trends

### 4. **Dashboard Development** 
- Interactive web interface
- Origin/destination flight search
- Real-time delay metrics
- Historical trend visualizations
- Predictive insights

## 🛠️ Technology Stack

- **Data Processing**: Python, Pandas, NumPy
- **Notebooks**: Jupyter
- **Dashboard**: To be determined
- **Data Storage**: CSV files

## 📝 Notebooks

### clean.ipynb
Main data cleaning and preprocessing notebook. Contains:
- Data loading and exploration
- Data quality checks
- Missing value handling
- Feature engineering
- Lookup table joins

## 🚀 Getting Started

1. Clone the repository
2. Download the data from the BTS source (place in `Data/` folder)
3. Install required dependencies: `pip install -r requirements.txt`
4. Run `clean.ipynb` to process the data
5. Proceed with analysis notebooks

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

## 📄 License

This project uses publicly available data from the Bureau of Transportation Statistics.

## 👤 Author

Sneha Uppu

---
