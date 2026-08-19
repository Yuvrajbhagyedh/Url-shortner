import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api.js";

function CreateForm({ onCreated }) {
  const [url, setUrl] = useState("");
  const [alias, setAlias] = useState("");
  const [expires, setExpires] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const payload = { original_url: url };
      if (alias.trim()) payload.custom_alias = alias.trim();
      if (expires) payload.expires_at = new Date(expires).toISOString();
      await api.createLink(payload);
      setUrl("");
      setAlias("");
      setExpires("");
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card create-form" onSubmit={submit}>
      <div className="row">
        <div className="grow">
          <label>Long URL</label>
          <input
            type="url"
            required
            placeholder="https://example.com/a/very/long/link"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
        <div>
          <label>Custom alias (optional)</label>
          <input placeholder="my-link" value={alias} onChange={(e) => setAlias(e.target.value)} />
        </div>
        <div>
          <label>Expires (optional)</label>
          <input type="datetime-local" value={expires} onChange={(e) => setExpires(e.target.value)} />
        </div>
        <button className="btn primary" disabled={busy}>
          {busy ? "…" : "Shorten"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

export default function Dashboard() {
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState("");

  const load = () => {
    setLoading(true);
    api
      .listLinks()
      .then(setLinks)
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const copy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(""), 1500);
  };

  const remove = async (code) => {
    if (!confirm(`Delete /${code}? This cannot be undone.`)) return;
    await api.deleteLink(code);
    load();
  };

  return (
    <>
      <h2>Your links</h2>
      <CreateForm onCreated={load} />

      {loading ? (
        <div className="muted center">Loading…</div>
      ) : links.length === 0 ? (
        <div className="card empty muted">No links yet — shorten your first URL above.</div>
      ) : (
        <div className="card table-card">
          <table>
            <thead>
              <tr>
                <th>Short link</th>
                <th>Destination</th>
                <th className="num">Clicks</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {links.map((l) => (
                <tr key={l.id}>
                  <td>
                    <a href={l.short_url} target="_blank" rel="noreferrer" className="mono">
                      {l.short_url.replace(/^https?:\/\//, "")}
                    </a>
                    <button className="link-btn" onClick={() => copy(l.short_url)}>
                      {copied === l.short_url ? "copied!" : "copy"}
                    </button>
                  </td>
                  <td className="truncate" title={l.original_url}>
                    {l.original_url}
                  </td>
                  <td className="num">{l.click_count}</td>
                  <td className="muted">{new Date(l.created_at).toLocaleDateString()}</td>
                  <td className="actions">
                    <Link className="btn ghost sm" to={`/analytics/${l.short_code}`}>
                      Analytics
                    </Link>
                    <a className="btn ghost sm" href={api.qrUrl(l.short_code)} target="_blank" rel="noreferrer">
                      QR
                    </a>
                    <button className="btn danger sm" onClick={() => remove(l.short_code)}>
                      Delete
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
