# Architecture

## Diagram

```mermaid
flowchart LR
  subgraph Browser["Browser (React + Vite)"]
    UI["Pages: Dashboard, My Footprint, Daily Missions,\nCommunity, Solar Advisor, Resource Hub"]
    API["api.js (fetch, JSON)"]
    UI --> API
  end
  subgraph Server["Flask backend"]
    R["routes.py\nREST endpoints"]
    V["validators.py\nserver-side validation"]
    S["services.py\nDB operations"]
    C["calculations.py\npure formulas"]
    G["gamification.py\npoints, streaks, badges"]
    RE["recommendations.py\nrule engine"]
    R --> V
    R --> S
    R --> C
    R --> G
    R --> RE
    S --> C
  end
  DB[("SQLite\nusers, readings, challenges,\ncompletions, resources, community_goals")]
  API -- "HTTP /api (JSON)" --> R
  S --> DB
  G --> DB
  AI["Adaption Labs (optional, not connected)"] -.-> R
```

Plain-text version:

```
React (Vite) --HTTP/JSON--> Flask routes --> validators
                                  |--> services --> SQLite
                                  |--> calculations (pure)
                                  |--> gamification (derived from completions)
                                  |--> recommendations (rules)
                 (optional, not connected) Adaption Labs coach
```

## Data model

```
users 1 --- * readings        UNIQUE(user_id, period)
users 1 --- * completions     UNIQUE(user_id, challenge_id, completed_on)
challenges 1 --- * completions
resources, community_goals    reference tables
```

Key constraints (see `backend/wattwise/schema.sql`): positive kWh and tariff, `YYYY-MM` period
format, household 1-50, AC hours 0-24, foreign keys on. The unique constraint on completions is
what prevents duplicate points for the same mission on the same day.

## Design decisions

- **Derived, not duplicated.** Points, streaks, badges, leaderboard and community progress are all
  computed from saved completion and reading rows, so they cannot drift or be faked.
- **Pure calculations.** `calculations.py` has no Flask or database code, so formulas are easy to
  unit test and explain.
- **Emission factor stored per reading.** Changing the configured factor later does not silently
  rewrite history.
- **Dashboard refresh.** Pages share a `version` counter; saving a reading or completing a mission
  bumps it, which re-fetches every visible panel.
- **Secrets stay on the server.** The optional AI credentials are read from environment variables
  and never sent to the frontend.
