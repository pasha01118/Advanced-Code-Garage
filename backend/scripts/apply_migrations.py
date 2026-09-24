"""Idempotent SQL migrator for ACG's Supabase schema.

Usage:
    export DATABASE_URL="postgresql://postgres.<ref>:<password>@<pooler-host>:6543/postgres"
    python scripts/apply_migrations.py

Applies every .sql file in backend/sql/ in lexicographic order.
Old files that have already been tracked in the migrations table are skipped.
"""

import os
from pathlib import Path

import psycopg

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required (pooled Supabase connection string).")

    applied: set[str] = set()
    with psycopg.connect(database_url, autocommit=True) as conn:
        conn.execute(
            """
            create table if not exists _schema_migrations (
                file_name text primary key,
                applied_at timestamptz not null default now()
            )
            """
        )
        for (name,) in conn.execute("select file_name from _schema_migrations"):
            applied.add(name)

        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            if sql_file.name in applied:
                print(f"skip  {sql_file.name}")
                continue
            sql = sql_file.read_text()
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.execute(
                "insert into _schema_migrations (file_name) values (%s)", (sql_file.name,)
            )
            print(f"apply {sql_file.name}")

    print("migrations complete")


if __name__ == "__main__":
    main()