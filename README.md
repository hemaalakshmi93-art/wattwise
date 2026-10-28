# WattWise: Mission LiFE Citizen Engagement Prototype

HACKCULT'26, Track 1 (Green Energy & Sustainability), problem statement HC26-GEDA01.

WattWise helps a household understand its electricity use and carbon footprint, take small daily
actions, and see community progress. It is a working full-stack prototype: React talks to a Flask
REST API, and everything is stored in SQLite.

**Honesty note.** All consumption values are entered by the user. Cost, emissions and solar figures
are estimates from documented formulas and editable assumptions. Nothing is measured live, no AI is
connected, and no subsidy, scheme or vendor data is invented.

## What is in it

| Area | What works |
|---|---|
| My Footprint | Save monthly kWh (or two meter readings), tariff, optional km driven. Cost, emissions, previous-vs-current change, history chart with metric and range filters, delete a reading. |
| Daily Missions | 7 missions with title, explanation, action, points, completion button, status and date. One completion per mission per day, enforced by a database constraint. |
| Recommendations | Rule-based, from your saved readings and household answers. Every item shows why it appears. |
| Community | Your points, streak, badges (individual) shown separately from the community goal and leaderboard (all participants). |
| Solar Advisor | Size, generation, savings, payback and CO2 avoided from editable assumptions. Formulas shown. Links to official portals. |
| Resource Hub | Searchable, filterable guidance. Links only to a few official home pages; everything else has no link. |
| AI Energy Coach | Not connected. A status endpoint reports this honestly. See `docs/ASSUMPTIONS.md`. |

## Requirements

- Python 3.10+
- Node.js 18+ and npm

## Setup and run (two terminals)

**Terminal 1: backend**

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # optional; defaults work. On Windows: copy .env.example .env
python app.py               # API on http://127.0.0.1:5001
```

The database file is created automatically at `backend/instance/wattwise.db` on first start.

Optional demo households (clearly labelled "Demo", flagged `is_demo`) so the leaderboard is not empty:

```bash
flask --app app seed-demo
```

**Terminal 2: frontend**

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Open http://localhost:5173. On first visit you will see the onboarding form. In development, Vite
proxies `/api` to the Flask server on port 5001. If you change the backend port, run the frontend
with `VITE_PROXY_TARGET=http://127.0.0.1:<port> npm run dev`.

## Tests

```bash
cd backend
pytest -q
```

46 tests cover the formulas (cost, emissions, change, solar sizing, streaks) and the API
(validation, duplicate-points protection, persistence across an app restart, leaderboard,
community totals, solar recalculation, resource search).

## Production-style build of the frontend

```bash
cd frontend && npm run build     # outputs frontend/dist
```

Serve `dist/` from any static host and point it at the API with `VITE_API_URL` at build time
(and set `WATTWISE_CORS_ORIGIN` on the backend to that origin).

## Configuration (backend/.env)

| Variable | Default | Meaning |
|---|---|---|
| `WATTWISE_EMISSION_FACTOR` | 0.82 | kg CO2e per kWh. **Verify against the latest official CEA value before presenting.** |
| `WATTWISE_TRANSPORT_FACTOR` | 0.17 | kg CO2e per km, assumed average petrol car |
| `WATTWISE_PER_PERSON_THRESHOLD` | 100 | kWh per person per month used by one recommendation rule |
| `WATTWISE_DB` | `backend/instance/wattwise.db` | SQLite path |
| `WATTWISE_CORS_ORIGIN` | `http://localhost:5173` | allowed frontend origin |
| `ADAPTION_API_URL`, `ADAPTION_API_KEY` | empty | reserved for the optional AI coach; never sent to the frontend |

## Project layout

```
wattwise/
  backend/
    app.py                 entry point
    wattwise/
      __init__.py          app factory, config, error handlers
      schema.sql           tables, constraints, indexes
      db.py                connection + init + CLI commands
      seed_data.py         missions, resources, community goal
      calculations.py      pure formulas (footprint, solar)
      recommendations.py   rule engine with "why"
      gamification.py      points, streaks, badges (derived from records)
      services.py          database operations
      validators.py        server-side validation
      routes.py            REST endpoints
      demo.py              optional labelled demo data
    tests/                 pytest suite
  frontend/
    src/                   React app (pages/, components/, api.js)
  docs/                    API, architecture, assumptions
```

## More documentation

- `docs/API.md`: every endpoint with examples
- `docs/ARCHITECTURE.md`: architecture diagram and data model
- `docs/ASSUMPTIONS.md`: assumptions, limitations, future work, demo checklist

## Where the acceptance criteria are verified

| Criterion | Evidence |
|---|---|
| Enter and save consumption | `test_save_and_fetch_reading` |
| Survives restart | `test_readings_persist_across_app_restart` |
| Correct dashboard numbers | `test_calculations.py`, `test_footprint_change` |
| Completing a mission updates points once per day | `test_complete_challenge_awards_points_once_per_day` |
| Leaderboard from stored records | `test_leaderboard_computed_from_records` |
| Solar responds to inputs | `test_solar_endpoint_and_recalculation` |
| Clear errors on bad input | `test_invalid_readings_rejected`, `test_solar_validation` |
