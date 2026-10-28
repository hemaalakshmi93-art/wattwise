"""Single source of 'today' so tests can control dates."""
from datetime import date


def today() -> date:
    return date.today()
