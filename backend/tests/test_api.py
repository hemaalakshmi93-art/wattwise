from datetime import date

import pytest


def _reading(client, uid, period, kwh, **extra):
    return client.post(f"/api/users/{uid}/readings", json={"period": period, "kwh": kwh, **extra})


# ------------------------------------------------------------- users
def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_create_user_validation(client):
    r = client.post("/api/users", json={"name": "", "household_size": 0, "tariff_per_kwh": -1})
    assert r.status_code == 400
    fields = r.get_json()["error"]["fields"]
    assert {"name", "household_size", "tariff_per_kwh"} <= set(fields)


def test_create_user_with_initial_reading(client):
    r = client.post("/api/users", json={
        "name": "Asha", "household_size": 3, "tariff_per_kwh": 7,
        "initial_reading": {"period": "2026-09", "kwh": 150},
    })
    assert r.status_code == 201
    uid = r.get_json()["user"]["id"]
    readings = client.get(f"/api/users/{uid}/readings").get_json()["readings"]
    assert len(readings) == 1 and readings[0]["cost"] == 1050.0 and readings[0]["emissions_kg"] == 120.0


def test_unknown_user_404(client):
    assert client.get("/api/users/999").status_code == 404
    assert client.get("/api/users/999/footprint").status_code == 404


# ---------------------------------------------------------- readings
def test_save_and_fetch_reading(client, user):
    r = _reading(client, user["id"], "2026-09", 200)
    assert r.status_code == 201
    body = r.get_json()["reading"]
    assert body["cost"] == 1200.0          # 200 * tariff 6
    assert body["emissions_kg"] == 160.0   # 200 * factor 0.8
    assert body["emission_factor"] == 0.8


def test_same_period_updates_not_duplicates(client, user):
    _reading(client, user["id"], "2026-09", 200)
    r = _reading(client, user["id"], "2026-09", 250)
    assert r.status_code == 200
    readings = client.get(f"/api/users/{user['id']}/readings").get_json()["readings"]
    assert len(readings) == 1 and readings[0]["kwh"] == 250


def test_meter_readings(client, user):
    r = client.post(f"/api/users/{user['id']}/readings",
                    json={"period": "2026-09", "meter_start": 1000, "meter_end": 1180.5})
    assert r.status_code == 201
    assert r.get_json()["reading"]["kwh"] == 180.5
    assert r.get_json()["reading"]["source"] == "meter"


def test_meter_end_must_exceed_start(client, user):
    r = client.post(f"/api/users/{user['id']}/readings",
                    json={"period": "2026-09", "meter_start": 500, "meter_end": 400})
    assert r.status_code == 400 and "meter_end" in r.get_json()["error"]["fields"]


@pytest.mark.parametrize("payload,field", [
    ({"period": "2026-13", "kwh": 100}, "period"),
    ({"period": "Sept", "kwh": 100}, "period"),
    ({"period": "2027-01", "kwh": 100}, "period"),   # future
    ({"period": "2026-09", "kwh": -5}, "kwh"),
    ({"period": "2026-09", "kwh": 0}, "kwh"),
    ({"period": "2026-09", "kwh": "abc"}, "kwh"),
    ({"period": "2026-09"}, "kwh"),
    ({"period": "2026-09", "kwh": 100, "tariff_per_kwh": 0}, "tariff_per_kwh"),
    ({"period": "2026-09", "kwh": 100, "transport_km": -1}, "transport_km"),
])
def test_invalid_readings_rejected(client, user, payload, field):
    r = client.post(f"/api/users/{user['id']}/readings", json=payload)
    assert r.status_code == 400
    assert field in r.get_json()["error"]["fields"]


def test_non_json_body_rejected(client, user):
    r = client.post(f"/api/users/{user['id']}/readings", data="nope", content_type="text/plain")
    assert r.status_code == 400


def test_transport_optional(client, user):
    r = _reading(client, user["id"], "2026-09", 100, transport_km=100)
    assert r.get_json()["reading"]["transport_emissions_kg"] == 20.0


def test_delete_reading(client, user):
    rid = _reading(client, user["id"], "2026-09", 100).get_json()["reading"]["id"]
    assert client.delete(f"/api/users/{user['id']}/readings/{rid}").status_code == 200
    assert client.delete(f"/api/users/{user['id']}/readings/{rid}").status_code == 404


def test_footprint_empty_state(client, user):
    f = client.get(f"/api/users/{user['id']}/footprint").get_json()
    assert f["has_data"] is False and f["latest"] is None and f["series"] == []
    assert f["emission_factor"] == 0.8


def test_footprint_change(client, user):
    _reading(client, user["id"], "2026-08", 100)
    _reading(client, user["id"], "2026-09", 120)
    f = client.get(f"/api/users/{user['id']}/footprint").get_json()
    assert f["latest"]["period"] == "2026-09" and f["previous"]["period"] == "2026-08"
    assert f["change"]["kwh_pct"] == 20.0 and f["change"]["cost_abs"] == 120.0
    assert f["per_person_kwh"] == 30.0  # 120 / household of 4


def test_readings_persist_across_app_restart(tmp_path, today):
    from wattwise import create_app

    cfg = {"TESTING": True, "DATABASE": str(tmp_path / "persist.db")}
    app1 = create_app(cfg)
    c1 = app1.test_client()
    uid = c1.post("/api/users", json={"name": "P", "household_size": 2, "tariff_per_kwh": 5}).get_json()["user"]["id"]
    c1.post(f"/api/users/{uid}/readings", json={"period": "2026-09", "kwh": 90})

    app2 = create_app(cfg)  # simulates restarting the server
    readings = app2.test_client().get(f"/api/users/{uid}/readings").get_json()["readings"]
    assert len(readings) == 1 and readings[0]["kwh"] == 90


# ---------------------------------------------------------- missions
def _challenge_id(client, uid, code_title_part):
    for c in client.get(f"/api/users/{uid}/challenges").get_json()["challenges"]:
        if code_title_part in c["title"].lower():
            return c
    raise AssertionError("challenge not found")


def test_challenges_have_required_fields(client, user):
    chs = client.get(f"/api/users/{user['id']}/challenges").get_json()["challenges"]
    assert len(chs) >= 5
    for c in chs:
        assert c["title"] and c["description"] and c["action"] and c["points"] > 0
        assert c["completed_today"] is False and c["last_completed_on"] is None


def test_complete_challenge_awards_points_once_per_day(client, user, today):
    uid = user["id"]
    ch = _challenge_id(client, uid, "unused lights")
    r = client.post(f"/api/users/{uid}/challenges/{ch['id']}/complete")
    assert r.status_code == 201
    assert r.get_json()["progress"]["total_points"] == ch["points"]

    dup = client.post(f"/api/users/{uid}/challenges/{ch['id']}/complete")
    assert dup.status_code == 409
    assert client.get(f"/api/users/{uid}/progress").get_json()["total_points"] == ch["points"]

    # status reflects completion
    again = _challenge_id(client, uid, "unused lights")
    assert again["completed_today"] is True and again["last_completed_on"] == "2026-10-28"

    # next day it can be completed again
    today.set(date(2026, 10, 29))
    assert client.post(f"/api/users/{uid}/challenges/{ch['id']}/complete").status_code == 201
    p = client.get(f"/api/users/{uid}/progress").get_json()
    assert p["total_points"] == ch["points"] * 2 and p["current_streak"] == 2


def test_unknown_challenge_404(client, user):
    assert client.post(f"/api/users/{user['id']}/challenges/9999/complete").status_code == 404


def test_badges(client, user, today):
    uid = user["id"]
    solar = _challenge_id(client, uid, "solar")
    client.post(f"/api/users/{uid}/challenges/{solar['id']}/complete")
    badges = {b["code"]: b["earned"] for b in client.get(f"/api/users/{uid}/progress").get_json()["badges"]}
    assert badges["first_mission"] and badges["solar_scout"] and not badges["streak_3"]


# --------------------------------------------------- recommendations
def test_recommendations_new_user(client, user):
    body = client.get(f"/api/users/{user['id']}/recommendations").get_json()
    ids = [r["id"] for r in body["recommendations"]]
    assert body["source"] == "rule-based"
    assert "add_first_reading" in ids and "ac_hours" in ids
    assert all(r["why"] for r in body["recommendations"])


def test_recommendation_on_usage_rise(client, user):
    _reading(client, user["id"], "2026-08", 100)
    _reading(client, user["id"], "2026-09", 130)
    recs = client.get(f"/api/users/{user['id']}/recommendations").get_json()["recommendations"]
    rise = next(r for r in recs if r["id"] == "usage_rise")
    assert "30%" in rise["why"]


# ------------------------------------------------------ community
def test_leaderboard_computed_from_records(client, today):
    a = client.post("/api/users", json={"name": "Alpha", "household_size": 1, "tariff_per_kwh": 5}).get_json()["user"]["id"]
    b = client.post("/api/users", json={"name": "Beta", "household_size": 1, "tariff_per_kwh": 5}).get_json()["user"]["id"]
    chs = client.get(f"/api/users/{a}/challenges").get_json()["challenges"]
    client.post(f"/api/users/{b}/challenges/{chs[0]['id']}/complete")
    client.post(f"/api/users/{b}/challenges/{chs[1]['id']}/complete")
    client.post(f"/api/users/{a}/challenges/{chs[0]['id']}/complete")
    board = client.get("/api/leaderboard").get_json()["leaderboard"]
    assert [e["name"] for e in board] == ["Beta", "Alpha"]
    assert board[0]["points"] == chs[0]["points"] + chs[1]["points"] and board[0]["rank"] == 1


def test_community_progress_from_saved_completions(client, user):
    empty = client.get("/api/community").get_json()
    assert empty["goal"]["completions"] == 0 and empty["goal"]["percent"] == 0
    ch = client.get(f"/api/users/{user['id']}/challenges").get_json()["challenges"][0]
    client.post(f"/api/users/{user['id']}/challenges/{ch['id']}/complete")
    c = client.get("/api/community").get_json()
    assert c["goal"]["completions"] == 1 and c["participants"] == 1
    assert c["goal"]["percent"] == round(1 / c["goal"]["target_completions"] * 100, 1)


def test_demo_seed_is_labelled_and_idempotent(app, client):
    from wattwise.db import get_db
    from wattwise.demo import seed_demo

    with app.app_context():
        assert seed_demo(get_db()) == 3
        assert seed_demo(get_db()) == 0
    board = client.get("/api/leaderboard").get_json()["leaderboard"]
    assert len(board) == 3 and all(e["is_demo"] and e["name"].startswith("Demo") for e in board)


# ----------------------------------------------------------- solar
SOLAR_OK = {"monthly_kwh": 300, "roof_area_m2": 100, "monthly_bill": 1800}


def test_solar_endpoint_and_recalculation(client):
    a = client.post("/api/solar/estimate", json=SOLAR_OK).get_json()
    assert a["recommended_size_kw"] > 0 and "Preliminary" in a["label"] and a["formulas"]
    b = client.post("/api/solar/estimate", json={**SOLAR_OK, "peak_sun_hours": 4}).get_json()
    assert b["recommended_size_kw"] > a["recommended_size_kw"]
    assert b["assumptions"]["peak_sun_hours"] == 4


def test_solar_validation(client):
    r = client.post("/api/solar/estimate", json={"monthly_kwh": -1, "roof_area_m2": "x",
                                                  "performance_ratio": 2})
    assert r.status_code == 400
    assert {"monthly_kwh", "roof_area_m2", "monthly_bill", "performance_ratio"} <= set(
        r.get_json()["error"]["fields"])


# --------------------------------------------------------- resources
def test_resources_search_and_filter(client):
    allr = client.get("/api/resources").get_json()
    assert len(allr["resources"]) > 5 and "Rooftop solar" in allr["categories"]
    solar = client.get("/api/resources?category=Rooftop solar").get_json()["resources"]
    assert solar and all(r["category"] == "Rooftop solar" for r in solar)
    hit = client.get("/api/resources?q=standby").get_json()["resources"]
    assert hit and all("standby" in (r["title"] + r["summary"]).lower() for r in hit)
    assert client.get("/api/resources?q=zzzzzz").get_json()["resources"] == []


def test_resource_urls_are_https_or_null(client):
    for r in client.get("/api/resources").get_json()["resources"]:
        assert r["url"] is None or r["url"].startswith("https://")


# ----------------------------------------------------------- coach
def test_coach_never_fabricates(client):
    s = client.get("/api/coach/status").get_json()
    assert s["available"] is False


def test_api_errors_are_json(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and "error" in r.get_json()
