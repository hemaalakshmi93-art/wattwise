"""Rule-based recommendation engine.

Every recommendation is produced by a plain rule over the user's own saved
data and carries a 'why' that states the rule that fired. This is NOT AI
output and is never presented as such.
"""
from datetime import date, timedelta


def build_recommendations(user, readings, completions, today, per_person_threshold=100):
    """
    user: dict with household_size, has_ac, ac_hours_per_day
    readings: list of dicts sorted by period ASC (kwh, period)
    completions: list of dicts (code, completed_on ISO string)
    """
    recs = []
    latest = readings[-1] if readings else None
    previous = readings[-2] if len(readings) >= 2 else None

    if latest is None:
        recs.append({
            "id": "add_first_reading",
            "title": "Add your first monthly reading",
            "action": "Open My Footprint and enter the units (kWh) from your latest electricity bill.",
            "why": "You have no saved readings yet, so there is nothing to personalise from.",
        })
    elif previous is None:
        recs.append({
            "id": "add_second_reading",
            "title": "Add another month to see a trend",
            "action": "Enter last month's units from an older bill on My Footprint.",
            "why": "You have one saved reading. Two or more are needed to show a change over time.",
        })

    if latest and previous:
        change = (latest["kwh"] - previous["kwh"]) / previous["kwh"] * 100
        if change > 10:
            recs.append({
                "id": "usage_rise",
                "title": "Find out what changed since last month",
                "action": "Compare appliance use and guests or season changes between the two months. "
                          "Try the 'Compare this week with last week' mission.",
                "why": f"Your usage rose {change:.0f}% from {previous['period']} to {latest['period']}.",
            })
        elif change < -5:
            recs.append({
                "id": "usage_drop",
                "title": "Keep the habits that are working",
                "action": "Note what you did differently this month and repeat it.",
                "why": f"Your usage fell {abs(change):.0f}% from {previous['period']} to {latest['period']}.",
            })

    if latest:
        per_person = latest["kwh"] / user["household_size"]
        if per_person > per_person_threshold:
            recs.append({
                "id": "high_per_person",
                "title": "Look for your biggest electricity loads",
                "action": "List your high-wattage appliances (AC, geyser, refrigerator, pump) and "
                          "check how long each runs.",
                "why": f"Your latest reading is {per_person:.0f} kWh per person, above this "
                       f"prototype's rule-of-thumb threshold of {per_person_threshold:.0f}. "
                       "The threshold is configurable and is not an official benchmark.",
            })
        if latest["kwh"] >= 150 and not any(c["code"] == "solar_explore" for c in completions):
            recs.append({
                "id": "try_solar",
                "title": "Check rooftop solar feasibility",
                "action": "Use the Solar Advisor with your consumption and roof area.",
                "why": f"Your latest reading is {latest['kwh']:.0f} kWh a month, and you have not "
                       "tried the solar mission yet.",
            })

    if user["has_ac"] and user["ac_hours_per_day"] >= 6:
        recs.append({
            "id": "ac_hours",
            "title": "Trim air-conditioner running time",
            "action": "Raise the set-point a degree or two, and use a fan during milder hours.",
            "why": f"You told us the AC runs about {user['ac_hours_per_day']:g} hours a day.",
        })

    week_ago = (today - timedelta(days=7)).isoformat()
    recent_codes = {c["code"] for c in completions if c["completed_on"] >= week_ago}
    if "standby_hunt" not in recent_codes:
        recs.append({
            "id": "standby",
            "title": "Hunt for standby power",
            "action": "Switch off idle devices at the socket, starting with TV and chargers.",
            "why": "You have not completed the standby mission in the last 7 days.",
        })
    return recs
