import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { Card, Loading, ErrorBox, Empty, PageHeader } from "../components/ui.jsx";

export default function Resources() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    const timer = setTimeout(() => {
      api.resources(q, category)
        .then((data) => {
          if (cancelled) return;
          setState({ data, loading: false, error: null });
          if (!categories.length) setCategories(data.categories);
        })
        .catch((error) => !cancelled && setState({ data: null, loading: false, error }));
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, category, tick]);

  return (
    <>
      <PageHeader title="Resource Hub">
        Practical guidance and official starting points. Links go to external sites; check them directly for current details.
      </PageHeader>

      <Card>
        <div className="filters wide">
          <input type="search" placeholder="Search resources" aria-label="Search resources"
            value={q} onChange={(e) => setQ(e.target.value)} />
          <select aria-label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
      </Card>

      {state.loading && !state.data ? <Loading label="Loading resources" /> : state.error ? (
        <ErrorBox error={state.error} onRetry={() => setTick((t) => t + 1)} />
      ) : state.data.resources.length === 0 ? (
        <Card><Empty title="No resources match">Try a different word or choose All categories.</Empty></Card>
      ) : (
        <div className="res-grid">
          {state.data.resources.map((r) => (
            <article key={r.id} className="card res">
              <span className="tag">{r.category}</span>
              <h3>{r.title}</h3>
              <p>{r.summary}</p>
              {r.url ? (
                <a href={r.url} target="_blank" rel="noopener noreferrer">Open official source</a>
              ) : (
                <span className="muted small">General guidance. No external link.</span>
              )}
            </article>
          ))}
        </div>
      )}
    </>
  );
}
