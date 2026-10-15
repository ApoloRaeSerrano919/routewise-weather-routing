
import type { Result, TripRequest } from "../types/routing";

export async function planRoutes(
  payload: TripRequest
): Promise<Result> {
  const response = await fetch("/api/plan/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  let data: unknown;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `Server returned an invalid response (${response.status}).`
    );
  }

  if (!response.ok) {
    let message = `Route analysis failed (${response.status}).`;

    if (
      typeof data === "object" &&
      data !== null &&
      "error" in data
    ) {
      message = String(data.error);
    }

    throw new Error(message);
  }

  if (
    typeof data !== "object" ||
    data === null ||
    !("routes" in data) ||
    !Array.isArray(data.routes) ||
    data.routes.length === 0
  ) {
    throw new Error("No routes were returned.");
  }

  return data as Result;
}
