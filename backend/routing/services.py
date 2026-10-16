
import math
import os
import requests
from django.core.cache import cache

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


def weather_batch(points, departure, load_lb):
    """Attach WeatherAPI.com hourly forecasts to route checkpoints.

    The API is queried per approximate location, with a 10-minute Django
    cache to avoid re-requesting identical forecast locations.
    """
    key = os.environ.get("WEATHERAPI_API_KEY")
    if not key:
        raise RuntimeError("WEATHERAPI_API_KEY is not configured.")
    if departure.tzinfo is None:
        raise ValueError("Departure datetime must include a timezone.")

    now = datetime.now(timezone.utc)
    departure = departure.astimezone(timezone.utc)
    if departure < now:
        raise ValueError("Departure must be in the future.")
    # The free plan covers three calendar days, not 72 rolling hours.
    # Keep departure close to now; arrival forecast availability is
    # verified independently for every checkpoint.
    if departure > now + timedelta(hours=24):
        raise ValueError("Choose a departure within the next 24 hours on the free weather plan.")

    # Avoid duplicate requests for checkpoints near each other.
    forecasts_by_location = {}
    for point in points:
        location = (round(point["lat"], 2), round(point["lon"], 2))
        if location not in forecasts_by_location:
            cache_key = f"routewise_weatherapi_v1_{location[0]}_{location[1]}"
            hours = cache.get(cache_key)
            if hours is None:
                response = S.get(WEATHER_URL, params={
                    "key": key,
                    "q": f"{location[0]},{location[1]}",
                    "days": 3,
                    "aqi": "no",
                    "alerts": "no",
                }, timeout=25)
                if not response.ok:
                    try:
                        detail = response.json().get("error", {}).get("message", "")
                    except ValueError:
                        detail = ""
                    # Never expose the key or full URL in an exception.
                    raise RuntimeError(
                        f"WeatherAPI.com returned HTTP {response.status_code}"
                        + (f": {detail}" if detail else "")
                    )
                payload = response.json()
                days = payload.get("forecast", {}).get("forecastday", [])
                hours = [hour for day in days for hour in day.get("hour", [])]
                if not hours:
                    raise ValueError("WeatherAPI.com returned no hourly forecast data.")
                cache.set(cache_key, hours, timeout=600)
            forecasts_by_location[location] = hours

    for point in points:
        location = (round(point["lat"], 2), round(point["lon"], 2))
        hours = forecasts_by_location[location]
        def sample(when):
            target = when.timestamp()
            closest = min(hours, key=lambda h: abs(h["time_epoch"] - target))
            if abs(closest["time_epoch"] - target) > 3600:
                return None
            values = (closest.get("wind_mph"), closest.get("precip_in"), closest.get("snow_cm"))
            if any(value is None for value in values):
                return None
            wind, rain, snow = float(values[0]), float(values[1]), float(values[2]) / 2.54
            if not all(math.isfinite(x) and x >= 0 for x in (wind, rain, snow)):
                return None
            return {
                "wind_mph": round(wind, 2),
                "rain_in_hr": round(rain, 3),
                "snow_in_hr": round(snow, 3),
                "risk": risk(wind, rain, snow, load_lb),
            }

        eta = departure + timedelta(hours=point["eta_hours"])
        arrival = sample(eta)
        if arrival is None:
            raise ValueError("Weather forecast unavailable for a checkpoint arrival time. Choose an earlier departure.")
        point.update(arrival)
        point["eta"] = eta.isoformat()
        point["forecast_risks"] = [
            (reading["risk"] if (reading := sample(departure + timedelta(hours=h))) else None)
            for h in range(49)
        ]
        del point["eta_hours"]
    return points


def build(origin, destination, departure, load_lb, spacing):
    """
    Build weather-aware route alternatives.

    Returns data compatible with the existing React frontend.
    """

    start = geocode(origin)
    end = geocode(destination)

    paths = graphhopper_routes(start, end)

    output = []
    route_points = []

    for path in paths:

        # GraphHopper returns [longitude, latitude].
        # Leaflet frontend expects [latitude, longitude].
        coords = [
            [lat, lon]
            for lon, lat in path["points"]["coordinates"]
        ]

        miles = path["distance"] / 1609.344

        # GraphHopper duration is milliseconds.
        hours = path["time"] / 3_600_000

        cps = checkpoints(
            coords,
            spacing,
            miles,
            hours,
        )

        route_points.append(
            (coords, miles, hours, cps)
        )

    # Request weather in batches across all routes.
    all_points = [
        cp
        for _, _, _, cps in route_points
        for cp in cps
    ]

    weather_batch(
        all_points,
        departure,
        load_lb,
    )

    for index, (coords, miles, hours, cps) in enumerate(
        route_points
    ):

        totals = {
            "High": 0.0,
            "Severe": 0.0,
            "No Travel": 0.0,
        }

        weighted = 0.0

        for a, b in zip(cps, cps[1:]):

            length = b["mile"] - a["mile"]

            # Use the higher risk of the segment endpoints.
            grade = max(
                RANK[a["risk"]],
                RANK[b["risk"]],
            )

            category = RISK_NAMES[grade]

            if category in totals:
                totals[category] += length

            weighted += grade * length

        output.append({
            "id": index + 1,
            "distance_miles": round(miles, 1),
            "duration_hours": round(hours, 2),
            "coordinates": coords,
            "checkpoints": cps,
            "high_miles": round(
                totals["High"], 1
            ),
            "severe_miles": round(
                totals["Severe"], 1
            ),
            "no_travel_miles": round(
                totals["No Travel"], 1
            ),
            "average_risk": (
                round(weighted / miles, 3)
                if miles > 0
                else 0
            ),
        })

    return {
        "routes": output,
        "recommended_id": recommend(output),
        "warning": (
            "GraphHopper car-profile routes are for "
            "assessment demonstration only. "
            "They are not validated for commercial "
            "truck navigation."
        ),
        "alternatives_found": len(output),
    }
