
import type { Route } from "../types/routing";
import { riskColors, unavailableColor } from "../utils/weather";

type Props = {
  route: Route | undefined;
  hour: number;
  onHourChange: (hour: number) => void;
  heatVisible: boolean;
  onHeatVisibleChange: (visible: boolean) => void;
};

const QUICK_HOURS = [0, 12, 24, 48] as const;

function formatMile(mile: number): string {
  return Number.isInteger(mile)
    ? String(mile)
    : mile.toFixed(1);
}

export default function WeatherTimeline({
  route,
  hour,
  onHourChange,
  heatVisible,
  onHeatVisibleChange,
}: Props) {
  const checkpoints = route?.checkpoints ?? [];

  return (
    <section
      className="heatPanel"
      aria-labelledby="weather-corridor-heading"
    >
      <div className="heatHeading">
        <div>
          <h2 id="weather-corridor-heading">
            Weather risk corridor
          </h2>
          <p>
            Explore forecast risk at fixed locations
            along the selected route.
          </p>
        </div>

        <strong className="forecastHour">
          +{hour}h
        </strong>
      </div>

      {/* Quick forecast selection */}
      <div
        className="quickHours"
        role="group"
        aria-label="Quick forecast hour selection"
      >
        {QUICK_HOURS.map((quickHour) => (
          <button
            key={quickHour}
            type="button"
            className={
              hour === quickHour ? "current" : ""
            }
            aria-pressed={hour === quickHour}
            onClick={() => onHourChange(quickHour)}
          >
            +{quickHour}h
          </button>
        ))}
      </div>

      {/* Forecast time slider */}
      <div className="forecastSlider">
        <input
          id="weather-hour"
          type="range"
          min={0}
          max={48}
          step={1}
          value={hour}
          onChange={(event) =>
            onHourChange(Number(event.target.value))
          }
          aria-label="Forecast hour"
          aria-valuetext={`${hour} hours after departure`}
        />

        <div className="timeline" aria-hidden="true">
          <span>DEPARTURE</span>
          <span>+24 HOURS</span>
          <span>+48 HOURS</span>
        </div>
      </div>

      {/* Geographic overlay toggle */}
      <label className="heatToggle">
        <input
          type="checkbox"
          checked={heatVisible}
          onChange={(event) =>
            onHeatVisibleChange(event.target.checked)
          }
        />
        <span>
          Show weather-risk overlay on map
        </span>
      </label>

      {/* Checkpoint risk visualization */}
      {route && checkpoints.length > 0 ? (
        <div className="checkpointSection">
          <div className="checkpointHeader">
            <span>
              <strong>{checkpoints.length}</strong>{" "}
              forecast checkpoints
            </span>
            <span>
              Forecast +{hour}h
            </span>
          </div>

          <div
            className="checkpointScroll"
            role="region"
            aria-label="Weather risk checkpoints"
            tabIndex={0}
          >
            <div
              className="heatStrip"
              role="list"
              aria-label="Weather risk along the route"
            >
              {checkpoints.map((checkpoint, index) => {
                const selectedRisk =
                  checkpoint.forecast_risks?.[hour] ?? null;

                const riskLabel =
                  selectedRisk ?? "Unavailable";

                const color = selectedRisk
                  ? riskColors[selectedRisk] ??
                    unavailableColor
                  : unavailableColor;

                const mileLabel = formatMile(
                  checkpoint.mile
                );

                const description =
                  `Checkpoint ${index + 1}. ` +
                  `Mile ${mileLabel}. ` +
                  `Risk ${riskLabel}. ` +
                  `Forecast ${hour} hours after departure.`;

                return (
                  <div
                    key={`${index}-${checkpoint.mile}`}
                    className="heatCheckpoint"
                    role="listitem"
                    tabIndex={0}
                    aria-label={description}
                    title={description}
                  >
                    <div
                      className="heatCheckpointColor"
                      style={{
                        backgroundColor: color,
                        opacity: selectedRisk ? 1 : 0.45,
                      }}
                      aria-hidden="true"
                    />

                    <span className="heatCheckpointMile">
                      {mileLabel}
                      <span className="mileUnit"> mi</span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="checkpointHelp">
            Each colored block represents one forecast
            checkpoint. Hover or focus on a block to
            inspect its risk and mileage.
          </p>
        </div>
      ) : (
        <p className="hint emptyCheckpoints">
          Analyze a route to display checkpoint weather
          risks.
        </p>
      )}

      {/* Risk classification legend */}
      <div
        className="legend"
        aria-label="Weather risk legend"
      >
        {Object.entries(riskColors).map(
          ([riskName, color]) => (
            <span key={riskName}>
              <i
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              {riskName}
            </span>
          )
        )}

        <span>
          <i
            style={{
              backgroundColor: unavailableColor,
            }}
            aria-hidden="true"
          />
          Unavailable
        </span>
      </div>

      {/* Explanation */}
      <p className="notice">
        The timeline shows forecast risk at fixed
        checkpoint locations, measured from the selected
        departure time. Route recommendations instead use
        weather expected when the truck reaches each
        checkpoint. The map overlay represents sampled
        weather regions, not a continuous meteorological
        grid.
      </p>
    </section>
  );
}
