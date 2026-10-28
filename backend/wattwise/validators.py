"""Server-side input validation. Every endpoint validates here, never in the UI only."""
import re

from . import clock

PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ApiError(Exception):
    def __init__(self, message, status=400, fields=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.fields = fields or {}


def require_json(payload):
    if not isinstance(payload, dict):
        raise ApiError("Request body must be a JSON object.")
    return payload


def number(data, key, errors, *, required=True, minimum=None, maximum=None,
           exclusive_min=None, integer=False):
    raw = data.get(key)
    if raw is None or raw == "":
        if required:
            errors[key] = "This field is required."
        return None
    if isinstance(raw, bool):
        errors[key] = "Must be a number."
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        errors[key] = "Must be a number."
        return None
    if value != value or value in (float("inf"), float("-inf")):
        errors[key] = "Must be a finite number."
        return None
    if integer:
        if value != int(value):
            errors[key] = "Must be a whole number."
            return None
        value = int(value)
    if exclusive_min is not None and value <= exclusive_min:
        errors[key] = f"Must be greater than {exclusive_min}."
        return None
    if minimum is not None and value < minimum:
        errors[key] = f"Must be at least {minimum}."
        return None
    if maximum is not None and value > maximum:
        errors[key] = f"Must be at most {maximum}."
        return None
    return value


def text(data, key, errors, *, required=True, max_len=80):
    raw = data.get(key)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        if required:
            errors[key] = "This field is required."
        return None
    if not isinstance(raw, str):
        errors[key] = "Must be text."
        return None
    raw = raw.strip()
    if len(raw) > max_len:
        errors[key] = f"Must be at most {max_len} characters."
        return None
    return raw


def raise_if(errors):
    if errors:
        raise ApiError("Some values are invalid. Please fix them and try again.", 400, errors)


def validate_reading(data, default_tariff):
    """Return a clean dict: period, kwh, tariff, transport_km, source."""
    data = require_json(data)
    errors = {}

    period = data.get("period")
    if not isinstance(period, str) or not PERIOD_RE.match(period):
        errors["period"] = "Use the format YYYY-MM, for example 2026-09."
        period = None
    elif period > clock.today().strftime("%Y-%m"):
        errors["period"] = "The period cannot be in the future."

    kwh = None
    source = "manual"
    has_meter = data.get("meter_start") not in (None, "") or data.get("meter_end") not in (None, "")
    if has_meter and data.get("kwh") in (None, ""):
        start = number(data, "meter_start", errors, minimum=0, maximum=10_000_000)
        end = number(data, "meter_end", errors, minimum=0, maximum=10_000_000)
        if start is not None and end is not None:
            if end <= start:
                errors["meter_end"] = "Must be greater than the starting meter reading."
            else:
                kwh = round(end - start, 3)
                if kwh > 50_000:
                    errors["meter_end"] = "The difference is unrealistically large (over 50,000 kWh)."
                source = "meter"
    else:
        kwh = number(data, "kwh", errors, exclusive_min=0, maximum=50_000)

    tariff = number(data, "tariff_per_kwh", errors, required=False, exclusive_min=0, maximum=100)
    if tariff is None:
        tariff = default_tariff
    transport_km = number(data, "transport_km", errors, required=False, minimum=0, maximum=100_000)

    raise_if(errors)
    return {
        "period": period,
        "kwh": kwh,
        "tariff": tariff,
        "transport_km": transport_km,
        "source": source,
    }


def validate_user(data):
    data = require_json(data)
    errors = {}
    name = text(data, "name", errors, max_len=60)
    household = number(data, "household_size", errors, minimum=1, maximum=50, integer=True)
    tariff = number(data, "tariff_per_kwh", errors, exclusive_min=0, maximum=100)
    city = text(data, "city", errors, required=False, max_len=80)

    has_ac = data.get("has_ac", False)
    if not isinstance(has_ac, bool):
        errors["has_ac"] = "Must be true or false."
    ac_hours = number(data, "ac_hours_per_day", errors, required=False, minimum=0, maximum=24)
    if ac_hours is None:
        ac_hours = 0.0
    if isinstance(has_ac, bool) and not has_ac:
        ac_hours = 0.0

    initial = data.get("initial_reading")
    raise_if(errors)

    clean_initial = None
    if initial is not None:
        try:
            clean_initial = validate_reading(initial, tariff)
        except ApiError as err:
            raise ApiError(
                err.message, 400, {f"initial_reading.{k}": v for k, v in err.fields.items()}
            )
    return {
        "name": name,
        "household_size": household,
        "tariff_per_kwh": tariff,
        "city": city,
        "has_ac": has_ac,
        "ac_hours_per_day": ac_hours,
        "initial_reading": clean_initial,
    }
