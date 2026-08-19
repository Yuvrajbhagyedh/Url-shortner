import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api.js";
import { AreaChart, BarBreakdown } from "../components/Charts.jsx";

function Stat({ label, value }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function LinkAnalytics() {
  const { code } = useParams();
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setData(null);
    api
      .analytics(code, days)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [code, days]);

  if (error) return <div className="error">{error}</div>;
  if (!data) return <div className="muted center">Loading analytics…</div>;

  return (
    <>
      <div className="page-head">
        <div>
          <Link to="/" className="muted small">
            ← Back to links
          </Link>
          <h2 className="mono">/{data.short_code}</h2>
        </div>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div className="stats">
        <Stat label="Total clicks" value={data.total_clicks} />
        <Stat label="Unique visitors" value={data.unique_visitors} />
        <Stat
          label="Avg clicks / day"
          value={(data.total_clicks / Math.max(1, days)).toFixed(1)}
        />
      </div>

      <div className="card">
        <h3>Clicks over time</h3>
        <AreaChart data={data.timeseries} />
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>By country</h3>
          <BarBreakdown items={data.by_country} />
        </div>
        <div className="card">
          <h3>By device</h3>
          <BarBreakdown items={data.by_device} />
        </div>
        <div className="card">
          <h3>By browser</h3>
          <BarBreakdown items={data.by_browser} />
        </div>
        <div className="card">
          <h3>Top referrers</h3>
          <BarBreakdown items={data.by_referrer} />
        </div>
      </div>
    </>
  );
}
