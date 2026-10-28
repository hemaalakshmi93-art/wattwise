import React from "react";
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";

export const METRICS = {
  kwh: { label: "Consumption (kWh)", key: "kwh", unit: "kWh", type: "bar" },
  cost: { label: "Estimated cost (Rs)", key: "cost", unit: "Rs", type: "bar" },
  emissions_kg: { label: "Estimated emissions (kg CO2e)", key: "emissions_kg", unit: "kg CO2e", type: "line" },
};

export default function TrendChart({ series, metric = "kwh", height = 260 }) {
  const m = METRICS[metric];
  const common = { data: series, margin: { top: 8, right: 8, bottom: 0, left: -8 } };
  const axes = (
    <>
      <CartesianGrid stroke="#e3e8e1" strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="period" tick={{ fontSize: 12, fill: "#51604f" }} tickLine={false} axisLine={{ stroke: "#d4dbd1" }} />
      <YAxis tick={{ fontSize: 12, fill: "#51604f" }} tickLine={false} axisLine={false} width={56} />
      <Tooltip
        cursor={{ fill: "rgba(31,95,63,0.06)" }}
        formatter={(v) => [`${Number(v).toLocaleString("en-IN")} ${m.unit}`, m.label]}
        contentStyle={{ borderRadius: 10, border: "1px solid #d4dbd1", fontSize: 13 }}
      />
    </>
  );
  return (
    <div role="img" aria-label={`${m.label} by month`}>
      <ResponsiveContainer width="100%" height={height}>
        {m.type === "bar" ? (
          <BarChart {...common}>
            {axes}
            <Bar dataKey={m.key} fill="#1f5f3f" radius={[6, 6, 0, 0]} maxBarSize={44} />
          </BarChart>
        ) : (
          <LineChart {...common}>
            {axes}
            <Line type="monotone" dataKey={m.key} stroke="#1f5f3f" strokeWidth={2.5} dot={{ r: 3.5, fill: "#1f5f3f" }} />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
