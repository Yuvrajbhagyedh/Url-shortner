import { useEffect, useState } from "react";
import { api } from "../lib/api.js";

export default function ApiKeys() {
  const [keys, setKeys] = useState([]);
  const [name, setName] = useState("");
  const [quota, setQuota] = useState(10000);
  const [created, setCreated] = useState(null); // freshly created plaintext key
  const [error, setError] = useState("");

  const load = () => api.listKeys().then(setKeys);
  useEffect(() => {
    load();
  }, []);

  const create = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await api.createKey(name || "default", Number(quota));
      setCreated(res.api_key);
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const revoke = async (id) => {
    if (!confirm("Revoke this key? Apps using it will stop working.")) return;
    await api.revokeKey(id);
    load();
  };

  return (
    <>
      <h2>API keys</h2>
      <p className="muted">
        Use a key to shorten links programmatically:{" "}
        <code className="mono">
          POST {api.base}/api/v1/shorten
        </code>{" "}
        with header <code className="mono">X-API-Key</code>.
      </p>

      <form className="card create-form" onSubmit={create}>
        <div className="row">
          <div className="grow">
            <label>Key name</label>
            <input placeholder="production-server" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>Monthly quota (0 = unlimited)</label>
            <input type="number" min="0" value={quota} onChange={(e) => setQuota(e.target.value)} />
          </div>
          <button className="btn primary">Generate key</button>
        </div>
        {error && <div className="error">{error}</div>}
      </form>

      {created && (
        <div className="card key-reveal">
          <strong>Copy your new key now — it won't be shown again:</strong>
          <div className="reveal-row">
            <code className="mono">{created}</code>
            <button className="btn ghost sm" onClick={() => navigator.clipboard.writeText(created)}>
              copy
            </button>
          </div>
        </div>
      )}

      {keys.length === 0 ? (
        <div className="card empty muted">No API keys yet.</div>
      ) : (
        <div className="card table-card">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th className="num">Quota</th>
                <th>Last used</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.id}>
                  <td>{k.name}</td>
                  <td className="mono">{k.key_prefix}…</td>
                  <td className="num">{k.monthly_quota === 0 ? "∞" : k.monthly_quota}</td>
                  <td className="muted">
                    {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                  </td>
                  <td className="actions">
                    <button className="btn danger sm" onClick={() => revoke(k.id)}>
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
