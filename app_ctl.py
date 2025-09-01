#!/usr/bin/env python3

import argparse
import json

import requests
import uvicorn


def start_server(host: str, port: int, reload: bool):
    """Start the FastAPI server"""
    uvicorn.run("api.main:app", host=host, port=port, reload=reload, reload_excludes=["app_ctl.py"])


def make_request(method: str, base_url: str, endpoint: str, params: dict | None = None) -> dict:
    """Make HTTP request to the API"""
    url = f"{base_url}{endpoint}"
    print(params)
    try:
        if method == "GET":
            response = requests.get(url)

        elif method == "POST":
            response = requests.post(url, json=params)

        elif method == "PUT":
            response = requests.put(url, json=params)

        elif method == "DELETE":
            response = requests.delete(url)

        else:
            print(f"Unsupported HTTP method: {method}")
            exit(1)

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(str(e))
        try:
            print(e.response.json())
        except:
            pass
        exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Weather API Control Tool")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")

    subparsers = parser.add_subparsers(dest="command", help="Commands", required=True)

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload of the server when (code) files change")

    # Add city command
    add_parser = subparsers.add_parser("add", help="Add a new city job")
    add_parser.add_argument("name", help="City name")
    add_parser.add_argument("country_code", help="Country Code")
    add_parser.add_argument("--interval", type=float, help="Optional update interval hours (float)")

    # Get city command
    get_parser = subparsers.add_parser("get", help="Get a city job")
    get_parser.add_argument("city_id", type=int, help="City ID")

    # Delete city command
    delete_parser = subparsers.add_parser("delete", help="Delete a city job")
    delete_parser.add_argument("city_id", type=int, help="City ID")

    # List jobs command
    subparsers.add_parser("list", help="List all jobs")

    # Update interval command
    update_parser = subparsers.add_parser("update", help="Update a city's job interval")
    update_parser.add_argument("city_id", type=int, help="City ID")
    update_parser.add_argument("interval", type=float, help="New update interval hours (float)")

    # Get temperature reports command
    reports_parser = subparsers.add_parser("temps", help="Get city temperatures")
    reports_parser.add_argument("city_id", type=int, help="City ID")
    reports_parser.add_argument("--tz", type=str, help="Optional timezone")
    reports_parser.add_argument("--unit", type=str, choices=["c", "f", "C", "F"], help="Optional temperature unit")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    base_url = f"http://{args.host}:{args.port}"
    result = None

    if args.command == "server":
        start_server(args.host, args.port, reload=args.reload)

    elif args.command == "add":
        data = {"name": args.name, "country_code": args.country_code}

        if args.interval:
            data["interval_hours"] = args.interval

        result = make_request("POST", base_url, "/job/", data)

    elif args.command == "get":
        result = make_request("GET", base_url, f"/job/{args.city_id}")

    elif args.command == "delete":
        result = make_request("DELETE", base_url, f"/job/{args.city_id}")

    elif args.command == "list":
        result = make_request("GET", base_url, "/jobs/")

    elif args.command == "update":
        result = make_request("PUT", base_url, f"/job/{args.city_id}", {"interval_hours": args.interval})

    elif args.command == "temps":
        data = {"city_id": args.city_id}

        if args.tz:
            data["timezone"] = args.tz

        if args.unit:
            data["temperature_unit"] = args.unit

        result = make_request("POST", base_url, "/reports/", data)

    if result is not None:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
