from .cleaning import clean_flights
from .normalization import normalize_flights
from .s3_utils import read_from_s3, write_to_s3
from .postgre_utils import delete_existing_data, load_to_postgres, rebuild_dim_city_airports

BUCKET = "airline-analytics-raw-data"

def process_month(year, month):
    raw_key = f"raw/{year}/{month}.csv"
    cleaned_key = f"cleaned/{year}/{month}.parquet"
    normalized_key = f"normalized/{year}/{month}.parquet"

    print(f"\n Processing {year}-{month}")

    # Delete existing data to avoid duplicates
    delete_existing_data(year, month)
    # Read raw data from S3
    df_raw = read_from_s3(BUCKET, raw_key)
    # Clean data
    df_clean = clean_flights(df_raw)
    write_to_s3(df_clean, BUCKET, cleaned_key)
    # Normalize data
    df_norm = normalize_flights(df_clean)
    write_to_s3(df_norm, BUCKET, normalized_key)
    # Load data to PostgreSQL
    load_to_postgres(df_norm)

    print(f"Finished {year}-{month}")


def run_data_pipeline():
    months = ["01","02","03","04","05","06","07","08","09","10"]

    for month in months:
        process_month("2025", month)

    # Refresh city-airport dimension after loading all months
    rebuild_dim_city_airports()


if __name__ == "__main__":
    run_data_pipeline()