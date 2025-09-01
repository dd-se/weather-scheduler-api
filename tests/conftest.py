from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from requests import RequestException
from sqlalchemy.pool import StaticPool

from api.db import Base, City, WeatherObservation, create_engine, sessionmaker
from api.weather import GEOCODE_API, WEATHER_API

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

GEOCODE_API_EXAMPLE_RESPONSE = {"results": [{"id": 2673730, "name": "Stockholm", "latitude": 99.99, "longitude": 0.01}]}
WEATHER_API_EXAMPLE_RESPONSE = {"current_weather": {"time": "2025-08-30T18:00", "interval": 900, "temperature": 17.6, "windspeed": 4.7}}


class MockResponseObject:
    def __init__(self, mock_data: dict = {}):
        self.mock_data = mock_data

    def json(self):
        return self.mock_data


def mock_call_api(url: str, params: dict):
    if params.get("name") == "RAISE EXCEPTION":
        raise RequestException("mocked")
    if params.get("name") == "NOT FOUND":
        return MockResponseObject()
    if url == GEOCODE_API:
        return MockResponseObject(GEOCODE_API_EXAMPLE_RESPONSE)
    if url == WEATHER_API:
        return MockResponseObject(WEATHER_API_EXAMPLE_RESPONSE)
    raise ValueError("Something went wrong!")


@pytest.fixture(scope="function")
def in_memory_test_db(monkeypatch):
    monkeypatch.setattr("api.db.engine", test_engine)
    monkeypatch.setattr("api.db.SessionLocal", TestingSessionLocal)

    Base.metadata.create_all(bind=test_engine)

    try:
        db = TestingSessionLocal()
        city_1 = City(name="NEW YORK", country_code="US", latitude=0.5, longitude=-0.5, interval_hours=0.25)
        city_2 = City(name="STOCKHOLM", country_code="SE", latitude=0.3, longitude=0.2, interval_hours=0.5)

        now = datetime.now(timezone.utc).isoformat()
        obs_1 = WeatherObservation(city_id=1, temperature_c=9, utc_iso_time=now)
        obs_2 = WeatherObservation(city_id=2, temperature_c=9, utc_iso_time=now)

        db.add_all([city_1, city_2, obs_1, obs_2])
        db.commit()

    finally:
        db.close()

    yield  # Run the test

    # Teardown on test finish
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def mock_external_api_requests(monkeypatch):
    monkeypatch.setattr("api.weather.call_api", mock_call_api)


@pytest.fixture(scope="function")
def mock_scheduler(monkeypatch):
    dummy_scheduler = Mock()
    monkeypatch.setattr("api.scheduler.scheduler", dummy_scheduler)
