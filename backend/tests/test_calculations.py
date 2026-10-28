from datetime import date

import pytest

from wattwise import calculations as calc
from wattwise.gamification import streaks


def test_cost_and_emissions():
    assert calc.monthly_cost(200, 6.5) == 1300.0
    assert calc.electricity_emissions_kg(200, 0.82) == 164.0
    assert calc.transport_emissions_kg(100, 0.17) == 17.0


def test_percent_change():
    assert calc.percent_change(100, 110) == 10.0
    assert calc.percent_change(200, 150) == -25.0
    assert calc.percent_change(0, 50) is None


def test_compare_readings():
    prev = {"kwh": 100, "cost": 600, "emissions_kg": 80}
    cur = {"kwh": 120, "cost": 720, "emissions_kg": 96}
    out = calc.compare_readings(prev, cur)
    assert out["kwh_abs"] == 20 and out["kwh_pct"] == 20.0
    assert out["cost_abs"] == 120 and out["emissions_pct"] == 20.0


def _solar(**over):
    args = dict(monthly_kwh=300, roof_area_m2=100, monthly_bill=1800, emission_factor=0.8,
                peak_sun_hours=5, performance_ratio=0.8, area_per_kw=10, cost_per_kw=60000)
    args.update(over)
    return calc.solar_estimate(**args)


def test_solar_sized_by_consumption():
    r = _solar()
    # yield = 5 * 0.8 * 30 = 120 kWh/kW/month; 300 / 120 = 2.5 kW
    assert r["yield_kwh_per_kw_month"] == 120.0
    assert r["recommended_size_kw"] == 2.5
    assert r["limited_by"] == "consumption"
    assert r["monthly_generation_kwh"] == 300.0
    assert r["bill_offset_percent"] == 100.0
    assert r["monthly_savings_inr"] == 1800.0
    assert r["estimated_system_cost_inr"] == 150000.0
    assert r["payback_years"] == round(150000 / (1800 * 12), 1)
    assert r["co2_avoided_kg_per_year"] == 300 * 12 * 0.8


def test_solar_limited_by_roof():
    r = _solar(roof_area_m2=10)  # 1 kW max
    assert r["recommended_size_kw"] == 1.0
    assert r["limited_by"] == "roof area"
    assert r["bill_offset_percent"] == 40.0
    assert r["monthly_savings_inr"] == 720.0  # 120 kWh * 6 INR


def test_solar_responds_to_assumptions():
    low = _solar(peak_sun_hours=4)
    high = _solar(peak_sun_hours=6)
    assert low["recommended_size_kw"] > high["recommended_size_kw"]
    assert _solar(cost_per_kw=30000)["payback_years"] < _solar()["payback_years"]


def test_solar_tiny_roof_note():
    r = _solar(roof_area_m2=0.5)
    assert any("too small" in n for n in r["notes"])


def test_streaks():
    today = date(2026, 10, 28)
    d = lambda n: date(2026, 10, n)  # noqa: E731
    assert streaks(set(), today) == (0, 0)
    assert streaks({d(28)}, today) == (1, 1)
    assert streaks({d(26), d(27), d(28)}, today) == (3, 3)
    # nothing today yet: streak survives until a full day is missed
    assert streaks({d(26), d(27)}, today) == (2, 2)
    # a gap breaks the current streak but longest is remembered
    assert streaks({d(20), d(21), d(22), d(23), d(27)}, today) == (1, 4)
