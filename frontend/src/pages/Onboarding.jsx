import React, { useState } from "react";
import { api } from "../api.js";
import { Card, Field, Notice } from "../components/ui.jsx";
import ConsumptionFields, { emptyConsumption, consumptionPayload } from "../components/ConsumptionFields.jsx";

export default function Onboarding({ onCreated, onCancel }) {
  const [p, setP] = useState({
    name: "", household_size: "", tariff_per_kwh: "", city: "", has_ac: false, ac_hours_per_day: "",
  });
  const [c, setC] = useState(emptyConsumption());
  const [addReading, setAddReading] = useState(true);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState(null);
  const [saving, setSaving] = useState(false);

  const set = (k) => (e) => setP({ ...p, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setMessage(null);
    const body = { ...p };
    if (!p.has_ac) delete body.ac_hours_per_day;
    if (addReading) body.initial_reading = consumptionPayload(c);
    try {
      const { user } = await api.createUser(body);
      onCreated(user);
    } catch (err) {
      setErrors(err.fields);
      setMessage(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="onboard">
      <div className="page-head">
        <h1>Set up your household</h1>
        <p className="muted">
          A few details so WattWise can calculate your numbers. You enter everything yourself;
          WattWise does not read your meter.
        </p>
      </div>
      <form onSubmit={submit} noValidate>
        <Card title="Household">
          <div className="grid-2">
            <Field label="Name for this profile" error={errors.name}>
              <input value={p.name} onChange={set("name")} maxLength={60} placeholder="e.g. Hema's home" required />
            </Field>
            <Field label="City (optional)" error={errors.city}>
              <input value={p.city} onChange={set("city")} maxLength={80} />
            </Field>
            <Field label="People in household" error={errors.household_size}>
              <input type="number" min="1" max="50" step="1" value={p.household_size}
                onChange={set("household_size")} required />
            </Field>
            <Field label="Electricity tariff (Rs per kWh)" error={errors.tariff_per_kwh}
              hint="Check your bill. Used to estimate cost.">
              <input type="number" min="0" step="any" value={p.tariff_per_kwh}
                onChange={set("tariff_per_kwh")} required />
            </Field>
          </div>
          <label className="check">
            <input type="checkbox" checked={p.has_ac} onChange={(e) => setP({ ...p, has_ac: e.target.checked })} />
            We use an air conditioner
          </label>
          {p.has_ac && (
            <Field label="Typical AC hours per day" error={errors.ac_hours_per_day}
              hint="Used only to personalise suggestions.">
              <input type="number" min="0" max="24" step="any" value={p.ac_hours_per_day}
                onChange={set("ac_hours_per_day")} />
            </Field>
          )}
        </Card>

        <Card title="Electricity consumption" subtitle="Optional now. You can add readings later on My Footprint.">
          <label className="check">
            <input type="checkbox" checked={addReading} onChange={(e) => setAddReading(e.target.checked)} />
            Add one monthly reading now
          </label>
          {addReading && (
            <ConsumptionFields value={c} onChange={setC} errors={errors} prefix="initial_reading." />
          )}
        </Card>

        {message && <Notice tone="error">{message}</Notice>}
        <div className="row-end">
          {onCancel && (
            <button type="button" className="btn ghost" onClick={onCancel}>Cancel</button>
          )}
          <button className="btn" disabled={saving}>{saving ? "Saving..." : "Create profile"}</button>
        </div>
      </form>
    </div>
  );
}
