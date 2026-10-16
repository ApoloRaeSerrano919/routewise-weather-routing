import math
import os
import requests
import threading
import time

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from .risk import risk, RANK, recommend


# Load environment variables from backend/.env
load_dotenv()

S = requests.Session()
S.headers.update({
    "User-Agent": "RouteWise/1.0 (weather-aware routing assessment)"
})

GRAPHOPPER_URL = "https://graphhopper.com/api/1/route"
WEATHER_URL = "https://api.weatherapi.com/v1/forecast.json"
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

RISK_NAMES = ["Low", "Moderate", "High", "Severe", "No Travel"]


def fetch(url, params, timeout=22):
    """Request JSON data from an external API."""
    response = S.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def geocode(query):
    """Convert a US city or address into latitude and longitude."""
    api_key = os.environ.get("GEOAPIFY_API_KEY")

    if not api_key:
        raise RuntimeError("GEOAPIFY_API_KEY is not configured.")

    data = fetch(
        "https://api.geoapify.com/v1/geocode/search",
        {
            "text": query,
            "format": "json",
            "limit": 1,
            "filter": "countrycode:us",
            "apiKey": api_key,
        },
    )

    results = data.get("results", [])

    if not results:
        raise ValueError(f"Could not locate: {query}")

    location = results[0]

    return float(location["lat"]), float(location["lon"])


def graphhopper_routes(start, end):
    """Request up to three genuine route alternatives."""

    api_key = os.getenv("GRAPHHOPPER_API_KEY")

    if not api_key:
        raise ValueError(
            "GRAPHHOPPER_API_KEY is missing from backend/.env"
        )

    params = {
        "point": [
            f"{start[0]},{start[1]}",
            f"{end[0]},{end[1]}",
        ],
        "profile": "car",
        "algorithm": "alternative_route",
        "alternative_route.max_paths": 3,
        "alternative_route.max_weight_factor": 1.8,
        "alternative_route.max_share_factor": 0.8,
        "points_encoded": "false",
        "key": api_key,
    }

    data = fetch(GRAPHOPPER_URL, params, timeout=40)

    paths = data.get("paths", [])

    if not paths:
        raise ValueError("GraphHopper returned no routes")

    return paths[:3]


def distance(a, b):
    """Calculate distance between coordinates in miles."""

    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)

    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin((lon2 - lon1) / 2) ** 2
    )

    return 3958.7613 * 2 * math.asin(
        min(1, math.sqrt(h))
    )


def checkpoints(coords, spacing, total_miles, duration_hours):
    """Generate checkpoints at the requested mileage interval."""

    if len(coords) < 2:
        raise ValueError("Route geometry is incomplete")

    if spacing <= 0:
        raise ValueError("Checkpoint spacing must be positive")

    segments = [
        distance(coords[i], coords[i + 1])
        for i in range(len(coords) - 1)
    ]

    cumulative = [0.0]

    for segment in segments:
        cumulative.append(cumulative[-1] + segment)

    path_length = cumulative[-1]

    if path_length <= 0:
        raise ValueError("Route has zero length")

    targets = [0.0]

    n = 1

    while n * spacing < total_miles:
        targets.append(
            n * spacing * path_length / total_miles
        )
        n += 1

    targets.append(path_length)

    result = []
    segment_index = 0

    for target in targets:

        while (
            segment_index < len(segments) - 1
            and cumulative[segment_index + 1] < target
        ):
            segment_index += 1

        segment_length = segments[segment_index]

        fraction = (
            (target - cumulative[segment_index]) / segment_length
            if segment_length > 0
            else 0.0
        )

        start = coords[segment_index]
        end = coords[segment_index + 1]

        lat = start[0] + fraction * (end[0] - start[0])
        lon = start[1] + fraction * (end[1] - start[1])

        result.append({
            "lat": lat,
            "lon": lon,
            "mile": round(
                target * total_miles / path_length, 2
            ),
            "eta_hours": (
                duration_hours * target / path_length
            ),
        })

    return result


# Forecast responses are shared by requests handled by this Python process.
# Render restarts or multiple workers will each have their own cache.
_WEATHER_CACHE = {}
