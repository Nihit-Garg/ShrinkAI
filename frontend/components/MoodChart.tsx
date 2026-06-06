"use client";

interface MoodEntry {
  score: number;        // -1.0 to 1.0
  recorded_at: string;  // ISO date string
  session_id: string;
}

interface MoodChartProps {
  data: MoodEntry[];
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function scoreLabel(score: number): string {
  if (score >= 0.6) return 'Hopeful';
  if (score >= 0.2) return 'Okay';
  if (score >= -0.2) return 'Neutral';
  if (score >= -0.6) return 'Low';
  return 'Distressed';
}

function scoreColor(score: number): string {
  if (score >= 0.3) return '#7ca982'; // sage green
  if (score >= -0.3) return '#c4a882'; // warm sand
  return '#c4825a'; // warm amber-red
}

export function MoodChart({ data }: MoodChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-full bg-[var(--color-sage)]/10 flex items-center justify-center mb-4">
          <div className="w-8 h-8 rounded-full bg-[var(--color-sage)]/30" />
        </div>
        <p className="text-[var(--color-charcoal)] font-medium mb-2">No mood data yet</p>
        <p className="text-sm text-[var(--color-slate)] max-w-xs leading-relaxed">
          Mood scores are captured automatically after each conversation. Have a few sessions and come back here.
        </p>
      </div>
    );
  }

  // Chart dimensions
  const W = 560;
  const H = 220;
  const pad = { top: 24, right: 24, bottom: 44, left: 44 };
  const cW = W - pad.left - pad.right;
  const cH = H - pad.top - pad.bottom;

  // Coordinate helpers
  const toX = (i: number) =>
    pad.left + (data.length === 1 ? cW / 2 : (i / (data.length - 1)) * cW);
  const toY = (score: number) =>
    pad.top + ((1 - score) / 2) * cH;

  const zeroY = toY(0);
  const latestScore = data[data.length - 1]?.score ?? 0;

  // SVG path
  const pts = data.map((d, i) => `${toX(i)},${toY(d.score)}`);
  const linePath = pts.length > 1 ? `M ${pts.join(' L ')}` : '';

  // Gradient fill under line
  const fillPath =
    pts.length > 1
      ? `M ${toX(0)},${zeroY} L ${pts.join(' L ')} L ${toX(data.length - 1)},${zeroY} Z`
      : '';

  // Y-axis labels
  const yLabels = [
    { score: 1.0, label: '+1.0' },
    { score: 0.5, label: '+0.5' },
    { score: 0, label: '0' },
    { score: -0.5, label: '−0.5' },
    { score: -1.0, label: '−1.0' },
  ];

  return (
    <div className="w-full">
      {/* Current mood summary */}
      <div className="flex items-center gap-3 mb-6">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: scoreColor(latestScore) }}
        />
        <span className="text-sm text-[var(--color-slate)]">
          Latest session mood:{' '}
          <span className="font-semibold text-[var(--color-charcoal)]">
            {scoreLabel(latestScore)}
          </span>{' '}
          <span className="opacity-60">({latestScore >= 0 ? '+' : ''}{latestScore.toFixed(2)})</span>
        </span>
      </div>

      {/* SVG Chart */}
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full max-w-2xl"
          style={{ minWidth: '300px' }}
        >
          <defs>
            <linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#7ca982" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#7ca982" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Background */}
          <rect x={pad.left} y={pad.top} width={cW} height={cH} fill="rgba(255,255,255,0.4)" rx={8} />

          {/* Y-axis gridlines + labels */}
          {yLabels.map(({ score, label }) => {
            const y = toY(score);
            return (
              <g key={score}>
                <line
                  x1={pad.left}
                  y1={y}
                  x2={pad.left + cW}
                  y2={y}
                  stroke={score === 0 ? '#9cad9f' : '#e0e8e1'}
                  strokeWidth={score === 0 ? 1.5 : 1}
                  strokeDasharray={score === 0 ? undefined : '4 3'}
                />
                <text
                  x={pad.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize={9}
                  fill="#9cad9f"
                >
                  {label}
                </text>
              </g>
            );
          })}

          {/* Fill under line */}
          {fillPath && (
            <path d={fillPath} fill="url(#moodGradient)" />
          )}

          {/* Line */}
          {linePath && (
            <path
              d={linePath}
              fill="none"
              stroke="#7ca982"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Data points + tooltips */}
          {data.map((d, i) => (
            <g key={i}>
              <circle
                cx={toX(i)}
                cy={toY(d.score)}
                r={5}
                fill="white"
                stroke={scoreColor(d.score)}
                strokeWidth={2.5}
              />
              {/* X-axis date label — show every nth if dense */}
              {(data.length <= 8 || i % Math.ceil(data.length / 8) === 0 || i === data.length - 1) && (
                <text
                  x={toX(i)}
                  y={H - 6}
                  textAnchor="middle"
                  fontSize={9}
                  fill="#9cad9f"
                >
                  {formatDate(d.recorded_at)}
                </text>
              )}
            </g>
          ))}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-4 text-xs text-[var(--color-slate)]">
        {[
          { color: '#7ca982', label: 'Hopeful (≥ +0.3)' },
          { color: '#c4a882', label: 'Neutral' },
          { color: '#c4825a', label: 'Low (≤ −0.3)' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
