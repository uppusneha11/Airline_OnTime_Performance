import io
from pathlib import Path
import boto3
import pandas as pd
from dotenv import load_dotenv

# Load .env so AWS credentials are available
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

s3 = boto3.client("s3")

def upload_file_to_s3(local_path, bucket_name, s3_key):
    s3.upload_file(local_path, bucket_name, s3_key)

def read_from_s3(bucket_name, key):
    obj = s3.get_object(Bucket = bucket_name, Key = key)
    return pd.read_csv(obj["Body"], low_memory = False)

def write_to_s3(df, bucket_name, key):
    buffer = io.BytesIO()
    df.to_parquet(buffer, index = False)

    s3.put_object(
        Bucket = bucket_name,
        Key = key,
        Body = buffer.getvalue()
    )