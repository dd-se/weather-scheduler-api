import pytest
from requests import RequestException

from api.weather import fetch_weather_job, get_coordinates


def test_create_weather_job(in_memory_test_db, mock_external_api_requests):
    # Should create a weather observation
    assert fetch_weather_job(city_id=1) is True
    # Should not create a weather observation
    assert fetch_weather_job(city_id=1999) is None


def test_get_coordinates(mock_external_api_requests):
    assert get_coordinates("Stockholm", "SE") == (99.99, 0.01)
    assert get_coordinates("NOT FOUND", "SE") is None
    with pytest.raises(RequestException):
        get_coordinates("RAISE EXCEPTION", "SE")
