"""Seed the bench Postgres with N books, talking directly to the DB.

Reusable for both APIs — they share the same schema. Run once after
`docker compose up`; both APIs will see the same rows.

    python benchmark/seed.py --count 10000

The script is idempotent: if N rows already exist it skips. Use --reset
to truncate first.
"""
from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import create_engine, text

DEFAULT_DSN = "postgresql+psycopg2://bench_user:bench_pass@localhost:55432/bench_db"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument("--reset", action="store_true")
    p.add_argument("--dsn", default=os.environ.get("BENCH_DSN", DEFAULT_DSN))
    args = p.parse_args()

    engine = create_engine(args.dsn, future=True)
    with engine.begin() as conn:
        if args.reset:
            conn.execute(text("TRUNCATE books RESTART IDENTITY"))
            print("truncated books")

        current = conn.execute(text("SELECT COUNT(*) FROM books")).scalar_one()
        if current >= args.count:
            print(f"already have {current} rows, skipping")
            return 0

        to_insert = args.count - current
        print(f"inserting {to_insert} rows (current={current})")

        # Bulk insert in chunks to avoid one giant parameterised statement.
        CHUNK = 1_000
        inserted = 0
        while inserted < to_insert:
            n = min(CHUNK, to_insert - inserted)
            rows = [
                {
                    "title": f"Bench Book {current + inserted + i + 1}",
                    "author": f"Author {(current + inserted + i) % 200}",
                    "year": 1950 + ((current + inserted + i) % 70),
                    "isbn": f"BENCH-{current + inserted + i + 1:08d}",
                }
                for i in range(n)
            ]
            conn.execute(
                text(
                    "INSERT INTO books (title, author, year, isbn, status) "
                    "VALUES (:title, :author, :year, :isbn, 'active')"
                ),
                rows,
            )
            inserted += n
            if inserted % 5_000 == 0 or inserted == to_insert:
                print(f"  {inserted}/{to_insert}")

    print(f"done; total rows now: {args.count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
