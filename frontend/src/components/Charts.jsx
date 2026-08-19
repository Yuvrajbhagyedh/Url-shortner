// Dependency-free inline-SVG charts (no chart library needed).

export function AreaChart({ data, height = 180 }) {
  // data: [{ date, clicks }]
  const width = 640;
  const pad = 24;
  const max = Math.max(1, ...data.map((d) => d.clicks));
  const stepX = data.length > 1 ? (width - pad * 2) / (data.length - 1) : 0;
  const y = (v) => height - pad - (v / max) * (height - pad * 2);
  const x = (i) => pad + i * stepX;

  const points = data.map((d, i) => `${x(i)},${y(d.clicks)}`).join(" ");
  const area = `${pad},${height - pad} ${points} ${x(data.length - 1)},${height - pad}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart" preserveAspectRatio="none">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#areaGrad)" />
      <polyline points={points} fill="none" stroke="var(--accent)" strokeWidth="2" />
    </svg>
  );
}

export function BarBreakdown({ items }) {
  const max = Math.max(1, ...items.map((i) => i.clicks));
  if (items.length === 0) return <div className="muted small">No data yet</div>;
  return (
    <div className="bars">
      {items.map((it) => (
        <div className="bar-row" key={it.label}>
          <span className="bar-label" title={it.label}>
            {it.label}
          </span>
          <span className="bar-track">
            <span className="bar-fill" style={{ width: `${(it.clicks / max) * 100}%` }} />
          </span>
          <span className="bar-value">{it.clicks}</span>
        </div>
      ))}
    </div>
  );
}
