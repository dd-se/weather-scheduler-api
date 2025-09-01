from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="function")
def client(in_memory_test_db, mock_external_api_requests, mock_scheduler):
    with TestClient(app) as c:
        yield c


# API endpoint tests
def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_city_job(client: TestClient):
    response = client.get("/job/1")
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "NEW YORK"
    assert result["country_code"] == "US"

    response = client.get("/job/2")
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "STOCKHOLM"
    assert result["country_code"] == "SE"

    # Test getting a non-existing city job
    response = client.get("/job/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"


def test_create_city_job(client: TestClient):
    test_city = {"name": "helsingborg", "country_code": "sE", "interval_hours": 0.3}
    response = client.post("/job/", json=test_city)
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == 3
    assert result["name"] == "HELSINGBORG"
    assert result["country_code"] == "SE"
    assert result["interval_hours"] == 0.3
    assert result["latitude"] == 99.99
    assert result["longitude"] == 0.01

    # Test creating duplicate city
    response = client.post("/job/", json=test_city)
    assert response.status_code == 400
    assert response.json()["detail"] == "Job already exists"

    # Test creating a non-existing city
    test_city = {"name": "NOT FOUND", "country_code": "SE", "interval_hours": 0.3}
    response = client.post("/job/", json=test_city)
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"

    # Test sending a invalid request
    test_city = {"name": None, "country_code": "SE", "interval_hours": 0.3}
    response = client.post("/job/", json=test_city)
    assert response.status_code == 422

    # Test external API error
    test_city = {"name": "RAISE EXCEPTION", "country_code": "SE", "interval_hours": 0.3}
    response = client.post("/job/", json=test_city)
    assert response.status_code == 500


def test_update_city_job(client: TestClient):
    # Get existing New York city
    response = client.get("/job/1")
    old_interval_hours = response.json()["interval_hours"]
    assert old_interval_hours == 0.25

    # Test updating interval hours
    update_data = {"interval_hours": 2}
    response = client.put("/job/1", json=update_data)
    assert response.status_code == 200

    new_interval_hours = response.json()["interval_hours"]
    assert new_interval_hours == 2
    assert new_interval_hours != old_interval_hours

    # Test updating non-existent city
    response = client.put("/job/9999", json=update_data)
    assert response.status_code == 404

    # Test updating with interval hours > 2
    response = client.put("/job/1", json={"interval_hours": 2.0001})
    assert response.status_code == 422


def test_delete_city_job(client: TestClient):
    # Test deleting existing city
    response = client.delete("/job/1")
    assert response.status_code == 200
    assert response.json() == {"status": "City ID '1' deleted"}

    # Verify city is deleted
    response = client.get("/job/1")
    assert response.status_code == 404

    # Test deleting non-existent city
    response = client.delete("/job/999999")
    assert response.status_code == 404


def test_get_city_jobs(client: TestClient):
    # Test getting the two cities we create for every test
    response = client.get("/jobs/")
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 2


def test_get_city_temperatures(client: TestClient):
    # Test getting weather reports
    data = {"city_id": 1, "temperature_unit": "C", "timezone": "Europe/Stockholm"}
    response = client.post("/reports/", json=data)
    response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    obs_1 = result[0]
    assert obs_1["city_id"] == 1
    assert obs_1["temperature_unit"] == "C"
    assert obs_1["timezone"] == "Europe/Stockholm"
    assert "temperature" in obs_1
    assert "timestamp" in obs_1

    data = {"city_id": 2, "temperature_unit": "F", "timezone": "America/New_York"}
    obs_2 = client.post("/reports/", json=data).json()[0]
    assert obs_2["temperature_unit"] == "F"
    assert obs_2["timezone"] == "America/New_York"

    # Fahrenheit should be greater than Celcius as a value
    assert obs_2["temperature"] > obs_1["temperature"]

    # Assert timestamp strings are not equal
    assert obs_1["timestamp"] != obs_2["timestamp"]

    new_york_time = datetime.fromisoformat(obs_2["timestamp"])
    stockholm_time = datetime.fromisoformat(obs_1["timestamp"])
    # Assert that as datetime objects they are equal
    assert new_york_time == stockholm_time

    # Test getting non-existing weather reports
    data = {"city_id": 9999, "temperature_unit": "F", "timezone": "America/New_York"}
    response = client.post("/reports/", json=data)
    assert response.status_code == 404

    # Test sending a invalid timezone
    data = {"city_id": 1, "temperature_unit": "C", "timezone": "Invalid/Timezone"}
    response = client.post("/reports/", json=data)
    assert response.status_code == 422
