from django.test import SimpleTestCase
from .risk import risk,recommend
class RiskTests(SimpleTestCase):
    def test_wind_boundary(self):
        self.assertEqual(risk(55,0,0,1000),"No Travel")
        self.assertEqual(risk(45,0,0,30001),"No Travel")
        self.assertEqual(risk(35,0,0,40001),"Severe")
        self.assertEqual(risk(25,0,0,1000),"Moderate")
    def test_precipitation(self):
        self.assertEqual(risk(0,0.5,0,1000),"Severe")
        self.assertEqual(risk(0,0,3.1,1000),"No Travel")
    def test_recommendation(self):
        r=lambda id,severe,high,avg,dur,no=0:dict(id=id,severe_miles=severe,high_miles=high,average_risk=avg,duration_hours=dur,no_travel_miles=no)
        self.assertEqual(recommend([r(1,2,0,1,2),r(2,0,3,2,3)]),2)
        self.assertEqual(recommend([r(1,0,0,0,1,1),r(2,1,0,2,2)]),2)
