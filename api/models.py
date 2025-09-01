from datetime import datetime
from typing import Annotated
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, StringConstraints, field_validator


# Schema used to validate incoming city creation requests from clients.
class CityBase(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)]
    country_code: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)]
    interval_hours: float = Field(ge=0.25, le=2.0, default=2.0)


class CityCreate(CityBase):
    pass


# Response schema returned to clients for city records.
# 'id' is assigned by the database.
class CitySchema(CityBase):
    id: int
    latitude: float
    longitude: float


# Schema for updating only the job interval
class UpdateJobInterval(BaseModel):
    interval_hours: float = Field(ge=0.25, le=2.0)


# Schema used to validate incoming weather report requests from clients.
class WeatherObservationRequest(BaseModel):
    city_id: int
    temperature_unit: Annotated[
        str,
        StringConstraints(pattern="^([Cc]|[Ff])$", to_upper=True),
        Field(default="C", description="The unit of temperature (celsius or fahrenheit)"),
    ]
    timezone: str = Field(default="UTC", description="Must be a valid IANA timezone")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, timezone: str) -> str:
        if timezone not in available_timezones():
            raise ValueError(f"'{timezone}' is not a valid IANA timezone.")
        return timezone


# Schema returned to clients.
# 'id' is assigned by the database. Used for documentation in /docs endpoint
class WeatherObservationRequestSchema(WeatherObservationRequest):
    id: int
    timestamp: datetime
    temperature: float
