import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load .env from project root (works when run from scripts/ or project root)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def connect_to_postgres():
    return psycopg2.connect(
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
         host = 'localhost',
        port = '5432'
    )
