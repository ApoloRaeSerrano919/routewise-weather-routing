
import { useState } from "react";
import type { FormEvent } from "react";

import TripForm from "./components/TripForm";
import type { TripValues } from "./components/TripForm";
import RouteComparison from "./components/RouteComparison";
import RouteMap from "./components/RouteMap";
import WeatherTimeline from "./components/WeatherTimeline";

import { planRoutes } from "./services/routingApi";
import type { Result } from "./types/routing";
import { localDateTime } from "./utils/weather";

export default function App() {
  const [trip, setTrip] = useState<TripValues>({
    origin: "Philadelphia, PA",
    destination: "New York, NY",
    departure: localDateTime(),
    load: 25000,
    spacing: 25,
  });

  const [result, setResult] = useState<Result | null>(null);
  const [selected, setSelected] = useState(1);
  const [hour, setHour] = useState(0);
  const [heatVisible, setHeatVisible] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);
  const [resultSpacing, setResultSpacing] = useState(25);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (loading) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const departureDate = new Date(trip.departure);

      if (Number.isNaN(departureDate.getTime())) {
        throw new Error("Please enter a valid departure date.");
      }

      if (departureDate.getTime() <= Date.now()) {
        throw new Error("Departure must be in the future.");
      }

      if (
        trip.origin.trim().toLowerCase() ===
        trip.destination.trim().toLowerCase()
      ) {
        throw new Error("Origin and destination must be different.");
      }

      const data = await planRoutes({
        origin: trip.origin.trim(),
        destination: trip.destination.trim(),
        departure: departureDate.toISOString(),
        load_lb: trip.load,
        spacing: trip.spacing,
      });

      setResult(data);
      setResultSpacing(trip.spacing);
      setSelected(data.recommended_id ?? data.routes[0].id);
      setHour(0);
      setStale(false);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unexpected error.";

      setError(message);

      if (result) {
        setStale(true);
      }
    } finally {
      setLoading(false);
    }
  }

  const route = result?.routes.find(
    (item) => item.id === selected
  );

  return (
    <main>
      <header>
        <span className="brand">◉ ROUTEWISE</span>
        <span className="tag">
          WEATHER INTELLIGENCE / DEMO
        </span>
      </header>

      <section className="intro">
        <div className="eyebrow">TRIP SAFETY PLANNER</div>

        <h1>
          Find the safer way <em>forward.</em>
        </h1>

        <p>
          Compare alternate routes with forecast-aware checkpoints
          and cargo-sensitive weather risk.
        </p>
      </section>

      <div className="layout">
        <aside className="panel">
          <TripForm
            {...trip}
            loading={loading}
            onChange={(patch) =>
              setTrip((previous) => ({
                ...previous,
                ...patch,
              }))
            }
            onSubmit={submit}
          />

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          {result && (
            <>
              <div className="resultStatus" role="status">
                {loading
                  ? "Updating analysis — previous results shown"
                  : stale
                    ? "Previous results — latest analysis failed"
                    : "Analysis ready"}
              </div>

              <RouteComparison
                result={result}
                selected={selected}
                onSelect={setSelected}
              />
            </>
          )}
        </aside>

        <section className="right">
          <div className="mapTop">
            <h2>Live route intelligence</h2>

            <span>
              {route
                ? `${route.checkpoints.length} forecast checkpoints`
                : "Forecast checkpoints"}
            </span>
          </div>

          <RouteMap
            result={result}
            route={route}
            selected={selected}
            hour={hour}
            spacing={resultSpacing}
            heatVisible={heatVisible}
          />

          <WeatherTimeline
            route={route}
            hour={hour}
            onHourChange={setHour}
            heatVisible={heatVisible}
            onHeatVisibleChange={setHeatVisible}
          />
        </section>
      </div>

      <footer>
        Prototype only — car routing may not respect truck
        restrictions. Never use for real dispatch or navigation.
      </footer>
    </main>
  );
}
