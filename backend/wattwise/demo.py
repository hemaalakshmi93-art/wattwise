"""Optional demo data. Run with: flask --app app seed-demo

Every record created here belongs to a user with is_demo = 1 and a name that
starts with 'Demo'. The numbers are sample values, NOT real households.
"""
from datetime import timedelta

from . import clock

# (name, household, tariff, has_ac, ac_hours, monthly kWh (oldest -> newest), mission days, challenge codes)
DEMO_HOUSEHOLDS = [
    ("Demo Household A", 4, 6.5, True, 8, [310, 295, 270], 5, ["lights_off", "ac_reduce", "standby_hunt"]),
    ("Demo Household B", 2, 7.0, False, 0, [120, 118, 125], 3, ["lights_off", "natural_light"]),
    ("Demo Household C", 5, 6.0, True, 5, [380, 400, 365], 2, ["weekly_compare", "solar_explore"]),
]


def seed_demo(db):
    if db.execute("SELECT 1 FROM users WHERE is_demo = 1 LIMIT 1").fetchone():
        return 0
    from flask import current_app

    cfg = current_app.config
    today = clock.today()
    challenges = {r["code"]: r for r in db.execute("SELECT * FROM challenges")}
    for name, hh, tariff, has_ac, ac_h, kwhs, days, codes in DEMO_HOUSEHOLDS:
        uid = db.execute(
            """INSERT INTO users (name, household_size, tariff_per_kwh, has_ac, ac_hours_per_day, is_demo)
               VALUES (?,?,?,?,?,1)""",
            (name, hh, tariff, int(has_ac), ac_h),
        ).lastrowid
        # Sample readings for the three most recent months
        y, m = today.year, today.month
        periods = []
        for _ in kwhs:
            periods.append(f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        for period, kwh in zip(reversed(periods), kwhs):
            db.execute(
                """INSERT INTO readings (user_id, period, kwh, tariff_per_kwh, cost, emission_factor,
                   emissions_kg, source) VALUES (?,?,?,?,?,?,?, 'manual')""",
                (uid, period, kwh, tariff, round(kwh * tariff, 2), cfg["EMISSION_FACTOR"],
                 round(kwh * cfg["EMISSION_FACTOR"], 2)),
            )
        for d in range(days):
            day = (today - timedelta(days=d + 1)).isoformat()
            for code in codes:
                ch = challenges[code]
                db.execute(
                    "INSERT OR IGNORE INTO completions (user_id, challenge_id, completed_on, points) VALUES (?,?,?,?)",
                    (uid, ch["id"], day, ch["points"]),
                )
    db.commit()
    return len(DEMO_HOUSEHOLDS)
