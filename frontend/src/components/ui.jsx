import React from "react";

export function Card({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <header className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {subtitle && <p className="muted small">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function Stat({ label, value, unit, note, tone }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${tone || ""}`}>
        {value}
        {unit && <small>{unit}</small>}
      </span>
      {note && <span className="muted small">{note}</span>}
    </div>
  );
}

export function Loading({ label = "Loading" }) {
  return (
    <div className="state" role="status">
      <span className="spinner" aria-hidden="true" />
      {label}...
    </div>
  );
}

export function ErrorBox({ error, onRetry }) {
  return (
    <div className="state error" role="alert">
      <strong>Something went wrong.</strong>
      <span>{error?.message || "Unknown error."}</span>
      {onRetry && (
        <button className="btn ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function Empty({ title, children, action }) {
  return (
    <div className="state empty">
      <strong>{title}</strong>
      {children && <span className="muted">{children}</span>}
      {action}
    </div>
  );
}

export function Field({ label, hint, error, children }) {
  return (
    <label className={`field ${error ? "has-error" : ""}`}>
      <span className="field-label">{label}</span>
      {children}
      {hint && !error && <span className="muted small">{hint}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}

export function Notice({ tone = "info", children }) {
  return (
    <div className={`notice ${tone}`} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

export function PageHeader({ title, children }) {
  return (
    <div className="page-head">
      <h1>{title}</h1>
      {children && <p className="muted">{children}</p>}
    </div>
  );
}
