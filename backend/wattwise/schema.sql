PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
    household_size  INTEGER NOT NULL CHECK (household_size BETWEEN 1 AND 50),
    tariff_per_kwh  REAL    NOT NULL CHECK (tariff_per_kwh > 0 AND tariff_per_kwh <= 100),
    city            TEXT,
    has_ac          INTEGER NOT NULL DEFAULT 0 CHECK (has_ac IN (0, 1)),
    ac_hours_per_day REAL   NOT NULL DEFAULT 0 CHECK (ac_hours_per_day BETWEEN 0 AND 24),
    is_demo         INTEGER NOT NULL DEFAULT 0 CHECK (is_demo IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- One reading per user per calendar month (period = 'YYYY-MM'). Values are
-- entered by the user; WattWise never measures live consumption.
CREATE TABLE IF NOT EXISTS readings (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period                 TEXT    NOT NULL CHECK (period GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
    kwh                    REAL    NOT NULL CHECK (kwh > 0),
    tariff_per_kwh         REAL    NOT NULL CHECK (tariff_per_kwh > 0),
    cost                   REAL    NOT NULL CHECK (cost >= 0),
    emission_factor        REAL    NOT NULL CHECK (emission_factor > 0),
    emissions_kg           REAL    NOT NULL CHECK (emissions_kg >= 0),
    transport_km           REAL    CHECK (transport_km IS NULL OR transport_km >= 0),
    transport_emissions_kg REAL    CHECK (transport_emissions_kg IS NULL OR transport_emissions_kg >= 0),
    source                 TEXT    NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'meter')),
    created_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, period)
);

CREATE TABLE IF NOT EXISTS challenges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL,
    action      TEXT    NOT NULL,
    points      INTEGER NOT NULL CHECK (points > 0)
);

-- The UNIQUE constraint is what prevents duplicate points for the same
-- challenge on the same day, even under concurrent requests.
CREATE TABLE IF NOT EXISTS completions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES challenges(id),
    completed_on TEXT    NOT NULL,
    points       INTEGER NOT NULL CHECK (points > 0),
    UNIQUE (user_id, challenge_id, completed_on)
);

CREATE TABLE IF NOT EXISTS resources (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    summary  TEXT NOT NULL,
    url      TEXT
);

CREATE TABLE IF NOT EXISTS community_goals (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    title              TEXT    NOT NULL UNIQUE,
    description        TEXT    NOT NULL,
    target_completions INTEGER NOT NULL CHECK (target_completions > 0)
);

CREATE INDEX IF NOT EXISTS idx_readings_user ON readings(user_id, period);
CREATE INDEX IF NOT EXISTS idx_completions_user ON completions(user_id, completed_on);
