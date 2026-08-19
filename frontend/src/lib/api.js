// Thin fetch wrapper around the ShortX API with JWT handling.
// Empty string = same origin (Docker / Render single service).
const API_BASE =
  import.meta.env.VITE_API_BASE !== undefined
    ? import.meta.env.VITE_API_BASE
    : "http://localhost:8000";

const TOKEN_KEY = "shortx_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  const opts = { method, headers };

  if (form) {
    // OAuth2 login expects x-www-form-urlencoded.
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    opts.body = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  if (auth) {
    const token = tokenStore.get();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, opts);
  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 404 || res.status === 502 || res.status === 503) {
      throw new Error("Server is waking up or restarting. Wait 30 seconds and try again.");
    }
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : detail
          ? JSON.stringify(detail)
          : `Request failed (${res.status})`
    );
  }
  return data;
}

export const api = {
  base: API_BASE,
  register: (email, password) =>
    request("/api/auth/register", { method: "POST", body: { email, password }, auth: false }),
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", form: { username: email, password }, auth: false }),
  me: () => request("/api/auth/me"),

  listLinks: () => request("/api/links"),
  createLink: (payload) => request("/api/links", { method: "POST", body: payload }),
  deleteLink: (code) => request(`/api/links/${code}`, { method: "DELETE" }),
  qrUrl: (code) => `${API_BASE}/api/links/${code}/qr`,

  analytics: (code, days = 30) => request(`/api/analytics/${code}?days=${days}`),

  listKeys: () => request("/api/keys"),
  createKey: (name, monthly_quota) =>
    request("/api/keys", { method: "POST", body: { name, monthly_quota } }),
  revokeKey: (id) => request(`/api/keys/${id}`, { method: "DELETE" }),
};
