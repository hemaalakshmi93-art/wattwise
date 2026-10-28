"""REST API. All endpoints live under /api and exchange JSON."""
from flask import Blueprint, current_app, jsonify, request

from . import calculations as calc
from . import clock, gamification, services
from .db import get_db
from .recommendations import build_recommendations
from .validators import ApiError, number, raise_if, require_json, validate_reading, validate_user

bp = Blueprint("api", __name__, url_prefix="/api")


def _body():
    return request.get_json(silent=True)


@bp.get("/health")
def health():
    get_db().execute("SELECT 1")
    return jsonify({"status": "ok"})


@bp.get("/config")
def config():
    cfg = current_app.config
    return jsonify({
        "emission_factor": cfg["EMISSION_FACTOR"],
        "emission_factor_unit": "kg CO2e per kWh",
        "transport_factor": cfg["TRANSPORT_FACTOR"],
        "per_person_threshold": cfg["PER_PERSON_THRESHOLD"],
        "solar_defaults": calc.SOLAR_DEFAULTS,
        "solar_limits": calc.SOLAR_LIMITS,
    })


# ------------------------------------------------------------------ users
@bp.get("/users")
def list_users():
    rows = get_db().execute("SELECT * FROM users ORDER BY id").fetchall()
    return jsonify({"users": [services.user_to_dict(r) for r in rows]})


@bp.post("/users")
def create_user():
    clean = validate_user(_body())
    user = services.create_user(get_db(), clean)
    return jsonify({"user": user}), 201


@bp.get("/users/<int:user_id>")
def get_user(user_id):
    return jsonify({"user": services.get_user(get_db(), user_id)})


# --------------------------------------------------------------- readings
@bp.get("/users/<int:user_id>/readings")
def get_readings(user_id):
    db = get_db()
    services.get_user(db, user_id)
    return jsonify({"readings": services.list_readings(db, user_id)})


@bp.post("/users/<int:user_id>/readings")
def post_reading(user_id):
    db = get_db()
    user = services.get_user(db, user_id)
    clean = validate_reading(_body(), user["tariff_per_kwh"])
    reading, created = services.save_reading(db, user_id, clean)
    return jsonify({"reading": reading, "created": created}), (201 if created else 200)


@bp.delete("/users/<int:user_id>/readings/<int:reading_id>")
def delete_reading(user_id, reading_id):
    db = get_db()
    services.get_user(db, user_id)
    cur = db.execute("DELETE FROM readings WHERE id = ? AND user_id = ?", (reading_id, user_id))
    db.commit()
    if cur.rowcount == 0:
        raise ApiError("Reading not found.", 404)
    return jsonify({"deleted": reading_id})


@bp.get("/users/<int:user_id>/footprint")
def footprint(user_id):
    db = get_db()
    user = services.get_user(db, user_id)
    return jsonify(services.footprint_summary(db, user))


# ------------------------------------------------- missions & recommendations
@bp.get("/users/<int:user_id>/challenges")
def challenges(user_id):
    db = get_db()
    services.get_user(db, user_id)
    return jsonify({"date": clock.today().isoformat(),
                    "challenges": services.list_challenges(db, user_id, clock.today())})


@bp.post("/users/<int:user_id>/challenges/<int:challenge_id>/complete")
def complete(user_id, challenge_id):
    db = get_db()
    services.get_user(db, user_id)
    result = services.complete_challenge(db, user_id, challenge_id, clock.today())
    progress = gamification.user_progress(db, user_id, clock.today())
    return jsonify({"result": result, "progress": progress}), 201


@bp.get("/users/<int:user_id>/progress")
def progress(user_id):
    db = get_db()
    services.get_user(db, user_id)
    return jsonify(gamification.user_progress(db, user_id, clock.today()))


@bp.get("/users/<int:user_id>/recommendations")
def recommendations(user_id):
    db = get_db()
    user = services.get_user(db, user_id)
    readings = services.list_readings(db, user_id)
    comps = [dict(r) for r in db.execute(
        """SELECT c.code, comp.completed_on FROM completions comp
           JOIN challenges c ON c.id = comp.challenge_id WHERE comp.user_id = ?""", (user_id,))]
    recs = build_recommendations(user, readings, comps, clock.today(),
                                 current_app.config["PER_PERSON_THRESHOLD"])
    return jsonify({
        "source": "rule-based",
        "note": "These suggestions come from simple rules applied to your saved data. They are not AI-generated.",
        "recommendations": recs,
    })


# -------------------------------------------------------------- community
@bp.get("/leaderboard")
def leaderboard():
    return jsonify({"leaderboard": services.leaderboard(get_db())})


@bp.get("/community")
def community():
    return jsonify(services.community_summary(get_db()))


# ------------------------------------------------------------------ solar
@bp.post("/solar/estimate")
def solar_estimate():
    data = require_json(_body())
    errors = {}
    kwh = number(data, "monthly_kwh", errors, exclusive_min=0, maximum=50_000)
    area = number(data, "roof_area_m2", errors, exclusive_min=0, maximum=100_000)
    bill = number(data, "monthly_bill", errors, exclusive_min=0, maximum=10_000_000)
    location = data.get("location")
    if location is not None and (not isinstance(location, str) or len(location) > 80):
        errors["location"] = "Must be text of at most 80 characters."

    assumptions = {}
    for key, default in calc.SOLAR_DEFAULTS.items():
        if key == "days_per_month":
            continue
        lo, hi = calc.SOLAR_LIMITS[key]
        raw = data.get(key)
        if raw in (None, ""):
            assumptions[key] = default
        else:
            val = number(data, key, errors, minimum=lo, maximum=hi)
            assumptions[key] = val if val is not None else default
    raise_if(errors)

    result = calc.solar_estimate(
        kwh, area, bill, current_app.config["EMISSION_FACTOR"],
        assumptions["peak_sun_hours"], assumptions["performance_ratio"],
        assumptions["area_per_kw"], assumptions["cost_per_kw"],
    )
    result["assumptions"] = assumptions
    result["emission_factor"] = current_app.config["EMISSION_FACTOR"]
    result["location"] = location.strip() if isinstance(location, str) and location.strip() else None
    result["location_note"] = (
        "The location is only echoed back. Sunlight hours are an assumption you can edit; no live "
        "weather or irradiance data is used."
    )
    result["label"] = "Preliminary estimate. Not an official quotation or guaranteed saving."
    return jsonify(result)


# -------------------------------------------------------------- resources
@bp.get("/resources")
def resources():
    q = (request.args.get("q") or "").strip().lower()
    category = (request.args.get("category") or "").strip()
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM resources ORDER BY category, title")]
    categories = sorted({r["category"] for r in rows})
    if category:
        rows = [r for r in rows if r["category"] == category]
    if q:
        rows = [r for r in rows if q in r["title"].lower() or q in r["summary"].lower()
                or q in r["category"].lower()]
    return jsonify({"resources": rows, "categories": categories})


# --------------------------------------------------------------- AI coach
@bp.get("/coach/status")
def coach_status():
    """The AI Energy Coach is optional. No integration is implemented until the
    Adaption Labs API, credentials and method are confirmed, so this never
    returns generated advice."""
    cfg = current_app.config
    has_creds = bool(cfg["ADAPTION_API_URL"] and cfg["ADAPTION_API_KEY"])
    return jsonify({
        "available": False,
        "credentials_present": has_creds,
        "message": (
            "AI Energy Coach is not connected. The rule-based recommendations on this page are "
            "fully working without it."
        ),
    })
