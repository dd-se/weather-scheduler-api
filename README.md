# Weather Scheduler API

This is a FastAPI application and CLI-tool (for management) that allows you to schedule periodic jobs for fetching and storing current weather data (temperature) for specified cities using the Open-Meteo API. Data is stored in a SQLite database, and the API provides endpoints to manage these jobs (create, read, update, delete) and retrieve weather reports in customizable temperature units and timezones.

The scheduler runs in the background using APScheduler, fetching weather data at user-defined intervals (between 0.25 and 2 hours).

## Features

- **CLI Tool**: A command-line interface (`app_ctl.py`) for starting the server or interacting with the API.
- **Job Management**: Create, update, delete, and list scheduled jobs for cities.
- **Scheduling**: Automatically fetches current temperature for cities using Open-Meteo API at user-defined intervals.
- **Customized Reports**: Retrieve historical weather observations for a city, converted to fahrenheit/celsius and adjusted to a specified timezone.
- **Logging**: Multi-handler logging (console, file, database) for errors and info.

## Requirements

- Python 3.10+
- Install dependencies with pip or uv:
  ```bash
  pip install -r requirements.txt
  ```
  ```bash
  uv sync
  ```

## Usage

Run the FastAPI server using Uvicorn:

```bash
uvicorn api.main:app [--reload]
```
Alternatively, use the CLI tool:

```bash
python app_ctl.py server [--dev]
```
The API will be available at `http://127.0.0.1:8000`.

The documentation endpoint will be available at  `http://127.0.0.1:8000/docs`

## CLI Tool (`app_ctl.py`)

The `app_ctl.py` script provides a command-line interface for starting the server or managing jobs via API calls.

Available commands:

- **Start Server**:
  ```bash
  python3 app_ctl.py server [--host 127.0.0.1] [--port 8000] [--dev]
  ```

- **Add City Job**:
  ```bash
  python3 app_ctl.py add Stockholm SE [--interval 1.0]
  ```

  This schedules hourly weather reports for Stockholm, SE.

- **Get City Job**:
  ```bash
  python3 app_ctl.py get 1
  ```
  This gets the job with ID 1.

- **Delete City Job**:
  ```bash
  python3 app_ctl.py delete 1
  ```

- **List All Jobs**:
  ```bash
  python3 app_ctl.py list
  ```

- **Update Job Interval**:
  ```bash
  python3 app_ctl.py update 1 0.5
  ```
  This updates the scheduled interval to every 30 minutes.

- **Get Reports**:
  ```bash
  python3 app_ctl.py temps 1 [--tz Europe/Stockholm] [--unit C|F]
  ```
  Returns list of observations with temperatures in fahrenheit/celsius and timestamps in the specified timezone. Defaults to UTC and celsius.

  Type `--help` for more information.

## Database Schema

- **cities**: Stores city details (id, name, country_code, latitude, longitude, interval_hours).
- **weather_observations**: Stores observations (id, city_id, utc_iso_time, temperature_c).
- **logs**: Stores application logs (id, timestamp, level, message).

## Logging

- Logs are output to console (INFO), file (`logs/logs.txt`, WARNING), and database (`logs` table, WARNING).

## Notes

- Weather and geocoding data are fetched from [Open-Meteo API](https://open-meteo.com/), which is free and requires no API key.

## Flowchart on create city job

![flowchart_create_city_job](<flowchart.jpg>)

## License
MIT