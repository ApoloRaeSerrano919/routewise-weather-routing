
import { Popup } from "react-leaflet";

import type { Checkpoint } from "../types/routing";
import { riskColors } from "../utils/weather";

type CheckpointPopupProps = {
  checkpoint: Checkpoint;
  hour: number;
};

export default function CheckpointPopup({
  checkpoint,
  hour,
}: CheckpointPopupProps) {
  const arrivalTime = new Date(checkpoint.eta).toLocaleString();
  const arrivalRisk = checkpoint.risk;
  const forecastRisk = checkpoint.forecast_risks?.[hour] ?? "Unavailable";

  return (
    <Popup>
      <strong>Checkpoint — Mile {checkpoint.mile}</strong>

      <p>
        <b>Estimated arrival:</b>
        <br />
        {arrivalTime}
      </p>

      <p>
        <b>Risk at truck arrival:</b>{" "}
        <span style={{ color: riskColors[arrivalRisk] }}>
          {arrivalRisk}
        </span>
      </p>

      <p>
        Wind: {checkpoint.wind_mph} mph
        <br />
        Rain: {checkpoint.rain_in_hr} in/hr
        <br />
        Snow: {checkpoint.snow_in_hr} in/hr
      </p>

      <hr />

      <p>
        <b>Forecast at +{hour} hours:</b>
        <br />
        {forecastRisk}
      </p>
    </Popup>
  );
}
