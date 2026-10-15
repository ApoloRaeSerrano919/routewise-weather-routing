
import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Circle,
  useMap,
} from "react-leaflet";

import type { Route, Result } from "../types/routing";
import { riskColors, unavailableColor } from "../utils/weather";
import CheckpointPopup from "./CheckpointPopup";

type RouteMapProps = {
  result: Result | null;
  route: Route | undefined;
  selected: number;
  hour: number;
  spacing: number;
  heatVisible: boolean;
};

type FitRouteProps = {
  route: Route;
};

function FitRoute({ route }: FitRouteProps) {
  const map = useMap();

  useEffect(() => {
    if (route.coordinates.length === 0) {
      return;
    }

    const bounds = route.coordinates.map(
      ([lat, lon]) => [lat, lon] as [number, number]
    );

    map.fitBounds(bounds, {
      padding: [35, 35],
    });
  }, [map, route]);

  return null;
}

export default function RouteMap({
  result,
  route,
  selected,
  hour,
  spacing,
  heatVisible,
}: RouteMapProps) {
  const hasRoute = route && route.coordinates.length > 0;

  if (!hasRoute) {
    return (
      <div className="mapBox">
        <div className="placeholder">
          <div className="compass">⌖</div>

          <b>Your journey starts here</b>

          <p>
            Enter trip details to visualize alternative
            routes and weather checkpoints.
          </p>
        </div>
      </div>
    );
  }

  const mapCenter: [number, number] = [
    route.coordinates[0][0],
    route.coordinates[0][1],
  ];

  return (
    <div className="mapBox">
      <MapContainer
        center={mapCenter}
        zoom={8}
        style={{
          height: "100%",
          width: "100%",
        }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitRoute route={route} />

        {/* Display all route alternatives */}
        {result?.routes.map((alternative) => {
          const isSelected = alternative.id === selected;

          const positions = alternative.coordinates.map(
            ([lat, lon]) => [lat, lon] as [number, number]
          );

          return (
            <Polyline
              key={alternative.id}
              positions={positions}
              pathOptions={{
                color: isSelected ? "#24a4aa" : "#64748b",
                weight: isSelected ? 6 : 3,
                opacity: isSelected ? 0.95 : 0.4,
              }}
            />
          );
        })}

        {/* Weather-risk overlay at the selected forecast hour */}
        {heatVisible &&
          route.checkpoints.map((checkpoint, index) => {
            const forecastRisk =
              checkpoint.forecast_risks?.[hour] ?? null;

            const fillColor = forecastRisk
              ? riskColors[forecastRisk] ?? unavailableColor
              : unavailableColor;

            return (
              <Circle
                key={`heat-${index}`}
                center={[checkpoint.lat, checkpoint.lon]}
                radius={spacing * 1609.344 * 0.7}
                pathOptions={{
                  stroke: false,
                  fillColor,
                  fillOpacity: forecastRisk ? 0.2 : 0.08,
                }}
              />
            );
          })}

        {/* Checkpoint markers use risk at the truck's arrival time */}
        {route.checkpoints.map((checkpoint, index) => (
          <CircleMarker
            key={index}
            center={[checkpoint.lat, checkpoint.lon]}
            radius={6}
            pathOptions={{
              color: "#10253b",
              fillColor:
                riskColors[checkpoint.risk] ?? unavailableColor,
              fillOpacity: 0.95,
              weight: 1,
            }}
          >
            <CheckpointPopup
              checkpoint={checkpoint}
              hour={hour}
            />
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
