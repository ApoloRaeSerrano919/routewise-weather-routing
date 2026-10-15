
from django.test import SimpleTestCase

from .risk import risk, recommend


class RiskBoundaryTests(SimpleTestCase):

    def test_wind_boundaries(self):
        self.assertEqual(risk(24.9, 0, 0, 25000), "Low")
        self.assertEqual(risk(25, 0, 0, 25000), "Moderate")
        self.assertEqual(risk(35, 0, 0, 25000), "High")
        self.assertEqual(risk(45, 0, 0, 25000), "Severe")
        self.assertEqual(risk(55, 0, 0, 25000), "No Travel")

    def test_rain_boundaries(self):
        self.assertEqual(risk(0, 0.10, 0, 25000), "Moderate")
        self.assertEqual(risk(0, 0.25, 0, 25000), "High")
        self.assertEqual(risk(0, 0.50, 0, 25000), "Severe")
        self.assertEqual(risk(0, 1.00, 0, 25000), "Severe")
        self.assertEqual(risk(0, 1.01, 0, 25000), "No Travel")

    def test_snow_boundaries(self):
        self.assertEqual(risk(0, 0, 0.5, 25000), "Moderate")
        self.assertEqual(risk(0, 0, 1.0, 25000), "High")
        self.assertEqual(risk(0, 0, 2.0, 25000), "Severe")
        self.assertEqual(risk(0, 0, 3.0, 25000), "Severe")
        self.assertEqual(risk(0, 0, 3.1, 25000), "No Travel")

    def test_load_sensitive_wind(self):
        self.assertEqual(risk(45, 0, 0, 30001), "No Travel")
        self.assertEqual(risk(35, 0, 0, 40001), "Severe")
        self.assertEqual(risk(45, 0, 0, 30000), "Severe")

    def test_no_safe_route(self):
        routes = [
            {
                "id": 1,
                "no_travel_miles": 10,
                "severe_miles": 0,
                "high_miles": 0,
                "average_risk": 1,
                "duration_hours": 3,
            }
        ]
        self.assertIsNone(recommend(routes))