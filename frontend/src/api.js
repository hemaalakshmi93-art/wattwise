// Thin wrapper over fetch. Every call goes to the Flask API; nothing is faked here.
const BASE = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(message, status, fields) {
    super(message);
    this.status = status;
    this.fields = fields || {};
  }
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Is the Flask backend running?", 0);
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON response */
  }
  if (!res.ok) {
    const err = data && data.error;
    throw new ApiError(err?.message || `Request failed (${res.status}).`, res.status, err?.fields);
  }
  return data;
}

export const api = {
  config: () => request("/config"),
  users: () => request("/users"),
  createUser: (body) => request("/users", { method: "POST", body }),
  footprint: (id) => request(`/users/${id}/footprint`),
  saveReading: (id, body) => request(`/users/${id}/readings`, { method: "POST", body }),
  deleteReading: (id, rid) => request(`/users/${id}/readings/${rid}`, { method: "DELETE" }),
  challenges: (id) => request(`/users/${id}/challenges`),
  complete: (id, cid) => request(`/users/${id}/challenges/${cid}/complete`, { method: "POST" }),
  progress: (id) => request(`/users/${id}/progress`),
  recommendations: (id) => request(`/users/${id}/recommendations`),
  leaderboard: () => request("/leaderboard"),
  community: () => request("/community"),
  solar: (body) => request("/solar/estimate", { method: "POST", body }),
  resources: (q = "", category = "") =>
    request(`/resources?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`),
  coach: () => request("/coach/status"),
};
