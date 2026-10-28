import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wattwise import create_app  # noqa: E402
from wattwise import clock  # noqa: E402


@pytest.fixture
def today(monkeypatch):
    """Mutable fake 'today'. Use today.set(date(...)) inside a test."""

    class Fake:
        value = date(2026, 10, 28)

        @classmethod
        def set(cls, d):
            cls.value = d

    monkeypatch.setattr(clock, "today", lambda: Fake.value)
    return Fake


@pytest.fixture
def app(tmp_path, today):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "EMISSION_FACTOR": 0.8,
        "TRANSPORT_FACTOR": 0.2,
    })


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(client):
    r = client.post("/api/users", json={
        "name": "Test Home", "household_size": 4, "tariff_per_kwh": 6,
        "has_ac": True, "ac_hours_per_day": 8,
    })
    assert r.status_code == 201
    return r.get_json()["user"]
