# WattWise API

Base URL (development): `http://127.0.0.1:5001/api`. All bodies and responses are JSON.

**Errors** always use this shape, with a matching HTTP status (400 invalid input, 404 not found,
409 conflict, 500 unexpected):

```json
{ "error": { "message": "Some values are invalid. Please fix them and try again.",
             "fields": { "kwh": "Must be greater than 0." } } }
```

There is no login. A "profile" is a user record selected in the UI (see limitations).

## General

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` |
| GET | `/config` | Emission factor, transport factor, threshold, solar defaults and limits |

## Users

| Method | Path | Description |
|---|---|---|
| GET | `/users` | List profiles |
| POST | `/users` | Create a profile (optionally with one initial reading). 201 |
| GET | `/users/{id}` | One profile |

`POST /users` body:

```json
{ "name": "Hema's home", "household_size": 4, "tariff_per_kwh": 6.5, "city": "Coimbatore",
  "has_ac": true, "ac_hours_per_day": 6,
  "initial_reading": { "period": "2026-09", "kwh": 220 } }
```

Validation: name 1-60 chars; household 1-50 whole number; tariff > 0 and <= 100;
ac hours 0-24.

## Readings and footprint

| Method | Path | Description |
|---|---|---|
| GET | `/users/{id}/readings` | All readings, oldest first |
| POST | `/users/{id}/readings` | Save a month. 201 if new, 200 if the month was updated |
| DELETE | `/users/{id}/readings/{rid}` | Delete one reading |
| GET | `/users/{id}/footprint` | Latest, previous, change, per-person kWh, series, formulas, factor |

`POST /users/{id}/readings` body (either `kwh` or both meter fields):

```json
{ "period": "2026-09", "kwh": 220, "tariff_per_kwh": 6.5, "transport_km": 120 }
{ "period": "2026-09", "meter_start": 10500, "meter_end": 10720 }
```

Rules: `period` is `YYYY-MM` and not in the future; kWh > 0 and <= 50,000; `meter_end` > `meter_start`;
tariff defaults to the profile tariff. Cost and emissions are computed on the server and stored with
the emission factor used.

`GET /users/{id}/footprint` (abridged):

```json
{ "has_data": true, "emission_factor": 0.82, "emission_factor_unit": "kg CO2e per kWh",
  "latest":   { "period": "2026-09", "kwh": 220, "cost": 1430.0, "emissions_kg": 180.4 },
  "previous": { "period": "2026-08", "kwh": 200, "cost": 1300.0, "emissions_kg": 164.0 },
  "change":   { "kwh_abs": 20, "kwh_pct": 10.0, "cost_abs": 130, "cost_pct": 10.0,
                "emissions_abs": 16.4, "emissions_pct": 10.0 },
  "per_person_kwh": 55.0, "series": [ "..." ], "formulas": [ "..." ], "disclaimer": "..." }
```

## Missions, progress, recommendations

| Method | Path | Description |
|---|---|---|
| GET | `/users/{id}/challenges` | Missions with `completed_today` and `last_completed_on` |
| POST | `/users/{id}/challenges/{cid}/complete` | Award points. 201, or 409 if already done today |
| GET | `/users/{id}/progress` | Points, streaks, completed count, badges, recent completions |
| GET | `/users/{id}/recommendations` | Rule-based suggestions, each with a `why` |

Recommendations are labelled `"source": "rule-based"`.

## Community

| Method | Path | Description |
|---|---|---|
| GET | `/leaderboard` | Ranked participants; demo accounts have `is_demo: true`. Ties share a rank |
| GET | `/community` | Goal progress (completions vs target), participants, points, readings logged |

## Solar

`POST /solar/estimate`

```json
{ "monthly_kwh": 300, "roof_area_m2": 40, "monthly_bill": 1900, "location": "optional",
  "peak_sun_hours": 5.0, "performance_ratio": 0.78, "area_per_kw": 10, "cost_per_kw": 60000 }
```

The four assumption fields are optional (defaults from `/config`) and range-checked
(sun hours 1-10, ratio 0.5-0.95, area per kW 5-20, cost per kW 10,000-200,000). The response contains
size, generation, offset %, savings, system cost (placeholder), payback years, CO2 avoided,
the formulas, the assumptions used, notes and a "preliminary estimate" label.

## Resources

`GET /resources?q=standby&category=Rooftop%20solar` returns `{ "resources": [...], "categories": [...] }`.
`url` is `null` when no verified link is included.

## AI Energy Coach

`GET /coach/status` always returns `"available": false` in this prototype, with a message.
No generated advice is ever returned.
