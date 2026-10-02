export default function TimeseriesChart({ points, metric = "traffic" }) {
  const series = Array.isArray(points) ? points : [];
  if (series.length === 0) {
    return <p className="muted">No time-series points are available yet.</p>;
  }

  const values = series.map((point) => Number(point[metric]) || 0);
  const max = Math.max(...values, 1);
  const width = 640;
  const height = 220;
  const pad = 28;
  const innerWidth = width - pad * 2;
  const innerHeight = height - pad * 2;

  const coords = values.map((value, index) => {
    const x = pad + (series.length === 1 ? innerWidth / 2 : (index / (series.length - 1)) * innerWidth);
    const y = pad + innerHeight - (value / max) * innerHeight;
    return `${x},${y}`;
  });

  return (
    <div className="chart-wrap">
      <svg className="timeseries-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${metric} over time`}>
        <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="currentColor" strokeOpacity="0.2" />
        <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="currentColor" strokeOpacity="0.2" />
        <line className="chart-grid-line" x1={pad} y1={pad + innerHeight / 3} x2={width - pad} y2={pad + innerHeight / 3} />
        <line className="chart-grid-line" x1={pad} y1={pad + (innerHeight * 2) / 3} x2={width - pad} y2={pad + (innerHeight * 2) / 3} />
        <polyline fill="none" stroke="var(--prism-blue)" strokeWidth="3" points={coords.join(" ")} />
        {coords.map((pair, index) => {
          const [x, y] = pair.split(",");
          return <circle key={series[index].date || index} cx={x} cy={y} r="4" fill="var(--prism-blue)" />;
        })}
      </svg>
      <div className="chart-legend">
        {series.map((point) => (
          <span key={point.date}>
            {point.date}: {point[metric]}
          </span>
        ))}
      </div>
    </div>
  );
}
