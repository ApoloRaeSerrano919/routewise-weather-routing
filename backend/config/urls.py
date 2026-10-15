
from django.urls import path
from routing.views import plan, location_suggestions

urlpatterns = [
    path("api/plan/", plan),
    path(
        "api/locations/",
        location_suggestions,
        name="location_suggestions",
    ),
]
