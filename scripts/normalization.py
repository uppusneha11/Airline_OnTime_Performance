import pandas as pd
from cleaning import null_duplicate

# Loading the data
def load_data(input_path):
    return pd.read_parquet(input_path)

# Creating Date Dimensions
def create_date(df):
    df["YEAR"] = df["FL_DATE"].dt.year
    df["QUARTER"]= df["FL_DATE"].dt.quarter
    df["MONTH"] = df["FL_DATE"].dt.month
    df["DAY_OF_WEEK"] = df["FL_DATE"].dt.dayofweek + 1
    df["DAY_OF_MONTH"] = df["FL_DATE"].dt.day

    return df

# Fix 2400 Time values as 2400 is same as 0000
def fix_midnight_values(df):
    time_cols = ["CRS_DEP_TIME", "CRS_ARR_TIME", "DEP_TIME", "ARR_TIME"]
    
    for col in time_cols:
        df.loc[df[col] == 2400, col] = 0
        df.loc[df[col] == 2400, "FL_DATE"] = df.loc[df[col] == 2400, "FL_DATE"] + pd.Timedelta(days=1)

        # Calling the null_duplicate function from cleaning.py because changing the date-time may result in some duplicates rows
        df = null_duplicate(df) 

    return df

# Extact Hour Columns
def extract_hour_columns(df):
    df["CRS_DEP_HOUR"] = (df["CRS_DEP_TIME"] // 100).astype("Int64")
    df["CRS_ARR_HOUR"] = (df["CRS_ARR_TIME"] // 100).astype("Int64")
    df["DEP_HOUR"] = (df["DEP_TIME"] // 100).astype("Int64")
    df["ARR_HOUR"] = (df["ARR_TIME"] // 100).astype("Int64")

    return df

# Time Bucket Logic
def time_bkt(hour):
    if pd.isna(hour):
        return pd.NA
    elif 0 <= hour <= 5:
        return "Late Night/Early Morning"
    elif 6 <= hour <= 11:
        return "Morning" 
    elif 12 <= hour <= 16:
        return "Afternoon"
    elif 17 <= hour <= 20:
        return "Evening"
    else:
        return "Night"

# Creating the Time Bucket Column
def create_time_bucket(df):
    df["TIME_BUCKET"] = df["SCH_DEP_HOUR"].apply(time_bkt)
    return df

# Remove Delay Values for Cancelled Flights and Correct Delay Flag Inconsistencies
def clean_cancelled_delays(df):
    cancelled_mask = df["CANCELLED"] == 1
    delay_cols = ["DEP_DEL15", "ARR_DEL15", "DEP_DELAY_NEW", "ARR_DELAY_NEW"]

    df.loc[cancelled_mask, delay_cols] = pd.NA

    df.loc[(df["DEP_DEL15"] == 1) & (df["DEP_DELAY_NEW"] < 15), "DEP_DEL15"] = 0
    df.loc[(df["DEP_DEL15"] == 0) & (df["DEP_DELAY_NEW"] > 15), "DEP_DEL15"] = 1
    df.loc[(df["ARR_DEL15"] == 1) & (df["ARR_DELAY_NEW"] < 15), "ARR_DEL15"] = 0
    df.loc[(df["ARR_DEL15"] == 0) & (df["ARR_DELAY_NEW"] > 15), "ARR_DEL15"] = 1

    return df

# Main Normalization Function
def normalize_flights(input_path, output_path):
    df = load_data(input_path)
    df = create_date(df)
    df = fix_midnight_values(df)
    df = extract_hour_columns(df)
    df = create_time_bucket(df)
    df = clean_cancelled_delays(df)

    df.to_parquet(output_path, index=False)
    return df