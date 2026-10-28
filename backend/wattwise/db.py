import sqlite3
from pathlib import Path

import click
from flask import current_app, g

from .seed_data import CHALLENGES, COMMUNITY_GOAL, RESOURCES

SCHEMA = Path(__file__).with_name("schema.sql")


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Create tables and load reference data. Safe to run repeatedly."""
    db = get_db()
    db.executescript(SCHEMA.read_text())
    db.executemany(
        "INSERT OR IGNORE INTO challenges (code, title, description, action, points) VALUES (?,?,?,?,?)",
        CHALLENGES,
    )
    db.executemany(
        "INSERT OR IGNORE INTO resources (title, category, summary, url) VALUES (?,?,?,?)",
        RESOURCES,
    )
    db.execute(
        "INSERT OR IGNORE INTO community_goals (title, description, target_completions) VALUES (?,?,?)",
        COMMUNITY_GOAL,
    )
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and reference data (idempotent)."""
        init_db()
        click.echo("Database ready.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Add clearly labelled demo households so the leaderboard is not empty."""
        from .demo import seed_demo

        n = seed_demo(get_db())
        click.echo(f"Added {n} demo households." if n else "Demo households already present.")
