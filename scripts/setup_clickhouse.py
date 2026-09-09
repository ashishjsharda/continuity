#!/usr/bin/env python3
"""
Helper to apply schema + seed data to a ClickHouse instance.
Requires clickhouse-connect or the native client.

Usage:
  python scripts/setup_clickhouse.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    import clickhouse_connect
except ImportError:
    print("Install clickhouse-connect: pip install clickhouse-connect")
    raise

ROOT = Path(__file__).resolve().parent.parent

def main():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )

    print("Connected to ClickHouse")

    schema_sql = (ROOT / "schema" / "production_schema.sql").read_text()
    # Split on statements (simple)
    for stmt in schema_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            print(f"Executing schema statement ({len(stmt)} chars)...")
            client.command(stmt)

    seed_sql = (ROOT / "data" / "seed_production.sql").read_text()
    for stmt in seed_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            print(f"Executing seed statement...")
            client.command(stmt)

    print("\n✅ Schema and seed data applied.")
    print("Tables:")
    rows = client.query("SHOW TABLES FROM production_memory").result_rows
    for r in rows:
        print(" -", r[0])

if __name__ == "__main__":
    main()
