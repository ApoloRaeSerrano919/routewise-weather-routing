
"""Standalone unit tests for RouteWise routing and weather logic."""

import sys
import unittest

from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from routing.risk import risk, recommend
from routing.services import checkpoints, weather_batch


class CoreTests(unittest.TestCase):

    def test_risk_boundaries(self):
        self.assertEqual(risk(55, 0, 0, 0), "No Travel")
        self.assertEqual(risk(45, 0, 0, 30001), "No Travel")
        self.assertEqual(risk(35, 0, 0, 40001), "Severe")
        self.assertEqual(risk(25, 0, 0, 0), "Moderate")
        self.assertEqual(risk(0, 1.01, 0, 0), "No Travel")
        self.assertEqual(risk(0, 0, 3.01, 0), "No Travel")

    def test_checkpoints(self):
        result = checkpoints(
            [[40, -75], [40, -74]],
            25,
            52.9,
            1,
        )

        self.assertEqual(result[0]["mile"], 0)
        self.assertEqual(result[-1]["mile"], 52.9)
        self.assertTrue(3 <= len(result) <= 5)

    @patch("routing.services.fetch")
    def test_batched_forecast_and_eta(self, mock_fetch):
        # Use tomorrow instead of a fixed calendar date.
        # Start at 12:00 UTC so all 49 slider hours are covered.
        tomorrow = (
            datetime.now(timezone.utc)
            + timedelta(days=1)
        ).replace(
            hour=12,
            minute=0,
            second=0,
            microsecond=0,
        )

        # Include the preceding day to cover timezone
        # boundaries and ensure a complete forecast.
        start = tomorrow - timedelta(days=1)

        timestamps = [
            (start + timedelta(hours=i)).strftime(
                "%Y-%m-%dT%H:%M"
            )
            for i in range(96)
        ]

        mock_fetch.return_value = {
            "hourly": {
                "time": timestamps,
                "wind_speed_10m": [25] * 96,
                "rain": [0] * 96,
                "snowfall": [0] * 96,
            }
        }

        points = [
            {
                "lat": 40.0,
                "lon": -75.0,
                "eta_hours": 2,
                "mile": 0,
            }
        ]

        weather_batch(
            points,
            tomorrow,
            1000,
        )

        self.assertEqual(
            points[0]["risk"],
            "Moderate",
        )

        self.assertEqual(
            len(points[0]["forecast_risks"]),
            49,
        )

        self.assertEqual(
            points[0]["forecast_risks"][48],
            "Moderate",
        )

        self.assertEqual(
            mock_fetch.call_count,
            1,
        )

    @patch("routing.services.fetch")
    def test_missing_weather_is_not_safe(self, mock_fetch):
        departure = (
            datetime.now(timezone.utc)
            + timedelta(days=1)
        ).replace(
            hour=12,
            minute=0,
            second=0,
            microsecond=0,
        )

        start = departure - timedelta(days=1)

        timestamps = [
            (start + timedelta(hours=i)).strftime(
                "%Y-%m-%dT%H:%M"
            )
            for i in range(96)
        ]

        wind = [25] * 96

        # Missing wind data at checkpoint arrival (+2 hours).
        arrival_index = 24 + 2
        wind[arrival_index] = None

        mock_fetch.return_value = {
            "hourly": {
                "time": timestamps,
                "wind_speed_10m": wind,
                "rain": [0] * 96,
                "snowfall": [0] * 96,
            }
        }

        points = [
            {
                "lat": 40.0,
                "lon": -75.0,
                "eta_hours": 2,
                "mile": 0,
            }
        ]

        with self.assertRaisesRegex(
            ValueError,
            "Weather forecast is unavailable",
        ):
            weather_batch(
                points,
                departure,
                1000,
            )

    def test_recommendation(self):
        def route(
            route_id,
            severe,
            high,
            average,
            hours,
            no_travel=0,
        ):
            return {
                "id": route_id,
                "severe_miles": severe,
                "high_miles": high,
                "average_risk": average,
                "duration_hours": hours,
                "no_travel_miles": no_travel,
            }

        self.assertEqual(
            recommend([
                route(1, 0, 0, 0, 1, 5),
                route(2, 1, 1, 1, 3),
            ]),
            2,
        )

        self.assertEqual(
            recommend([
                route(1, 1, 0, 0, 2),
                route(2, 0, 4, 2, 4),
            ]),
            2,
        )

    def test_all_routes_unsafe(self):
        routes = [
            {
                "id": 1,
                "severe_miles": 0,
                "high_miles": 0,
                "average_risk": 4,
                "duration_hours": 2,
                "no_travel_miles": 10,
            }
        ]

        self.assertIsNone(recommend(routes))


if __name__ == "__main__":
    unittest.main()
