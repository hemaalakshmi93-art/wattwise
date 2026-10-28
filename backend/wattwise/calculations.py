"""Pure calculation functions (no database, no Flask). Fully unit-tested.

All results are ESTIMATES based on user-entered values and configurable
assumptions. They are not measurements.
"""

# ---------------------------------------------------------------- footprint


def monthly_cost(kwh, tariff_per_kwh):
    """cost (INR) = kWh x tariff (INR per kWh)"""
    return round(kwh * tariff_per_kwh, 2)


def electricity_emissions_kg(kwh, emission_factor):
    """emissions (kg CO2e) = kWh x emission factor (kg CO2e per kWh)"""
    return round(kwh * emission_factor, 2)


def transport_emissions_kg(km, factor_per_km):
    """transport emissions (kg CO2e) = km x factor (kg CO2e per km)"""
    return round(km * factor_per_km, 2)


def percent_change(previous, current):
    """((current - previous) / previous) x 100, or None when previous is 0."""
    if previous in (0, None):
        return None
    return round((current - previous) / previous * 100, 1)


def compare_readings(previous, current):
    """Compare two reading dicts (needs kwh, cost, emissions_kg)."""
    out = {}
    for key, label in (("kwh", "kwh"), ("cost", "cost"), ("emissions_kg", "emissions")):
        out[f"{label}_abs"] = round(current[key] - previous[key], 2)
        out[f"{label}_pct"] = percent_change(previous[key], current[key])
    return out


FOOTPRINT_FORMULAS = [
    "Monthly cost (INR) = monthly kWh x tariff (INR per kWh)",
    "Electricity emissions (kg CO2e) = monthly kWh x emission factor (kg CO2e per kWh)",
    "Transport emissions (kg CO2e, optional) = km driven x transport factor (kg CO2e per km)",
    "Change (%) = (current - previous) / previous x 100",
    "When meter readings are entered: kWh = end reading - start reading",
]

# ------------------------------------------------------------------- solar

SOLAR_DEFAULTS = {
    "peak_sun_hours": 5.0,        # equivalent full-sun hours per day (assumption)
    "performance_ratio": 0.78,    # real-world losses: heat, wiring, inverter, dust
    "area_per_kw": 10.0,          # m2 of usable roof per kW of panels (assumption)
    "cost_per_kw": 60000.0,       # INR per kW installed (placeholder, get real quotes)
    "days_per_month": 30,
}

SOLAR_LIMITS = {
    "peak_sun_hours": (1.0, 10.0),
    "performance_ratio": (0.5, 0.95),
    "area_per_kw": (5.0, 20.0),
    "cost_per_kw": (10000.0, 200000.0),
}


def solar_estimate(monthly_kwh, roof_area_m2, monthly_bill, emission_factor,
                   peak_sun_hours, performance_ratio, area_per_kw, cost_per_kw,
                   days_per_month=30):
    """Preliminary rooftop-solar sizing. Returns a dict of results + formulas."""
    yield_per_kw_month = peak_sun_hours * performance_ratio * days_per_month
    needed_kw = monthly_kwh / yield_per_kw_month
    roof_limit_kw = roof_area_m2 / area_per_kw

    if needed_kw <= roof_limit_kw:
        size_kw, limited_by = needed_kw, "consumption"
    else:
        size_kw, limited_by = roof_limit_kw, "roof area"
    size_kw = round(size_kw, 2)

    generation = round(size_kw * yield_per_kw_month, 1)
    used = min(generation, monthly_kwh)
    offset_pct = round(used / monthly_kwh * 100, 1)
    effective_tariff = monthly_bill / monthly_kwh
    monthly_savings = round(used * effective_tariff, 2)
    system_cost = round(size_kw * cost_per_kw, 2)
    payback_years = round(system_cost / (monthly_savings * 12), 1) if monthly_savings > 0 else None
    co2_avoided_year = round(generation * 12 * emission_factor, 1)

    notes = [
        "Preliminary estimate only. Not a quotation and not a guarantee of savings.",
        "Subsidies, net-metering terms, shading, roof orientation and vendor pricing are not included.",
    ]
    if size_kw < 0.1:
        notes.append("The roof area entered is too small for a meaningful system at these assumptions.")
    if limited_by == "roof area":
        notes.append("Your roof area, not your consumption, limits the system size.")
    if payback_years is not None and payback_years > 25:
        notes.append("The indicative payback is longer than typical panel lifetimes.")

    return {
        "recommended_size_kw": size_kw,
        "limited_by": limited_by,
        "needed_size_for_full_offset_kw": round(needed_kw, 2),
        "roof_limit_kw": round(roof_limit_kw, 2),
        "yield_kwh_per_kw_month": round(yield_per_kw_month, 1),
        "monthly_generation_kwh": generation,
        "bill_offset_percent": offset_pct,
        "effective_tariff_per_kwh": round(effective_tariff, 2),
        "monthly_savings_inr": monthly_savings,
        "estimated_system_cost_inr": system_cost,
        "payback_years": payback_years,
        "co2_avoided_kg_per_year": co2_avoided_year,
        "formulas": [
            "Yield per kW per month = peak sun hours x performance ratio x days per month",
            "Size needed for full offset (kW) = monthly kWh / yield per kW per month",
            "Roof limit (kW) = roof area (m2) / area needed per kW",
            "Recommended size = the smaller of the size needed and the roof limit",
            "Monthly generation (kWh) = size x yield per kW per month",
            "Effective tariff = monthly bill / monthly kWh",
            "Monthly savings = min(generation, monthly kWh) x effective tariff",
            "System cost = size x cost per kW (placeholder; get real quotes)",
            "Payback (years) = system cost / (monthly savings x 12)",
            "CO2 avoided per year = monthly generation x 12 x emission factor",
        ],
        "notes": notes,
    }
