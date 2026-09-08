"""
One-shot script: deletes all rows from scan_events, scan_results, scans, and users.
Run from the project root: venv/Scripts/python scripts/reset_db.py
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

client = create_client(url, key)

tables = ["scan_events", "scan_results", "scans", "users"]

for table in tables:
    try:
        # neq on id to match every row (Supabase requires a filter)
        res = client.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        deleted = len(res.data) if res.data else "?"
        print(f"  {table}: deleted {deleted} rows")
    except Exception as e:
        print(f"  {table}: ERROR — {e}")

print("\nDone. Database is clean.")
