#!/usr/bin/env python3
"""Standardize `passID`/`passage_id` columns to 6-digit zero-padded strings.

The script connects directly to MySQL and updates every table in the target
schema that exposes a `passID` or `passage_id` column. Existing values that
already match the six-digit pattern are left untouched. For convenience you can
also request the script to tighten the column definitions to `CHAR(6)` once the
updates succeed.

Usage example:

    export MYSQL_HOST=localhost
    export MYSQL_USER=root
    export MYSQL_PASSWORD=secret
    export MYSQL_DB=cogsearch_textsearch3
    python scripts/standardize_passage_ids.py --alter-columns
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable, List, Sequence, Tuple

import mysql.connector

COLUMN_NAMES: Tuple[str, ...] = ("passID", "passage_id")
DEFAULT_SCHEMA = os.getenv("MYSQL_DB", "cogsearch_textsearch3")


def get_connection(schema: str):
    """Open a MySQL connection using env vars (mirrors Flask config defaults)."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=schema,
        auth_plugin="mysql_native_password",
    )


def fetch_target_columns(cursor, schema: str, column_names: Sequence[str]) -> List[Tuple[str, str]]:
    placeholders = ", ".join(["%s"] * len(column_names))
    query = f"""
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND COLUMN_NAME IN ({placeholders})
        ORDER BY TABLE_NAME, COLUMN_NAME
    """
    cursor.execute(query, (schema, *column_names))
    return [(row[0], row[1]) for row in cursor.fetchall()]


def standardize_column(cursor, schema: str, table: str, column: str) -> int:
    update_sql = f"""
        UPDATE `{schema}`.`{table}`
        SET `{column}` = LPAD(`{column}`, 6, '0')
        WHERE `{column}` REGEXP '^[0-9]{1,6}$' AND LENGTH(`{column}`) <> 6
    """
    cursor.execute(update_sql)
    return cursor.rowcount


def tighten_column(cursor, schema: str, table: str, column: str) -> None:
    alter_sql = f"""
        ALTER TABLE `{schema}`.`{table}`
        MODIFY `{column}` CHAR(6) NOT NULL
    """
    cursor.execute(alter_sql)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="Database/schema name (default: %(default)s)")
    parser.add_argument(
        "--columns",
        nargs="*",
        default=COLUMN_NAMES,
        help="Column names to standardize (default: passID passage_id)",
    )
    parser.add_argument(
        "--alter-columns",
        action="store_true",
        help="After updating values, tighten column definitions to CHAR(6)",
    )
    args = parser.parse_args(argv)

    conn = None
    try:
        conn = get_connection(args.schema)
        cursor = conn.cursor()

        targets = fetch_target_columns(cursor, args.schema, args.columns)
        if not targets:
            print(f"No columns named {', '.join(args.columns)} found in schema '{args.schema}'.")
            return 0

        print(f"Found {len(targets)} column(s) to standardize in schema '{args.schema}'.")
        total = 0
        for table, column in targets:
            changed = standardize_column(cursor, args.schema, table, column)
            total += changed
            print(f"  - {table}.{column}: updated {changed} row(s)")

        conn.commit()
        print(f"Finished value updates. Total rows touched: {total}.")

        if args.alter_columns:
            print("Tightening column definitions to CHAR(6)...")
            for table, column in targets:
                tighten_column(cursor, args.schema, table, column)
                print(f"  - {table}.{column}: altered to CHAR(6)")
            conn.commit()

        return 0
    except mysql.connector.Error as exc:  # pragma: no cover - manual script
        print(f"MySQL error: {exc}", file=sys.stderr)
        if conn:
            conn.rollback()
        return 1
    finally:
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":  # pragma: no cover - manual script
    sys.exit(main())
