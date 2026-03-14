from scripts.main import run_data_pipeline
from analytics.run_analytics import run_analytics_pipeline


def run_pipeline():

    run_data_pipeline()

    run_analytics_pipeline()


if __name__ == "__main__":
    run_pipeline()