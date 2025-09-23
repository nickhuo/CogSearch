CogSearch (Flask)

Overview
- Flask app with MySQL backend. App uses an application factory and Blueprints.
- Practice routes live under `src/routes/practice.py`; core routes under `src/routes/core.py`.

Quick Start

### 1. Environment Setup
- Python 3.10+
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`

### 2. Database Configuration
**Method 1: Using config file (Recommended)**
```bash
# Copy the example config file
cp src/instance/config.py.example src/instance/config.py

# Edit config.py with your database settings
nano src/instance/config.py
```

**Method 2: Using environment variables**
```bash
export SECRET_KEY="your-secret-key"
export MYSQL_HOST="localhost"
export MYSQL_USER="root"
export MYSQL_PASSWORD="your-password"
export MYSQL_DB="cogsearch_textsearch3"
```

### 3. Database Initialization
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE cogsearch_textsearch3;"

# Import schema
mysql -u root -p cogsearch_textsearch3 < schema.sql

# Load sample data (optional)
mysql -u root -p cogsearch_textsearch3 < seed_data.sql
```

### 4. Run Development Server
```bash
flask --app app run --debug
```

Project Structure
- `src/`: app package (`__init__.py`, Blueprints, services, db helpers)
- `templates/`: Jinja templates (practice templates under `templates/practice/`)
- `static/`: assets
- `instance/`: local config (ignored). Keep `config.py` here.
- `schema.sql`, `cogsearch.sql`: schema and seed scripts.

Notes
- DB helpers live in `cogsearch/db.py` and read Flask config via `current_app.config`.
- Avoid committing local DBs and secrets; `.gitignore` is configured accordingly.

Maintenance
- Standardize `passID` columns to six-digit format:
  ```bash
  # ensure MYSQL_* env vars are set
  python scripts/standardize_passage_ids.py --alter-columns
  ```
  The script queries `INFORMATION_SCHEMA` for any `passID`/`passage_id` fields,
  left-pads existing values with zeros, and (optionally) converts column types
  to `CHAR(6)` so future inserts are enforced.
