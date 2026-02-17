from cleaning import clean_flights

def run_pipeline():
    input_path = '/Users/snehauppu/Documents/Airline_OnTime_Performance/Data/T_ONTIME_REPORTING.csv'
    output_path = 'data/cleaned_data.parquet'

    clean_flights(input_path, output_path)

if __name__ == "__main__":
    run_pipeline()