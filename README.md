CogSearch (Flask)

Overview
- Flask app with MySQL backend. App uses an application factory and Blueprints.
- Practice routes live under `src/routes/practice.py`; core routes under `src/routes/core.py`.

Quick Start
- Python 3.10+
- Create venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Configure: copy `src/instance/config.py.example` to `src/instance/config.py` and adjust values; or set env vars `SECRET_KEY`, `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`.
- Init DB (example):
  - `mysql -u root -p -e "CREATE DATABASE cogsearch_textsearch3;"`
  - `mysql -u root -p cogsearch_textsearch3 < schema.sql`
  - `mysql -u root -p cogsearch_textsearch3 < seed_data.sql`  # load mock data
- Run dev server: `flask --app app run --debug`

Project Structure
- `src/`: app package (`__init__.py`, Blueprints, services, db helpers)
- `templates/`: Jinja templates (practice templates under `templates/practice/`)
- `static/`: assets
- `instance/`: local config (ignored). Keep `config.py` here.
- `schema.sql`, `cogsearch.sql`: schema and seed scripts.

Notes
- DB helpers live in `cogsearch/db.py` and read Flask config via `current_app.config`.
- Avoid committing local DBs and secrets; `.gitignore` is configured accordingly.
