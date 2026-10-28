import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAsync, fmt, inr } from "../hooks.js";
import { Card, Stat, Field, Notice, Loading, PageHeader } from "../components/ui.jsx";

const ASSUMPTION_LABELS = {
  peak_sun_hours: ["Peak sun hours per day", "Equivalent full-sun hours. Edit to match your own source."],
  performance_ratio: ["Performance ratio", "Share of ideal output after real-world losses (0.5 to 0.95)."],
  area_per_kw: ["Roof area per kW (m2)", "Usable roof needed for 1 kW of panels."],
  cost_per_kw: ["Installed cost per kW (Rs)", "A placeholder. Replace with real quotes."],
};

export default function Solar({ user, version }) {
  const cfg = useAsync(() => api.config(), []);
  const fp = useAsync(() => api.footprint(user.id), [user.id, version]);
  const links = useAsync(() => api.resources("", "Rooftop solar"), []);
  const [form, setForm] = useState({ monthly_kwh: "", roof_area_m2: "", monthly_bill: "", location: "" });
  const [assump, setAssump] = useState(null);
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState({});
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (cfg.data && !assump) setAssump({ ...cfg.data.solar_defaults });
  }, [cfg.data, assump]);

  // Pre-fill from the latest saved reading, only while the fields are still blank.
  useEffect(() => {
    const l = fp.data && fp.data.latest;
    if (l) {
      setForm((f) => ({
        ...f,
        monthly_kwh: f.monthly_kwh === "" ? String(l.kwh) : f.monthly_kwh,
        monthly_bill: f.monthly_bill === "" ? String(l.cost) : f.monthly_bill,
        location: f.location === "" && user.city ? user.city : f.location,
      }));
    }
  }, [fp.data, user.city]);

  const setF = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setA = (k) => (e) => setAssump({ ...assump, [k]: e.target.value });

  async function calculate(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setMsg(null);
    try {
      const body = { ...form, ...assump };
      if (!body.location) delete body.location;
      setResult(await api.solar(body));
    } catch (err) {
      setErrors(err.fields);
      setMsg(err.message);
      setResult(null);
    } finally {
      setBusy(false);
    }
  }

  if (cfg.loading && !cfg.data) return <Loading />;

  return (
    <>
      <PageHeader title="Solar Advisor">
        A rough, adjustable estimate to help you decide whether rooftop solar is worth looking into.
      </PageHeader>

      <form onSubmit={calculate} noValidate>
        <Card title="Your inputs">
          <div className="grid-2">
            <Field label="Monthly consumption (kWh)" error={errors.monthly_kwh}
              hint={fp.data && fp.data.latest ? "Pre-filled from your latest saved reading." : undefined}>
              <input type="number" min="0" step="any" value={form.monthly_kwh} onChange={setF("monthly_kwh")} required />
            </Field>
            <Field label="Monthly electricity bill (Rs)" error={errors.monthly_bill}>
              <input type="number" min="0" step="any" value={form.monthly_bill} onChange={setF("monthly_bill")} required />
            </Field>
            <Field label="Available rooftop area (m2)" error={errors.roof_area_m2}>
              <input type="number" min="0" step="any" value={form.roof_area_m2} onChange={setF("roof_area_m2")} required />
            </Field>
            <Field label="Location (optional)" error={errors.location}
              hint="Only displayed. Sunlight is controlled by the assumptions below.">
              <input value={form.location} maxLength={80} onChange={setF("location")} />
            </Field>
          </div>
        </Card>

        {assump && (
          <Card title="Assumptions you can change"
            action={<button type="button" className="btn ghost"
              onClick={() => setAssump({ ...cfg.data.solar_defaults })}>Reset to defaults</button>}>
            <div className="grid-2">
              {Object.entries(ASSUMPTION_LABELS).map(([k, [label, hint]]) => (
                <Field key={k} label={label} hint={hint} error={errors[k]}>
                  <input type="number" step="any" value={assump[k]} onChange={setA(k)} />
                </Field>
              ))}
            </div>
          </Card>
        )}

        {msg && <Notice tone="error">{msg}</Notice>}
        <div className="row-end">
          <button className="btn" disabled={busy}>{busy ? "Calculating..." : result ? "Recalculate" : "Calculate estimate"}</button>
        </div>
      </form>

      {result && (
        <>
          <Notice tone="info">{result.label}</Notice>
          <div className="stats">
            <Stat label="Suggested system size" value={fmt(result.recommended_size_kw, 2)} unit=" kW"
              note={`Limited by ${result.limited_by}`} />
            <Stat label="Estimated generation" value={fmt(result.monthly_generation_kwh, 0)} unit=" kWh/month"
              note={`Covers about ${result.bill_offset_percent}% of your usage`} />
            <Stat label="Indicative payback"
              value={result.payback_years == null ? "-" : fmt(result.payback_years, 1)} unit=" years"
              note={`Cost placeholder ${inr(result.estimated_system_cost_inr)}`} />
            <Stat label="Estimated saving" value={inr(result.monthly_savings_inr)} unit="/month"
              note={`CO2 avoided: ${fmt(result.co2_avoided_kg_per_year)} kg/year`} />
          </div>
          {result.location && <p className="muted small">Location entered: {result.location}. {result.location_note}</p>}
          <Card title="Formulas and assumptions used">
            <ul className="plain">{result.formulas.map((t) => <li key={t}>{t}</li>)}</ul>
            <p className="small">
              Yield per kW: {result.yield_kwh_per_kw_month} kWh per month. Size needed for full offset:{" "}
              {result.needed_size_for_full_offset_kw} kW. Roof limit: {result.roof_limit_kw} kW.
              Effective tariff: Rs {result.effective_tariff_per_kwh} per kWh. Emission factor: {result.emission_factor} kg CO2e per kWh.
            </p>
            <ul className="plain muted">{result.notes.map((t) => <li key={t}>{t}</li>)}</ul>
          </Card>
        </>
      )}

      <Card title="Next steps for exploring rooftop solar"
        subtitle="WattWise does not verify subsidies, rooftop suitability, weather or vendors.">
        <ol className="plain">
          <li>Check current eligibility, subsidy terms and the application process on the official portals below.</li>
          <li>Ask a qualified installer for a site survey and a written quotation.</li>
          <li>Compare that quotation with this estimate and with your own bills.</li>
        </ol>
        {links.loading ? <Loading /> : links.data && (
          <ul className="links">
            {links.data.resources.filter((r) => r.url).map((r) => (
              <li key={r.id}><a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}</a>
                <span className="muted small"> {r.summary}</span></li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
