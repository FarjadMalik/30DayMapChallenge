#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module to fetch historical weather data from the Open-Meteo Historical Weather API
(https://open-meteo.com/en/docs/historical-weather-api) for a given latitude/longitude
and date range. Data is retrieved in batches to manage memory/time, and saved to CSV.

Usage example:
    python open_meteo_historical.py \
      --lat 33.625 --lon 72.998 \
      --start_date 2019-01-01 --end_date 2025-11-08 \
      --output_file weather_history.csv
"""

import argparse
import datetime
import json
import os
import sys
import time
from typing import List, Dict, Optional

import requests
import pandas as pd

# Constants
API_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
# As per docs: start_date/end_date in ISO format, you choose hourly or daily variables. :contentReference[oaicite:1]{index=1}

DEFAULT_DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "rain_sum"
]
DEFAULT_HOURLY_VARS = [
    "temperature_2m",
    "precipitation"
]


def build_request_url(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    daily_vars: Optional[List[str]] = None,
    hourly_vars: Optional[List[str]] = None,
    timezone: str = "auto"
) -> str:
    """
    Builds the query URL for the Open-Meteo Historical Weather API.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone
    }
    if daily_vars:
        params["daily"] = ",".join(daily_vars)
    if hourly_vars:
        params["hourly"] = ",".join(hourly_vars)

    # convert params to URL query string
    query_parts = [f"{key}={requests.utils.quote(str(value))}" for key, value in params.items()]
    url = f"{API_BASE_URL}?{'&'.join(query_parts)}"
    return url


def fetch_data(url: str, retry: int = 3, pause_sec: float = 1.0) -> Dict:
    """
    Fetches the JSON from given URL. Retries on errors.
    """
    for attempt in range(1, retry + 1):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Warning: attempt {attempt} failed fetching {url}: {e}", file=sys.stderr)
            if attempt < retry:
                time.sleep(pause_sec)
            else:
                raise
    # Should not reach here
    return {}


def process_json_to_dataframe(
    json_data: Dict,
    daily_vars: Optional[List[str]] = None,
    hourly_vars: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Converts the returned JSON into a pandas DataFrame. It handles both daily and hourly values.
    """
    records = []
    timezone = json_data.get("timezone", "")
    # Process daily
    if daily_vars and "daily" in json_data:
        times = json_data["daily"].get("time", [])
        for idx, t in enumerate(times):
            row = {"time": t, "timezone": timezone}
            for var in daily_vars:
                row[var] = json_data["daily"].get(var, [None]*len(times))[idx]
            records.append(row)
    # Process hourly if present (optional)
    if hourly_vars and "hourly" in json_data:
        times = json_data["hourly"].get("time", [])
        for idx, t in enumerate(times):
            row = {"time": t, "timezone": timezone}
            for var in hourly_vars:
                row[var] = json_data["hourly"].get(var, [None]*len(times))[idx]
            records.append(row)

    df = pd.DataFrame.from_records(records)
    # Convert time column to datetime
    df["time"] = pd.to_datetime(df["time"])
    return df


def chunk_date_range(
    start_date: datetime.date,
    end_date: datetime.date,
    max_days: int = 365
) -> List[Dict[str, datetime.date]]:
    """
    Splits a large date range into chunks (of up to max_days) to avoid too large API calls.
    Returns a list of dicts with “start” and “end” keys.
    """
    chunks = []
    current = start_date
    while current <= end_date:
        next_end = min(current + datetime.timedelta(days=max_days - 1), end_date)
        chunks.append({"start": current, "end": next_end})
        current = next_end + datetime.timedelta(days=1)
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Fetch historical weather from Open-Meteo")
    parser.add_argument("--lat", type=float, required=True, help="Latitude of location")
    parser.add_argument("--lon", type=float, required=True, help="Longitude of location")
    parser.add_argument("--start_date", type=str, required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end_date", type=str, required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--output_file", type=str, required=True, help="CSV output file")
    parser.add_argument("--daily_vars", type=str,
                        default=",".join(DEFAULT_DAILY_VARS),
                        help=f"Comma-separated daily variables (default {DEFAULT_DAILY_VARS})")
    parser.add_argument("--hourly_vars", type=str,
                        default="",
                        help=f"Comma-separated hourly variables (optional, default none)")

    args = parser.parse_args()

    latitude = args.lat
    longitude = args.lon
    start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    output_file = args.output_file
    daily_vars_list = [v.strip() for v in args.daily_vars.split(",")] if args.daily_vars else None
    hourly_vars_list = [v.strip() for v in args.hourly_vars.split(",")] if args.hourly_vars else None

    print(f"Fetching historical weather for lat={latitude}, lon={longitude}, "
          f"from {start_date} to {end_date} …")

    # Create chunked ranges
    chunks = chunk_date_range(start_date, end_date, max_days=365)

    # For memory/time efficiency: process chunk by chunk and append to CSV
    first_chunk = True
    for chunk in chunks:
        s = chunk["start"].isoformat()
        e = chunk["end"].isoformat()
        url = build_request_url(latitude=latitude,
                                longitude=longitude,
                                start_date=s,
                                end_date=e,
                                daily_vars=daily_vars_list,
                                hourly_vars=hourly_vars_list)
        print(f"  -- Fetching chunk {s} to {e}")
        json_data = fetch_data(url)
        df = process_json_to_dataframe(json_data,
                                      daily_vars=daily_vars_list,
                                      hourly_vars=hourly_vars_list)
        # Write/append to CSV
        if first_chunk:
            df.to_csv(output_file, index=False, mode="w", header=True)
            first_chunk = False
        else:
            df.to_csv(output_file, index=False, mode="a", header=False)
        # Pause briefly to avoid hammering the service
        time.sleep(1.0)

    print(f"Done. Saved to {output_file}")

if __name__ == "__main__":
    main()
