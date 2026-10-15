import json
from datetime import datetime,timezone,timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import build
@csrf_exempt
def plan(request):
    if request.method!="POST":return JsonResponse({"error":"POST required"},status=405)
    try:
        data=json.loads(request.body)
        origin=str(data["origin"]).strip()
        destination=str(data["destination"]).strip()
        load=float(data["load_lb"])
        spacing=int(data["spacing"])
        if not origin or not destination or not (0<=load<=200000) or spacing not in (10,25,50):
            raise ValueError("Invalid origin, destination, load or checkpoint spacing")
        dt=datetime.fromisoformat(data["departure"].replace("Z","+00:00"))
        if dt.tzinfo is None:raise ValueError("Departure must include a timezone offset")
        dt=dt.astimezone(timezone.utc)
        if dt<datetime.now(timezone.utc):raise ValueError("Departure must be in the future")
        if dt>datetime.now(timezone.utc)+timedelta(days=5):raise ValueError("Choose a departure within the next five days for the 48-hour forecast")
        return JsonResponse(build(origin,destination,dt,load,spacing))
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        return JsonResponse({"error":str(exc)},status=400)
    except Exception:
        return JsonResponse({"error":"Routing or weather provider unavailable. Try again shortly."},status=502)


import os
import requests

from django.core.cache import cache
from django.views.decorators.http import require_GET


@require_GET
def location_suggestions(request):
    query = request.GET.get("q", "").strip()

    if len(query) < 3:
        return JsonResponse({"suggestions": []})

    if len(query) > 120:
        return JsonResponse(
            {"error": "Search text is too long."},
            status=400,
        )

    api_key = os.environ.get("GEOAPIFY_API_KEY")

    if not api_key:
        return JsonResponse(
            {"error": "Location autocomplete is not configured."},
            status=503,
        )

    cache_key = "location_suggestions:" + query.casefold()
    cached = cache.get(cache_key)

    if cached is not None:
        return JsonResponse({"suggestions": cached})

    try:
        response = requests.get(
            "https://api.geoapify.com/v1/geocode/autocomplete",
            params={
                "text": query,
                "format": "json",
                "limit": 6,
                "filter": "countrycode:us",
                "apiKey": api_key,
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        suggestions = []
        seen = set()

        for item in data.get("results", []):
            label = item.get("formatted")

            if not label or label in seen:
                continue

            seen.add(label)
            suggestions.append({
                "label": label,
                "lat": item.get("lat"),
                "lon": item.get("lon"),
            })

        cache.set(cache_key, suggestions, timeout=3600)

        return JsonResponse({"suggestions": suggestions})

    except requests.RequestException:
        return JsonResponse(
            {"error": "Location search is temporarily unavailable."},
            status=502,
        )

