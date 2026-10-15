
import math
import os
import requests

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
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
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
    """
    Fetch hourly weather forecasts for route checkpoints.

    Provides:
    - Weather conditions at each checkpoint's estimated arrival
    - Wind, rain, and snowfall risk classifications
    - Hourly risk data for the 0–48-hour heatmap slider

    Missing weather measurements are never treated as safe.
    """

    now = datetime.now(timezone.utc)

    # Ensure departure has timezone information.
    if departure.tzinfo is None:
        raise ValueError(
            "Departure datetime must include a timezone."
        )

    departure = departure.astimezone(timezone.utc)

    # Validate departure time.
    if departure < now:
        raise ValueError(
            "Departure must be in the future."
        )

    if departure > now + timedelta(days=5):
        raise ValueError(
            "Departure is too far ahead for the "
            "available 48-hour weather forecast."
        )

    results = []

    # Fetch forecasts for up to 25 locations per request.
    for offset in range(0, len(points), 25):
        batch = points[offset:offset + 25]

        data = fetch(
            WEATHER_URL,
            {
                "latitude": ",".join(
                    str(round(point["lat"], 5))
                    for point in batch
                ),
                "longitude": ",".join(
                    str(round(point["lon"], 5))
                    for point in batch
                ),
                "hourly": "wind_speed_10m,rain,snowfall",
                "wind_speed_unit": "mph",
                "precipitation_unit": "inch",
                "timezone": "UTC",
                "forecast_days": 8,
            },
            timeout=40,
        )

        forecasts = (
            data if isinstance(data, list) else [data]
        )

        if len(forecasts) != len(batch):
            raise ValueError(
                "Weather service returned an unexpected "
                "number of forecast locations."
            )

        for checkpoint, forecast in zip(batch, forecasts):
            hourly = forecast["hourly"]

            times = [
                datetime.fromisoformat(timestamp).replace(
                    tzinfo=timezone.utc
                )
                for timestamp in hourly["time"]
            ]

            if not times:
                raise ValueError(
                    "Weather service returned no hourly forecasts."
                )

            def sample(when):
                """
                Select the nearest hourly forecast.

                Return None if the requested time is outside
                the available forecast range or if any required
                measurement is missing.
                """

                index = min(
                    range(len(times)),
                    key=lambda i: abs(
                        (times[i] - when).total_seconds()
                    ),
                )

                difference = abs(
                    (times[index] - when).total_seconds()
                )

                # Do not use a forecast more than one hour
                # away from the requested time.
                if difference > 3600:
                    return None

                wind_value = hourly["wind_speed_10m"][index]
                rain_value = hourly["rain"][index]
                snow_value = hourly["snowfall"][index]

                # Missing data must not be interpreted as
                # zero wind, zero rain, or zero snowfall.
                if any(
                    value is None
                    for value in (
                        wind_value,
                        rain_value,
                        snow_value,
                    )
                ):
                    return None

                wind = float(wind_value)
                rain = float(rain_value)

                # Open-Meteo snowfall is reported in cm.
                # Convert to inches for Spotter's thresholds.
                snow_in_hr = float(snow_value) / 2.54

                # Reject invalid numeric measurements.
                if not all(
                    math.isfinite(value)
                    for value in (
                        wind,
                        rain,
                        snow_in_hr,
                    )
                ):
                    return None

                if min(wind, rain, snow_in_hr) < 0:
                    return None

                risk_level = risk(
                    wind,
                    rain,
                    snow_in_hr,
                    load_lb,
                )

                return {
                    "wind_mph": round(wind, 2),
                    "rain_in_hr": round(rain, 3),
                    "snow_in_hr": round(snow_in_hr, 3),
                    "risk": risk_level,
                }

            # Calculate when the truck reaches this checkpoint.
            eta = departure + timedelta(
                hours=checkpoint["eta_hours"]
            )

            arrival_weather = sample(eta)

            if arrival_weather is None:
                raise ValueError(
                    "Weather forecast is unavailable for "
                    "a checkpoint's estimated arrival time."
                )

            # Store arrival-time weather measurements.
            checkpoint.update(arrival_weather)
            checkpoint["eta"] = eta.isoformat()

            # Generate risk classifications for the slider:
            # +0h, +1h, ... +48h from departure.
            forecast_risks = []

            for hour in range(49):
                forecast_time = departure + timedelta(
                    hours=hour
                )

                hourly_weather = sample(forecast_time)

                if hourly_weather is None:
                    forecast_risks.append(None)
                else:
                    forecast_risks.append(
                        hourly_weather["risk"]
                    )

            checkpoint["forecast_risks"] = forecast_risks

            # Remove the temporary ETA offset.
            del checkpoint["eta_hours"]

            results.append(checkpoint)

    return results


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
