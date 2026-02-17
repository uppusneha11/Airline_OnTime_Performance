import pandas as pd 

# Column Selection
def select_cols(df):
    return df[[
        'FL_DATE','OP_UNIQUE_CARRIER','OP_CARRIER_FL_NUM','ORIGIN_AIRPORT_ID','ORIGIN_CITY_NAME',
        'ORIGIN_STATE_ABR','DEST_AIRPORT_ID','DEST_CITY_NAME','DEST_STATE_ABR','CRS_DEP_TIME',
        'DEP_TIME','DEP_DELAY_NEW','DEP_DEL15','CRS_ARR_TIME','ARR_TIME', 'ARR_DELAY_NEW',
        'ARR_DEL15','CANCELLED','CANCELLATION_CODE','DIVERTED','DISTANCE',
        'DISTANCE_GROUP','CARRIER_DELAY','WEATHER_DELAY','NAS_DELAY','SECURITY_DELAY',
        'LATE_AIRCRAFT_DELAY','DIV_AIRPORT_LANDINGS','DIV_REACHED_DEST','DIV_ARR_DELAY',
        'DIV_DISTANCE','DIV1_AIRPORT','DIV2_AIRPORT'
    ]].copy()


# Removing the null and duplicate columns based on selected key columns
def null_duplicate(df):
    key_cols = [
        "FL_DATE",
        "OP_UNIQUE_CARRIER",
        "OP_CARRIER_FL_NUM",
        "ORIGIN_AIRPORT_ID",
        "DEST_AIRPORT_ID"
    ]

    df = df.dropna(subset = key_cols)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset = key_cols, keep = "first")

    return df

# Type Conversion
def type_convert(df):
    df['FL_DATE'] = pd.to_datetime(df["FL_DATE"], format = "%m/%d/%Y %I:%M:%S %p", errors = 'coerce')

    df.loc[:, "CANCELLED"] = pd.to_numeric(df["CANCELLED"], errors = "coerce")
    df.loc[:, "DIVERTED"] = pd.to_numeric(df["DIVERTED"], errors = 'coerce')
    df.loc[:, "CANCELLED"] = df["CANCELLED"].fillna(0).astype(int)
    df.loc[:, "DIVERTED"] = df["DIVERTED"].fillna(0).astype(int)

    return df

# String Cleanup
def string_std(df):
    string_cols = [
        "OP_UNIQUE_CARRIER",
        "ORIGIN_STATE_ABR",
        "DEST_STATE_ABR",
        "ORIGIN_CITY_NAME",
        "DEST_CITY_NAME",
        "CANCELLATION_CODE",
        "DIV1_AIRPORT",
        "DIV2_AIRPORT"
    ]

    code_cols = [
        "OP_UNIQUE_CARRIER",
        "ORIGIN_STATE_ABR",
        "DEST_STATE_ABR",
        "CANCELLATION_CODE",
        "DIV1_AIRPORT",
        "DIV2_AIRPORT"
    ]

    city_cols = [
        "ORIGIN_CITY_NAME",
        "DEST_CITY_NAME",
    ]
    
    for col in string_cols:
        if col in df.columns:
            df.loc[:, col] = df[col].astype(str).str.strip()
            df.loc[:, col] = df[col].replace(["nan","NAN"], pd.NA)

    for col in code_cols:
        if col in df.columns:
            df.loc[:, col] = df[col].str.upper()

    for col in city_cols:
        if col in df.columns:
            df.loc[:, col] = df[col].str.title()
    return df
# Validation Checks
def valid(df):
    key_cols = [
        "FL_DATE",
        "OP_UNIQUE_CARRIER",
        "OP_CARRIER_FL_NUM",
        "ORIGIN_AIRPORT_ID",
        "DEST_AIRPORT_ID"
    ]

    string_cols = [
        "OP_UNIQUE_CARRIER",
        "ORIGIN_STATE_ABR",
        "DEST_STATE_ABR",
        "ORIGIN_CITY_NAME",
        "DEST_CITY_NAME",
        "CANCELLATION_CODE",
        "DIV1_AIRPORT",
        "DIV2_AIRPORT"
    ]

    assert df.duplicated(subset = key_cols).sum() == 0, "Duplicates found in key columns"
    assert df[key_cols].isnull().sum().sum() == 0, "Nulls found in key columns"
    assert set(df["CANCELLED"].unique()).issubset({0,1}), "Cancelled values are not 0 or 1"
    assert set(df["DIVERTED"].unique()).issubset({0,1}), "Diverted values are not 0 and 1"
    assert str(df["FL_DATE"].dtype).startswith("datetime"), "Flight Date is not a datetime"

    for col in string_cols:
        if col in df.columns:
            assert "NaN" not in df[col].astype(str).unique(), f"{col} contains NaN"

# The main cleaning function
def clean_flights(input_path, output_path):
    df = pd.read_csv(
        input_path,
        low_memory = False,
        dtype = {
            "OP_UNIQUE_CARRIER": "string",
            "ORIGIN_STATE_ABR": "string",
            "DEST_STATE_ABR": "string",
            }
        )

    df = select_cols(df)
    df = null_duplicate(df)
    df = type_convert(df)
    df = string_std(df)
    valid(df)

    df.to_parquet(output_path, index = False)
    return df