from s3_utils import upload_file_to_s3

BUCKET_NAME = "airline-analytics-raw-data"

months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

for month in months:
    local_path = f"/Users/snehauppu/Documents/Airline_OnTime_Performance/Data/{month}_2025.csv"
    s3_key = f"raw/2025/{month}.csv"

    upload_file_to_s3(local_path, BUCKET_NAME, s3_key)