import React, { useState } from "react";
import { api } from "../api.js";
import { useAsync, fmt, inr } from "../hooks.js";
import { Card, Stat, Loading, ErrorBox, Empty, Notice, PageHeader } from "../components/ui.jsx";
import TrendChart, { METRICS } from "../components/TrendChart.jsx";
import ConsumptionFields, { emptyConsumption, consumptionPayload } from "../components/ConsumptionFields.jsx";

const RANGES = [
  { id: "6", label: "Last 6 months", n: 6 },
  { id: "12", label: "Last 12 months", n: 12 },
  { id: "all", label: "All", n: Infinity },
];

export default function Footprint({ user, version, refresh }) {
  const fp = useAsync(() => api.footprint(user.id), [user.id, version]);
  const [form, setForm] = useState(emptyConsumption());
  const [errors, setErrors] = useState({});
  const [msg, setMsg] = useState(null);
  const [saving, setSaving] = useState(false);
  const [metric, setMetric] = useState("kwh");
  const [range, setRange] = useState("12");

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setMsg(null);
    try {
      const res = await api.saveReading(user.id, consumptionPayload(form, { includeTariff: true }));
      setMsg({ tone: "success", text: res.created ? "Reading saved." : "Reading for that month updated." });
      setForm({ ...emptyConsumption(), period: form.period });
      refresh();
    } catch (err) {
      setErrors(err.fields);
      setMsg({ tone: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  }

  async function remove(r) {
    if (!window.confirm(`Delete the reading for ${r.period}?`)) return;
    try {
      await api.deleteReading(user.id, r.id);
      setMsg({ tone: "success", text: `Reading for ${r.period} deleted.` });
      refresh();
    } catch (err) {
      setMsg({ tone: "error", text: err.message });
    }
  }

  const f = fp.data;
  const n = RANGES.find((r) => r.id === range).n;
  const series = f ? f.series.slice(-n) : [];

  return (
    <>
      <PageHeader title="My Footprint">
        Enter your own monthly figures. Cost and emissions are estimates calculated from them.
      </PageHeader>

      <Card title="Add or update a monthly reading" subtitle="Saving a month that already exists updates it.">
        <form onSubmit={save} noValidate>
          <ConsumptionFields value={form} onChange={setForm} errors={errors} showTariff />
          {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
          <div className="row-end">
            <button className="btn" disabled={saving}>{saving ? "Saving..." : "Save reading"}</button>
          </div>
        </form>
      </Card>

      {fp.loading && !f ? <Loading label="Loading footprint" /> : fp.error ? (
        <ErrorBox error={fp.error} onRetry={fp.reload} />
      ) : !f.has_data ? (
        <Card><Empty title="No readings yet">Save a reading above to see your footprint and trends.</Empty></Card>
      ) : (
        <>
          <div className="stats">
            <Stat label={`Consumption, ${f.latest.period}`} value={fmt(f.latest.kwh, 1)} unit=" kWh"
              note={f.change ? `${f.change.kwh_abs >= 0 ? "+" : ""}${fmt(f.change.kwh_abs, 1)} kWh vs ${f.previous.period}` : "No previous period"} />
            <Stat label="Estimated cost" value={inr(f.latest.cost)}
              note={f.change ? `${f.change.cost_abs >= 0 ? "+" : ""}${inr(f.change.cost_abs)} vs previous` : "No previous period"} />
            <Stat label="Estimated emissions" value={fmt(f.latest.emissions_kg, 1)} unit=" kg CO2e"
              note={f.change && f.change.emissions_pct != null ? `${f.change.emissions_pct > 0 ? "+" : ""}${f.change.emissions_pct}% vs previous` : "No previous period"} />
            {f.latest.transport_emissions_kg != null && (
              <Stat label="Transport estimate" value={fmt(f.latest.transport_emissions_kg, 1)} unit=" kg CO2e"
                note={`${fmt(f.latest.transport_km)} km at ${f.transport_factor} kg CO2e per km`} />
            )}
          </div>

          <Card title="History"
            action={
              <div className="filters">
                <select aria-label="Metric" value={metric} onChange={(e) => setMetric(e.target.value)}>
                  {Object.entries(METRICS).map(([k, m]) => <option key={k} value={k}>{m.label}</option>)}
                </select>
                <select aria-label="Time range" value={range} onChange={(e) => setRange(e.target.value)}>
                  {RANGES.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
                </select>
              </div>
            }>
            <TrendChart series={series} metric={metric} />
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Month</th><th className="num">kWh</th><th className="num">Cost</th>
                    <th className="num">kg CO2e</th><th>Entered as</th><th /></tr>
                </thead>
                <tbody>
                  {[...f.series].reverse().map((r) => (
                    <tr key={r.id}>
                      <td>{r.period}</td>
                      <td className="num">{fmt(r.kwh, 1)}</td>
                      <td className="num">{inr(r.cost)}</td>
                      <td className="num">{fmt(r.emissions_kg, 1)}</td>
                      <td>{r.source === "meter" ? "Meter readings" : "Units"}</td>
                      <td className="num"><button className="btn link" onClick={() => remove(r)}>Delete</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="How these estimates are calculated">
            <ul className="plain">
              {f.formulas.map((t) => <li key={t}>{t}</li>)}
            </ul>
            <p><strong>Emission factor used:</strong> {f.emission_factor} {f.emission_factor_unit}.
              Transport factor: {f.transport_factor} kg CO2e per km (assumed average petrol car).
              Both are configurable on the server. Check the latest official grid factor before relying on the results.</p>
            <p className="muted small">{f.disclaimer}</p>
          </Card>
        </>
      )}
    </>
  );
}
