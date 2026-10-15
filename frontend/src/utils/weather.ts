
import type { RiskLevel } from "../types/routing";

export const riskColors: Record<RiskLevel, string> = {
  Low: "#2dc78b",
  Moderate: "#f0c75e",
  High: "#f18b42",
  Severe: "#ef5461",
  "No Travel": "#ab57db",
};

export const unavailableColor = "#64748b";

export function localDateTime(hoursAhead = 2): string {
  const now = new Date();
  const futureTime = new Date(
    now.getTime() + hoursAhead * 60 * 60 * 1000
  );

  const timezoneOffset = futureTime.getTimezoneOffset() * 60 * 1000;
  const localTime = new Date(futureTime.getTime() - timezoneOffset);

  return localTime.toISOString().slice(0, 16);
}
