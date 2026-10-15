
export type RiskLevel =
  | "Low"
  | "Moderate"
  | "High"
  | "Severe"
  | "No Travel";

export type Checkpoint = {
  lat: number;
  lon: number;
  mile: number;
  eta: string;
  risk: RiskLevel;
  wind_mph: number;
  rain_in_hr: number;
  snow_in_hr: number;
  forecast_risks: (RiskLevel | null)[];
};

export type Route = {
  id: number;
  distance_miles: number;
  duration_hours: number;
  coordinates: number[][];
  checkpoints: Checkpoint[];
  high_miles: number;
  severe_miles: number;
  no_travel_miles: number;
  average_risk: number;
};

export type Result = {
  routes: Route[];
  recommended_id: number | null;
  warning: string;
  alternatives_found: number;
};

export type TripRequest = {
  origin: string;
  destination: string;
  departure: string;
  load_lb: number;
  spacing: number;
};
