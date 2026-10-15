# RouteWise — Weather-Aware Truck Routing

A full-stack prototype built for the Spotter Full Stack Developer assessment.

RouteWise compares alternative road routes using forecast weather conditions, estimated checkpoint arrival times, and cargo-weight-sensitive risk rules.

## Technology Stack

**Frontend**
- React 18, TypeScript, Vite
- React Leaflet and OpenStreetMap
- Responsive route comparison and weather visualization

**Backend**
- Python and Django
- GraphHopper Routing API
- OpenStreetMap Nominatim geocoding
- Open-Meteo hourly weather forecasts

## Features

- Enter origin, destination, departure date/time, and truck load weight
- Request up to three alternative routes through GraphHopper
- Sample weather at approximately 10-, 25-, or 50-mile intervals
- Calculate checkpoint ETAs using estimated route travel duration
- Evaluate wind, rainfall, and snowfall risk
- Apply additional wind restrictions for heavier loads
- Compare Severe, High, and No Travel mileage across routes
- Recommend a route when an acceptable alternative exists
- Display routes and weather checkpoints on an interactive map
- Explore forecast risk using a 0–48-hour timeline slider
- Display a geographic checkpoint-based weather-risk overlay

## Risk Classification

| Level | Wind (mph) | Rain (in/hr) | Snow (in/hr) |
|---|---|---|---|
| Low | Below 25 | Below 0.10 | Below 0.5 |
| Moderate | 25–34 | 0.10–0.25 | 0.5–1.0 |
| High | 35–44 | Above 0.25–0.50 | Above 1.0–2.0 |
| Severe | 45–54 | Above 0.50–1.00 | Above 2.0–3.0 |
| No Travel | 55+ | Above 1.00 | Above 3.0 |

Additional cargo-sensitive restrictions:

- Wind of at least 45 mph with a load above 30,000 lb: No Travel
- Wind of at least 35 mph with a load above 40,000 lb: at least Severe
- Wind of at least 55 mph: No Travel regardless of load

The highest applicable weather-risk category determines checkpoint risk.

Routes are ranked by Severe miles, High miles, average risk, and travel duration. Routes containing No Travel mileage are excluded from recommendation.

## Local Installation

### Backend

Requires Python 3.11+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure your own GraphHopper API key.

```dotenv
GRAPHHOPPER_API_KEY=your_key_here
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Start Django:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py runserver
```

The backend runs at `http://127.0.0.1:8000`.

### Frontend

Requires a Node.js version compatible with the installed Vite release.

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

The Vite development server proxies `/api` requests to Django.

## API

**POST `/api/plan/`**

Example request:

```json
{
  "origin": "Philadelphia, PA",
  "destination": "Pittsburgh, PA",
  "departure": "2026-10-16T14:00:00Z",
  "load_lb": 25000,
  "spacing": 25
}
```

Use a future departure timestamp when testing.

## Testing

Run Django tests:

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py test
```

Run standalone routing tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s routing -p "test_*unit.py" -v
```

Build the frontend:

```powershell
cd frontend
npm run build
```

## Important Limitations

This is an assessment prototype, not a production trucking navigation system.

- GraphHopper currently uses a car-routing profile; routes have not been validated for truck-specific height, weight, or road restrictions.
- The routing provider may return fewer than three alternatives for some trips.
- Route ETAs are estimates and do not incorporate all real-world driving conditions.
- Weather forecasts are hourly estimates rather than live road observations.
- The geographic weather overlay uses sampled checkpoint regions, not a continuous meteorological grid.
- Missing weather data is not interpreted as safe conditions.
- The application does not currently include production-grade authentication, request throttling, caching, or monitoring.
- External API quotas and usage policies apply.

**Do not use this application for actual dispatch, truck navigation, or safety-critical decisions.**

## Deployment

Production deployment requires:

- A secure `DJANGO_SECRET_KEY`
- `DEBUG=0`
- Configured `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- A private GraphHopper API key stored as a backend environment variable
- A production Django application server
- A hosted frontend configured to communicate with the deployed API

## Assessment Submission

- GitHub source repository
- Publicly accessible application
- 5–10-minute Loom demonstration
