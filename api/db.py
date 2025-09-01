from collections.abc import Generator
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
FILE = DB_DIR / "weather_data.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{FILE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, index=True)
    country_code: str = Column(String, index=True)
    latitude: float = Column(Float)
    longitude: float = Column(Float)
    interval_hours: float = Column(Float)
    weather_observations = relationship("WeatherObservation", back_populates="city")


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: int = Column(Integer, primary_key=True, index=True)
    city_id: int = Column(Integer, ForeignKey("cities.id"), index=True)
    utc_iso_time: str = Column(String)
    temperature_c: float = Column(Float)
    city = relationship("City", back_populates="weather_observations")


class Log(Base):
    __tablename__ = "logs"

    id: int = Column(Integer, primary_key=True, index=True)
    timestamp: DateTime = Column(DateTime)
    level: str = Column(String)
    message: str = Column(String)


Base.metadata.create_all(bind=engine)


def get_db_gen() -> Generator[Session, Any, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Session:
    return SessionLocal()
