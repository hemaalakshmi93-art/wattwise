"""Database-backed operations shared by the routes."""
import sqlite3
from datetime import date

from flask import current_app

from . import calculations as calc
from . import clock
from .validators import ApiError


def user_to_dict(row):
    d = dict(row)
    d["has_ac"] = bool(d["has_ac"])
    d["is_demo"] = bool(d["is_demo"])
    return d


def get_user(db, user_id):
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise ApiError("User not found.", 404)
    return user_to_dict(row)


def create_user(db, clean):
    cur = db.execute(
        """INSERT INTO users (name, household_size, tariff_per_kwh, city, has_ac, ac_hours_per_day)
           VALUES (?,?,?,?,?,?)""",
        (clean["name"], clean["household_size"], clean["tariff_per_kwh"], clean["city"],
         int(clean["has_ac"]), clean["ac_hours_per_day"]),
    )
    user_id = cur.lastrowid
    if clean["initial_reading"]:
        save_reading(db, user_id, clean["initial_reading"], commit=False)
    db.commit()
    return get_user(db, user_id)


def reading_to_dict(row):
    return dict(row)


def save_reading(db, user_id, clean, commit=True):
    """Insert or update the reading for (user, period). Returns (reading, created)."""
    cfg = current_app.config
    kwh = clean["kwh"]
    cost = calc.monthly_cost(kwh, clean["tariff"])
    emissions = calc.electricity_emissions_kg(kwh, cfg["EMISSION_FACTOR"])
    km = clean["transport_km"]
    t_emissions = calc.transport_emissions_kg(km, cfg["TRANSPORT_FACTOR"]) if km is not None else None

    existing = db.execute(
        "SELECT id FROM readings WHERE user_id = ? AND period = ?", (user_id, clean["period"])
    ).fetchone()
    values = (kwh, clean["tariff"], cost, cfg["EMISSION_FACTOR"], emissions, km, t_emissions, clean["source"])
    if existing:
        db.execute(
            """UPDATE readings SET kwh=?, tariff_per_kwh=?, cost=?, emission_factor=?,
               emissions_kg=?, transport_km=?, transport_emissions_kg=?, source=? WHERE id=?""",
            values + (existing["id"],),
        )
        rid, created = existing["id"], False
    else:
        cur = db.execute(
            """INSERT INTO readings (user_id, period, kwh, tariff_per_kwh, cost, emission_factor,
               emissions_kg, transport_km, transport_emissions_kg, source)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user_id, clean["period"]) + values,
        )
        rid, created = cur.lastrowid, True
    if commit:
        db.commit()
    row = db.execute("SELECT * FROM readings WHERE id = ?", (rid,)).fetchone()
    return reading_to_dict(row), created


def list_readings(db, user_id):
    rows = db.execute(
        "SELECT * FROM readings WHERE user_id = ? ORDER BY period ASC", (user_id,)
    ).fetchall()
    return [reading_to_dict(r) for r in rows]


def footprint_summary(db, user):
    cfg = current_app.config
    readings = list_readings(db, user["id"])
    summary = {
        "has_data": bool(readings),
        "emission_factor": cfg["EMISSION_FACTOR"],
        "emission_factor_unit": "kg CO2e per kWh",
        "transport_factor": cfg["TRANSPORT_FACTOR"],
        "formulas": calc.FOOTPRINT_FORMULAS,
        "disclaimer": (
            "These figures are estimates calculated from the values you entered and the "
            "emission factor shown. They are not live measurements."
        ),
        "latest": None,
        "previous": None,
        "change": None,
        "per_person_kwh": None,
        "series": readings,
    }
    if readings:
        latest = readings[-1]
        summary["latest"] = latest
        summary["per_person_kwh"] = round(latest["kwh"] / user["household_size"], 1)
        if len(readings) >= 2:
            prev = readings[-2]
            summary["previous"] = prev
            summary["change"] = calc.compare_readings(prev, latest)
    return summary


def list_challenges(db, user_id, today):
    today_iso = today.isoformat()
    rows = db.execute(
        """SELECT c.*,
             (SELECT 1 FROM completions x WHERE x.user_id = ? AND x.challenge_id = c.id
                AND x.completed_on = ?) AS done_today,
             (SELECT MAX(completed_on) FROM completions x WHERE x.user_id = ? AND x.challenge_id = c.id)
                AS last_completed_on
           FROM challenges c ORDER BY c.id""",
        (user_id, today_iso, user_id),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["completed_today"] = bool(d.pop("done_today"))
        out.append(d)
    return out


def complete_challenge(db, user_id, challenge_id, today):
    challenge = db.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    if challenge is None:
        raise ApiError("Challenge not found.", 404)
    try:
        db.execute(
            "INSERT INTO completions (user_id, challenge_id, completed_on, points) VALUES (?,?,?,?)",
            (user_id, challenge_id, today.isoformat(), challenge["points"]),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise ApiError("You have already completed this mission today. Come back tomorrow.", 409)
    return {"challenge_id": challenge_id, "points_awarded": challenge["points"],
            "completed_on": today.isoformat()}


def leaderboard(db):
    rows = db.execute(
        """SELECT u.id, u.name, u.is_demo,
                  COALESCE(SUM(c.points), 0) AS points,
                  COUNT(c.id) AS completions
           FROM users u LEFT JOIN completions c ON c.user_id = u.id
           GROUP BY u.id
           ORDER BY points DESC, completions DESC, u.name COLLATE NOCASE ASC"""
    ).fetchall()
    out = []
    rank = 0
    last_points = None
    for i, r in enumerate(rows, start=1):
        if r["points"] != last_points:
            rank = i
            last_points = r["points"]
        out.append({"rank": rank, "user_id": r["id"], "name": r["name"],
                    "is_demo": bool(r["is_demo"]), "points": r["points"],
                    "completions": r["completions"]})
    return out


def community_summary(db):
    goal = db.execute("SELECT * FROM community_goals ORDER BY id LIMIT 1").fetchone()
    totals = db.execute(
        """SELECT COUNT(*) AS completions, COALESCE(SUM(points),0) AS points,
                  COUNT(DISTINCT user_id) AS active_users FROM completions"""
    ).fetchone()
    demo = db.execute(
        """SELECT COUNT(*) AS n FROM completions c JOIN users u ON u.id = c.user_id
           WHERE u.is_demo = 1"""
    ).fetchone()["n"]
    participants = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    readings = db.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
    target = goal["target_completions"] if goal else 0
    done = totals["completions"]
    return {
        "goal": {
            "title": goal["title"] if goal else None,
            "description": goal["description"] if goal else None,
            "target_completions": target,
            "completions": done,
            "percent": round(min(done / target * 100, 100), 1) if target else 0,
        },
        "participants": participants,
        "active_participants": totals["active_users"],
        "total_points": totals["points"],
        "readings_logged": readings,
        "demo_completions": demo,
        "note": "Community figures are counted from saved records. Demo households, if loaded, "
                "are included and labelled in the leaderboard.",
    }
