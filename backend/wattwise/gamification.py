"""Points, streaks and badges. Everything is derived from saved completion
records, so nothing here is stored twice or can drift out of sync."""
from datetime import date, timedelta

BADGES = [
    ("first_mission", "First mission", "Complete your first daily mission."),
    ("streak_3", "Three-day streak", "Complete missions on 3 days in a row."),
    ("streak_7", "Seven-day streak", "Complete missions on 7 days in a row."),
    ("points_100", "100 points", "Earn 100 points in total."),
    ("solar_scout", "Solar scout", "Complete the rooftop solar mission."),
    ("data_keeper", "Data keeper", "Save electricity readings for 3 different months."),
    ("lower_usage", "Usage went down", "Your latest saved reading is lower than the one before it."),
]


def streaks(completion_dates, today):
    """Return (current_streak, longest_streak) from a set of date objects.

    The current streak counts consecutive days ending today, or ending
    yesterday if nothing has been completed yet today (so it is not lost
    until a full day is missed).
    """
    days = set(completion_dates)
    if not days:
        return 0, 0
    anchor = today if today in days else today - timedelta(days=1)
    current = 0
    d = anchor
    while d in days:
        current += 1
        d -= timedelta(days=1)

    longest = run = 0
    prev = None
    for d in sorted(days):
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        longest = max(longest, run)
        prev = d
    return current, longest


def user_progress(db, user_id, today):
    rows = db.execute(
        """SELECT c.code, c.title, comp.points, comp.completed_on
           FROM completions comp JOIN challenges c ON c.id = comp.challenge_id
           WHERE comp.user_id = ? ORDER BY comp.completed_on DESC, comp.id DESC""",
        (user_id,),
    ).fetchall()
    total_points = sum(r["points"] for r in rows)
    dates = {date.fromisoformat(r["completed_on"]) for r in rows}
    current, longest = streaks(dates, today)

    reading_rows = db.execute(
        "SELECT kwh FROM readings WHERE user_id = ? ORDER BY period DESC LIMIT 2", (user_id,)
    ).fetchall()
    reading_count = db.execute(
        "SELECT COUNT(*) AS n FROM readings WHERE user_id = ?", (user_id,)
    ).fetchone()["n"]
    lower = len(reading_rows) == 2 and reading_rows[0]["kwh"] < reading_rows[1]["kwh"]
    codes = {r["code"] for r in rows}

    earned = {
        "first_mission": len(rows) >= 1,
        "streak_3": longest >= 3,
        "streak_7": longest >= 7,
        "points_100": total_points >= 100,
        "solar_scout": "solar_explore" in codes,
        "data_keeper": reading_count >= 3,
        "lower_usage": lower,
    }
    badges = [
        {"code": c, "title": t, "description": d, "earned": earned[c]} for c, t, d in BADGES
    ]
    return {
        "total_points": total_points,
        "completed_count": len(rows),
        "current_streak": current,
        "longest_streak": longest,
        "badges": badges,
        "recent_completions": [
            {"code": r["code"], "title": r["title"], "points": r["points"], "completed_on": r["completed_on"]}
            for r in rows[:10]
        ],
    }
