import React from "react";
import { Field } from "./ui.jsx";
import { previousMonth } from "../hooks.js";

export const emptyConsumption = () => ({
  period: previousMonth(),
  mode: "kwh",
  kwh: "",
  meter_start: "",
  meter_end: "",
  tariff_per_kwh: "",
  transport_km: "",
});

// Converts the form state into the JSON body the API expects (blank fields are omitted).
export function consumptionPayload(v, { includeTariff = false } = {}) {
  const body = { period: v.period };
  if (v.mode === "kwh") body.kwh = v.kwh;
  else {
    body.meter_start = v.meter_start;
    body.meter_end = v.meter_end;
  }
  if (includeTariff && v.tariff_per_kwh !== "") body.tariff_per_kwh = v.tariff_per_kwh;
  if (v.transport_km !== "") body.transport_km = v.transport_km;
  return body;
}

export default function ConsumptionFields({ value, onChange, errors = {}, prefix = "", showTariff = false }) {
  const set = (k) => (e) => onChange({ ...value, [k]: e.target.value });
  const err = (k) => errors[prefix + k];
  return (
    <>
      <div className="seg" role="tablist" aria-label="How do you want to enter consumption?">
        <button type="button" role="tab" aria-selected={value.mode === "kwh"}
          className={value.mode === "kwh" ? "on" : ""} onClick={() => onChange({ ...value, mode: "kwh" })}>
          Units from bill (kWh)
        </button>
        <button type="button" role="tab" aria-selected={value.mode === "meter"}
          className={value.mode === "meter" ? "on" : ""} onClick={() => onChange({ ...value, mode: "meter" })}>
          Two meter readings
        </button>
      </div>

      <div className="grid-2">
        <Field label="Month" error={err("period")} hint="The month these units belong to.">
          <input type="month" value={value.period} onChange={set("period")} required />
        </Field>
        {value.mode === "kwh" ? (
          <Field label="Electricity used (kWh)" error={err("kwh")} hint="Units consumed in that month.">
            <input type="number" min="0" step="any" inputMode="decimal" value={value.kwh}
              onChange={set("kwh")} placeholder="e.g. 220" required />
          </Field>
        ) : (
          <>
            <Field label="Meter reading at start" error={err("meter_start")}>
              <input type="number" min="0" step="any" value={value.meter_start} onChange={set("meter_start")} required />
            </Field>
            <Field label="Meter reading at end" error={err("meter_end")} hint="kWh used = end minus start.">
              <input type="number" min="0" step="any" value={value.meter_end} onChange={set("meter_end")} required />
            </Field>
          </>
        )}
        {showTariff && (
          <Field label="Tariff for this month (Rs per kWh)" error={err("tariff_per_kwh")}
            hint="Leave blank to use your profile tariff.">
            <input type="number" min="0" step="any" value={value.tariff_per_kwh} onChange={set("tariff_per_kwh")} />
          </Field>
        )}
        <Field label="Distance driven (km, optional)" error={err("transport_km")}
          hint="Adds a separate transport estimate using the factor shown on My Footprint.">
          <input type="number" min="0" step="any" value={value.transport_km} onChange={set("transport_km")} />
        </Field>
      </div>
    </>
  );
}
