# CogSearch Data Import Guide

This note explains how to rebuild the `cogsearch_textsearch3` schema from the
materialized CSV exports in `src/db/material/`. Follow these steps whenever you
need a clean database that mirrors the bundled data dump.

## Prerequisites
- Local MySQL server (Homebrew 9.x or similar) with CLI tools on `PATH`.
- Credentials that can create/drop databases (examples below assume `root`
  with no password; adjust `-u/-p` flags as needed).
- Repository checked out at `/Users/.../CogSearch` (update paths if different).

## 1. Start MySQL (if needed)

```bash
mysql.server start
```

If another MySQL instance is already bound to port `3306`, stop it or update the
commands below to use the appropriate host/port/socket.

## 2. Reset the target database (destructive!)

```bash
mysql -h 127.0.0.1 -P 3306 -u root \
  -e "DROP DATABASE IF EXISTS cogsearch_textsearch3; CREATE DATABASE cogsearch_textsearch3;"
```

This permanently removes any existing data in `cogsearch_textsearch3` before
reloading the dump.

## 3. Apply the schema definition

```bash
mysql -h 127.0.0.1 -P 3306 -u root cogsearch_textsearch3 \
  < src/db/schema.sql
```

## 4. Enable local file imports

```bash
mysql -h 127.0.0.1 -P 3306 -u root \
  -e "SET GLOBAL local_infile = 1;"
```

The load script streams CSVs from disk, so `local_infile` must be allowed.

## 5. Load all materialized tables

```bash
mysql --local-infile=1 -h 127.0.0.1 -P 3306 -u root cogsearch_textsearch3 \
  < src/db/material/load_material.sql
```

The script directly bulk-imports each CSV snapshot now that the schema already
exposes the final column set (including `c4Ans` and the trimmed subtopic
tables).

## 6. Optional: Verify row counts

```bash
python3 - <<'PY'
from pathlib import Path
base = Path('src/db/material')
selects = []
for csv_path in sorted(base.glob('cogsearch_textsearch3_table_*.csv')):
    table = csv_path.name.removeprefix('cogsearch_textsearch3_table_').removesuffix('.csv')
    selects.append(f"SELECT '{table}' AS table_name, COUNT(*) AS row_count FROM `{table}`")
sql = "\nUNION ALL\n".join(selects) + ';'
Path('/tmp/table_counts.sql').write_text(sql)
PY

mysql -h 127.0.0.1 -P 3306 -u root -D cogsearch_textsearch3 < /tmp/table_counts.sql
```

You should see counts similar to the snapshot shared in the task log. Spot
check any critical tables with direct `SELECT` queries as needed.

## Troubleshooting
- **Stale PID / socket files**: remove `/opt/homebrew/var/mysql/*.pid` or
  `/tmp/mysql*.sock` if the server refuses to start because files already exist.
- **`local_infile` disabled**: rerun step 4 (some servers reset the flag on
  restart).
- **CSV path errors**: confirm the repository path and rerun the load command.

With these steps, teammates can reproduce the database state shipped with the
repository using only the checked-in schema and CSV artifacts.
