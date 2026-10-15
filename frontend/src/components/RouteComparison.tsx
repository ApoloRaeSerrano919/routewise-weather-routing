
import type { Result } from "../types/routing";

type RouteComparisonProps = {
  result: Result;
  selected: number;
  onSelect: (id: number) => void;
};

export default function RouteComparison({
  result,
  selected,
  onSelect,
}: RouteComparisonProps) {
  const hasSafeRoute = result.recommended_id !== null;

  return (
    <section aria-label="Route comparison">
      <h2 className="subhead">Route comparison</h2>

      <p className="hint">
        {result.alternatives_found} distinct{" "}
        {result.alternatives_found === 1 ? "route" : "routes"}{" "}
        returned by provider
      </p>

      {!hasSafeRoute && (
        <p className="error" role="alert">
          No safe route available. Every alternative contains
          No Travel weather conditions.
        </p>
      )}

      {result.routes.map((route) => {
        const isSelected = selected === route.id;
        const hasNoTravelConditions = route.no_travel_miles > 0;
        const isRecommended = result.recommended_id === route.id;

        return (
          <button
            key={route.id}
            type="button"
            className={`routeCard ${isSelected ? "active" : ""}`}
            aria-pressed={isSelected}
            onClick={() => onSelect(route.id)}
          >
            <div className="routeTitle">
              <span>ROUTE {route.id}</span>

              {isRecommended && (
                <span className="pill">
                  RECOMMENDED
                </span>
              )}

              {hasNoTravelConditions && (
                <span className="riskPill">
                  NO TRAVEL
                </span>
              )}
            </div>

            <div className="routeNumbers">
              <b>
                {route.distance_miles.toLocaleString()}
                <small> mi</small>
              </b>

              <span>
                {route.duration_hours.toFixed(2)} hr
              </span>
            </div>

            <div className="routeMetrics">
              <span>
                Severe{" "}
                <b>{route.severe_miles} mi</b>
              </span>

              <span>
                High{" "}
                <b>{route.high_miles} mi</b>
              </span>
            </div>

            {hasNoTravelConditions && (
              <div className="blocked">
                No Travel conditions:{" "}
                {route.no_travel_miles} mi
              </div>
            )}

            {isSelected && (
              <span className="selectedHint">
                Viewing on map ✓
              </span>
            )}
          </button>
        );
      })}
    </section>
  );
}
