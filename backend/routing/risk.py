
RANK = {
    "Low": 0,
    "Moderate": 1,
    "High": 2,
    "Severe": 3,
    "No Travel": 4,
}


def risk(wind_mph, rain_in_hr, snow_in_hr, load_lb):
    """Classify weather risk using Spotter's thresholds."""

    # Wind speed (mph)
    if wind_mph < 25:
        wind = 0
    elif wind_mph < 35:
        wind = 1
    elif wind_mph < 45:
        wind = 2
    elif wind_mph < 55:
        wind = 3
    else:
        wind = 4

    # Rainfall intensity (inches/hour)
    if rain_in_hr < 0.10:
        rain = 0
    elif rain_in_hr < 0.25:
        rain = 1
    elif rain_in_hr < 0.50:
        rain = 2
    elif rain_in_hr <= 1.00:
        rain = 3
    else:
        rain = 4

    # Snowfall intensity (inches/hour)
    if snow_in_hr < 0.5:
        snow = 0
    elif snow_in_hr < 1.0:
        snow = 1
    elif snow_in_hr < 2.0:
        snow = 2
    elif snow_in_hr <= 3.0:
        snow = 3
    else:
        snow = 4

    # Cargo-sensitive wind adjustments
    if wind_mph >= 55:
        wind = 4
    elif wind_mph >= 45 and load_lb > 30000:
        wind = 4
    elif wind_mph >= 35 and load_lb > 40000:
        wind = max(wind, 3)

    return ["Low", "Moderate", "High", "Severe", "No Travel"][
        max(wind, rain, snow)
    ]


def recommend(routes):
    """Prefer safe routes, then rank by Spotter's priorities."""

    if not routes:
        return None

    viable = [
        route for route in routes
        if route["no_travel_miles"] == 0
    ]

    # Do not label a No Travel route as recommended.
    if not viable:
        return None

    best = min(
        viable,
        key=lambda route: (
            route["severe_miles"],
            route["high_miles"],
            route["average_risk"],
            route["duration_hours"],
        ),
    )

    return best["id"]
