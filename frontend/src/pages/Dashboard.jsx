import React from "react";
import { api } from "../api.js";
import { useAsync, fmt, inr } from "../hooks.js";
import { Card, Stat, Loading, ErrorBox, Empty, PageHeader } from "../components/ui.jsx";
import TrendChart from "../components/TrendChart.jsx";

function changeText(pct) {
  if (pct == null) return "No previous month to compare";
  const word = pct > 0 ? "higher" : pct < 0 ? "lower" : "unchanged";
  return pct === 0 ? "Unchanged from previous month" : `${Math.abs(pct)}% ${word} than previous month`;
}

export default function Dashboard({ user, version, go }) {
  const fp = useAsync(() => api.footprint(user.id), [user.id, version]);
  const recs = useAsync(() => api.recommendations(user.id), [user.id, version]);
  const ch = useAsync(() => api.challenges(user.id), [user.id, version]);
  const prog = useAsync(() => api.progress(user.id), [user.id, version]);
  const coach = useAsync(() => api.coach(), []);

  if (fp.loading && !fp.data) return <Loading label="Loading your dashboard" />;
  if (fp.error) return <ErrorBox error={fp.error} onRetry={fp.reload} />;
  const f = fp.data;
  const latest = f.latest;
  const done = ch.data ? ch.data.challenges.filter((c) => c.completed_today).length : 0;
  const total = ch.data ? ch.data.challenges.length : 0;

  return (
    <>
      <PageHeader title={`Welcome, ${user.name}`}>
        Your own entered data, turned into estimates. Nothing here is measured live.
      </PageHeader>

      {!f.has_data ? (
        <Card>
          <Empty
            title="No readings yet"
            action={<button className="btn" onClick={() => go("footprint")}>Add your first reading</button>}
          >
            Enter the units (kWh) from an electricity bill and your dashboard will fill in.
          </Empty>
        </Card>
      ) : (
        <div className="stats">
          <Stat label={`Consumption, ${latest.period}`} value={fmt(latest.kwh, 1)} unit=" kWh"
            note={f.per_person_kwh != null ? `${fmt(f.per_person_kwh, 1)} kWh per person` : null} />
          <Stat label="Estimated cost" value={inr(latest.cost)} note={`at Rs ${fmt(latest.tariff_per_kwh, 2)} per kWh`} />
          <Stat label="Estimated emissions" value={fmt(latest.emissions_kg, 1)} unit=" kg CO2e"
            note={`factor ${f.emission_factor} kg CO2e per kWh`} />
          <Stat label="Change vs previous month"
            value={f.change && f.change.kwh_pct != null ? `${f.change.kwh_pct > 0 ? "+" : ""}${f.change.kwh_pct}%` : "-"}
            tone={f.change && f.change.kwh_pct > 0 ? "up" : f.change && f.change.kwh_pct < 0 ? "down" : ""}
            note={f.change ? changeText(f.change.kwh_pct) : "Add another month to compare"} />
        </div>
      )}

      <div className="cols">
        <Card title="Consumption history" subtitle="Monthly kWh you entered"
          action={<button className="btn ghost" onClick={() => go("footprint")}>Details</button>}>
          {f.series.length ? <TrendChart series={f.series} metric="kwh" height={240} /> : (
            <Empty title="Nothing to chart yet">Saved readings appear here.</Empty>
          )}
          <p className="muted small">Estimates based on your entered data.</p>
        </Card>

        <Card title="Your progress" subtitle="Individual, not community totals"
          action={<button className="btn ghost" onClick={() => go("missions")}>Missions</button>}>
          {prog.loading && !prog.data ? <Loading /> : prog.error ? <ErrorBox error={prog.error} onRetry={prog.reload} /> : (
            <div className="mini-stats">
              <div><span className="big">{prog.data.total_points}</span><span className="muted small">points</span></div>
              <div><span className="big">{prog.data.current_streak}</span><span className="muted small">day streak</span></div>
              <div><span className="big">{done}/{total}</span><span className="muted small">missions today</span></div>
            </div>
          )}
        </Card>
      </div>

      <Card title="Suggestions for you" subtitle="Rule-based, from your saved readings and answers">
        {recs.loading && !recs.data ? <Loading /> : recs.error ? <ErrorBox error={recs.error} onRetry={recs.reload} /> : (
          <ul className="recs">
            {recs.data.recommendations.slice(0, 3).map((r) => (
              <li key={r.id}>
                <strong>{r.title}</strong>
                <span>{r.action}</span>
                <span className="why">Why you see this: {r.why}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="AI Energy Coach" subtitle="Optional">
        {coach.loading ? <Loading /> : coach.error ? <ErrorBox error={coach.error} onRetry={coach.reload} /> : (
          <p className="muted">{coach.data.message}</p>
        )}
      </Card>
    </>
  );
}
