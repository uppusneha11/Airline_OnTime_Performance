from cleaning import clean_flights
from normalization import normalize_flights

def run_pipeline():
    input_path = '/Users/snehauppu/Documents/Airline_OnTime_Performance/Data/T_ONTIME_REPORTING.csv'
    output_path = 'data/cleaned_data.parquet'
    output_path_normalized = 'data/normalized_data.parquet'

    clean_flights(input_path, output_path)
    normalize_flights(output_path, output_path_normalized)

if __name__ == "__main__":
    run_pipeline()