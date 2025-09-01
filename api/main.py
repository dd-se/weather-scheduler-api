from contextlib import asynccontextmanager

import requests
from fastapi import Depends, FastAPI, HTTPException, Request, responses, status
from sqlalchemy.orm import Session

from .db import City, WeatherObservation, get_db, get_db_gen, select
from .logging import get_logger
from .models import *
from .scheduler import add_job, remove_job, shutdown_scheduler, start_scheduler, update_job_interval
from .utils import celsius_to_fahrenheit, convert_utc_iso_to_target_timezone
from .weather import fetch_weather_job, get_coordinates

logger = get_logger(__name__)

ALREADY_EXISTS = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job already exists")
NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
OK = responses.JSONResponse({"status": "ok"}, status_code=status.HTTP_200_OK)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup do this
    try:
        db = get_db()
        jobs = db.execute(select(City)).scalars().all()
        for job in jobs:
            add_job(job.id, job.interval_hours, fetch_weather_job, job.id)
        start_scheduler()
        logger.warning("API server started and existing jobs are scheduled")

    finally:
        db.close()

    yield
    # On shutdown do this
    shutdown_scheduler()
    logger.warning("API server stopped, and scheduled jobs are shutdown")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return OK


@app.post("/job/", response_model=CitySchema)
def create_city_job(city: CityCreate, db: Session = Depends(get_db_gen)):
    try:
        stmt = select(City).where(City.name == city.name, City.country_code == city.country_code)
        existing_city_job = db.execute(stmt).scalar()

        if existing_city_job:
            raise ALREADY_EXISTS

        coordinates = get_coordinates(city.name, city.country_code)

        if not coordinates:
            raise NOT_FOUND

        city_in_db = City(
            name=city.name,
            country_code=city.country_code,
            latitude=coordinates[0],
            longitude=coordinates[1],
            interval_hours=city.interval_hours,
        )
        db.add(city_in_db)
        db.commit()
        db.refresh(city_in_db)
        add_job(city_in_db.id, city_in_db.interval_hours, fetch_weather_job, city_in_db.id)

        return city_in_db

    except requests.RequestException as e:
        logger.critical(f"Status code: 500 - Detail: '{e}'")
        return responses.JSONResponse({"detail": "Internal Server Error"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/job/{city_id}", response_model=CitySchema)
def get_city_job(city_id: int, db: Session = Depends(get_db_gen)):
    stmt = select(City).where(City.id == city_id)
    city_job = db.execute(stmt).scalar()

    if not city_job:
        raise NOT_FOUND

    return city_job


@app.put("/job/{city_id}", response_model=CitySchema)
def update_city_job(city_id: int, update: UpdateJobInterval, db: Session = Depends(get_db_gen)):
    stmt = select(City).where(City.id == city_id)
    city_job = db.execute(stmt).scalar()

    if not city_job:
        raise NOT_FOUND

    city_job.interval_hours = update.interval_hours
    db.commit()
    db.refresh(city_job)
    update_job_interval(city_job.id, update.interval_hours, fetch_weather_job, city_job.id)

    return city_job


@app.delete("/job/{city_id}")
def delete_city_job(city_id: int, db: Session = Depends(get_db_gen)):
    city = db.execute(select(City).where(City.id == city_id)).scalar()

    if not city:
        raise NOT_FOUND

    db.delete(city)
    db.commit()
    remove_job(city_id)
    return responses.JSONResponse({"status": f"City ID '{city_id}' deleted"}, status_code=status.HTTP_200_OK)


@app.get("/jobs/", response_model=list[CitySchema])
def get_city_jobs(db: Session = Depends(get_db_gen)):
    city_jobs = db.execute(select(City)).scalars().all()
    return city_jobs


@app.post("/reports/", response_model=list[WeatherObservationRequestSchema])
def get_city_temperatures(request_weather_observation: WeatherObservationRequest, db: Session = Depends(get_db_gen)):
    stmt = select(WeatherObservation).where(WeatherObservation.city_id == request_weather_observation.city_id)
    existing_weather_observations_in_db = db.execute(stmt).scalars().all()

    if not existing_weather_observations_in_db:
        raise NOT_FOUND

    results = []
    for weather_observation in existing_weather_observations_in_db:
        temperature = weather_observation.temperature_c

        if request_weather_observation.temperature_unit != "C":
            temperature = celsius_to_fahrenheit(temperature)

        timestamp = convert_utc_iso_to_target_timezone(
            weather_observation.utc_iso_time,
            request_weather_observation.timezone,
        )

        results.append(
            {
                "id": weather_observation.id,
                "city_id": request_weather_observation.city_id,
                "temperature_unit": request_weather_observation.temperature_unit,
                "temperature": temperature,
                "timezone": request_weather_observation.timezone,
                "timestamp": timestamp,
            }
        )

    return results


@app.exception_handler(status.HTTP_400_BAD_REQUEST)
def bad_request(request: Request, e: HTTPException):
    logger.warning(f"Status code: '{e.status_code}' - Detail: '{e.detail}' - Offender: '{request.client.host}'")
    return responses.JSONResponse({"detail": e.detail}, status_code=e.status_code)


@app.exception_handler(status.HTTP_404_NOT_FOUND)
def not_found(request: Request, e: HTTPException):
    logger.info(f"Status code: '{e.status_code}' - Detail: '{e.detail}' - Offender: '{request.client.host}'")
    return responses.JSONResponse({"detail": e.detail}, status_code=e.status_code)
