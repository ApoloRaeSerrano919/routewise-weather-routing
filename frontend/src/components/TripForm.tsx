
import type { FormEvent } from "react";
import LocationAutocomplete from "./LocationAutocomplete";

export type TripValues = {
  origin: string;
  destination: string;
  departure: string;
  load: number;
  spacing: number;
};

type Props = TripValues & {
  loading: boolean;
  onChange: (patch: Partial<TripValues>) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
};

// Suggested locations for faster trip planning.
// Users can still enter any location manually.
const locations = [
  "Atlanta, GA",
  "Baltimore, MD",
  "Boston, MA",
  "Buffalo, NY",
  "Charlotte, NC",
  "Chicago, IL",
  "Cincinnati, OH",
  "Cleveland, OH",
  "Columbus, OH",
  "Dallas, TX",
  "Denver, CO",
  "Detroit, MI",
  "Harrisburg, PA",
  "Houston, TX",
  "Indianapolis, IN",
  "Jacksonville, FL",
  "Kansas City, MO",
  "Las Vegas, NV",
  "Los Angeles, CA",
  "Louisville, KY",
  "Memphis, TN",
  "Miami, FL",
  "Milwaukee, WI",
  "Minneapolis, MN",
  "Nashville, TN",
  "New Haven, CT",
  "New Orleans, LA",
  "New York, NY",
  "Newark, NJ",
  "Orlando, FL",
  "Philadelphia, PA",
  "Phoenix, AZ",
  "Pittsburgh, PA",
  "Portland, OR",
  "Richmond, VA",
  "Sacramento, CA",
  "Salt Lake City, UT",
  "San Antonio, TX",
  "San Diego, CA",
  "San Francisco, CA",
  "Seattle, WA",
  "St. Louis, MO",
  "Tampa, FL",
  "Washington, DC",
];

export default function TripForm({
  origin,
  destination,
  departure,
  load,
  spacing,
  loading,
  onChange,
  onSubmit,
}: Props) {
  return (
    <>
      <div className="sectionHeading">
        <h2>Plan a trip</h2>
        <span className="sectionHint">Trip details</span>
      </div>

      <form onSubmit={onSubmit} aria-busy={loading}>
        <div className="locationFields">
          <label htmlFor="trip-origin">
            <LocationAutocomplete
              id="trip-origin"
              label="ORIGIN"
              value={origin}
              onChange={(value) => onChange({ origin: value })}
              disabled={loading}
            />
          </label>

          <button
            className="swapButton"
            type="button"
            onClick={() =>
              onChange({
                origin: destination,
                destination: origin,
              })
            }
            aria-label="Swap origin and destination"
            title="Swap origin and destination"
          >
            ⇅ <span>Swap locations</span>
          </button>

          <label htmlFor="trip-destination">
            <LocationAutocomplete
              id="trip-destination"
              label="DESTINATION"
              value={destination}
              onChange={(value) => onChange({ destination: value })}
              disabled={loading}
            />
          </label>

          <datalist id="routewise-locations">
            {locations.map((location) => (
              <option
                key={location}
                value={location}
              />
            ))}
          </datalist>
        </div>

        <label htmlFor="trip-departure">
          DEPARTURE (YOUR LOCAL TIME)

          <input
            id="trip-departure"
            type="datetime-local"
            value={departure}
            onChange={(e) =>
              onChange({
                departure: e.target.value,
              })
            }
            required
          />
        </label>

        <label htmlFor="trip-load">
          LOAD WEIGHT (LB)

          <input
            id="trip-load"
            type="number"
            min="0"
            max="200000"
            value={load}
            onChange={(e) =>
              onChange({
                load: Number(e.target.value),
              })
            }
            required
          />

          <span className="fieldHelp">
            Cargo weight affects wind-risk classification.
          </span>
        </label>

        <label htmlFor="trip-spacing">
          WEATHER CHECKPOINT INTERVAL

          <select
            id="trip-spacing"
            value={spacing}
            onChange={(e) =>
              onChange({
                spacing: Number(e.target.value),
              })
            }
          >
            <option value={10}>Every 10 miles</option>
            <option value={25}>Every 25 miles</option>
            <option value={50}>Every 50 miles</option>
          </select>

          <span className="fieldHelp">
            Shorter intervals give more detail but may take
            longer.
          </span>
        </label>

        <button
          className="analyzeButton"
          type="submit"
          disabled={loading}
        >
          {loading
            ? "Analyzing forecasts…"
            : "Analyze routes →"}
        </button>

        {loading && (
          <p className="loadingHint" role="status">
            Getting route alternatives and checking weather
            at each checkpoint. Previous results remain
            visible until this finishes.
          </p>
        )}
      </form>
    </>
  );
}
