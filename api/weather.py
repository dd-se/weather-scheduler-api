from datetime import datetime, timezone
from typing import Literal

import requests

from .db import City, WeatherObservation, get_db, select
from .logging import get_logger
from .models import CityCreate

WEATHER_API = "https://api.open-meteo.com/v1/forecast"
GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"


logger = get_logger(__name__)


def call_api(url: str, query_params: dict):
    response = requests.get(url, params=query_params)
    response.raise_for_status()
    return response


def get_coordinates(city_name: str, country_code: str) -> tuple[float, float] | None:
    query_params = {"name": city_name, "countryCode": country_code}
    data: dict = call_api(GEOCODE_API, query_params).json()
    results: list[dict[str, str]] | None = data.get("results")

    if results:
        first = results[0]
        return float(first["latitude"]), float(first["longitude"])

    return None


def fetch_weather_job(city_id: int):
    try:
        db = get_db()
        city = db.execute(select(City).where(City.id == city_id)).scalar()

        if not city:
            logger.error(f"City ID '{city_id}' not found")
            return

        # The weather API provides a naive (timezone-unaware) ISO-formatted string.
        # To accommodate SQLite's datetime limitations, we store it as a timezone-aware ISO-formatted string in the database.
        #
        # Example:
        #   Weather API response: '2025-08-29T15:30'
        #   Stored in database: '2025-08-29T15:30:00+00:00'
        #
        # This string is post-processed when a user requests a different timezone format via the '/reports/' API endpoint.

        query_params = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "current_weather": True,
            "timezone": "UTC",
        }
        data: dict = call_api(WEATHER_API, query_params).json()
        current_weather = data.get("current_weather")

        if not current_weather:
            logger.error(f"No current weather data for city ID '{city_id}'")
            return

        utc_iso_time: str = datetime.fromisoformat(current_weather["time"]).replace(tzinfo=timezone.utc).isoformat()
        weather_obs_in_db = WeatherObservation(
            city_id=city_id,
            utc_iso_time=utc_iso_time,
            temperature_c=current_weather["temperature"],
        )
        db.add(weather_obs_in_db)
        db.commit()

        logger.info(f"Updated weather for city ID '{city_id}'")
        return True

    except requests.RequestException as e:
        logger.error(f"Error fetching weather for city ID '{city_id}': '{str(e)}'")

    except Exception as e:
        logger.critical(f"Unexpected error for city ID '{city_id}': '{str(e)}'")

    finally:
        db.close()
