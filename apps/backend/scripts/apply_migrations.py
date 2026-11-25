"""Idempotent SQL migrator for ACG's Supabase schema.

Usage:
    export DATABASE_URL="postgresql://postgres.<ref>:<password>@<pooler-host>:6543/postgres"
    python scripts/apply_migrations.py

Applies every .sql file in backend/sql/ in lexicographic order. The whole run
is one transaction behind an advisory lock, so a failure never leaves a
half-applied migration behind for the next run to trip over.
"""

import os
from pathlib import Path

import psycopg

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
MIGRATION_LOCK = 0x4143475F4D4947  # "ACG_MIG"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required (pooled Supabase connection string).")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Serialize concurrent migrators; the lock is released on commit.
            cur.execute("select pg_advisory_xact_lock(%s)", (MIGRATION_LOCK,))
            cur.execute(
                """
                create table if not exists _schema_migrations (
                    file_name text primary key,
                    applied_at timestamptz not null default now()
                )
                """
            )
            cur.execute("select file_name from _schema_migrations")
            applied = {row[0] for row in cur.fetchall()}

            for sql_file in sorted(SQL_DIR.glob("*.sql")):
                if sql_file.name in applied:
                    print(f"skip  {sql_file.name}")
                    continue
                cur.execute(sql_file.read_text())
                cur.execute(
                    "insert into _schema_migrations (file_name) values (%s)", (sql_file.name,)
                )
                print(f"apply {sql_file.name}")
        conn.commit()
    print("migrations complete")


if __name__ == "__main__":
    main()
