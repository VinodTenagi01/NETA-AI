import { PieChart, Pie, Cell } from 'recharts';

function getColor(p) {
  if (p >= 65) return '#10b981';
  if (p >= 50) return '#f59e0b';
  return '#ef4444';
}

export default function WinGauge({ probability, size = 240 }) {
  const color = getColor(probability);
  const fill = probability * 2;
  const empty = (100 - probability) * 2;
  const data = [
    { value: fill },
    { value: empty },
  ];

  const cx = size / 2;
  const cy = size * 0.58;
  const ir = size * 0.34;
  const or = size * 0.44;

  return (
    <div className="win-gauge-wrap">
      <div style={{ position: 'relative', width: size, height: size * 0.65 }}>
        <PieChart width={size} height={size * 0.65}>
          <Pie
            data={data}
            cx={cx}
            cy={cy}
            startAngle={180}
            endAngle={0}
            innerRadius={ir}
            outerRadius={or}
            dataKey="value"
            strokeWidth={0}
          >
            <Cell fill={color} />
            <Cell fill="#1a2640" />
          </Pie>
        </PieChart>

        {/* Needle-style center marker */}
        <svg
          style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
          width={size}
          height={size * 0.65}
        >
          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = 180 - tick * 1.8;
            const rad = (angle * Math.PI) / 180;
            const r1 = or + 6;
            const r2 = or + 14;
            const x1 = cx + r1 * Math.cos(rad);
            const y1 = cy - r1 * Math.sin(rad);
            const x2 = cx + r2 * Math.cos(rad);
            const y2 = cy - r2 * Math.sin(rad);
            return (
              <line key={tick} x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="var(--border-bright)" strokeWidth={2} />
            );
          })}

          {/* Tick labels */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = 180 - tick * 1.8;
            const rad = (angle * Math.PI) / 180;
            const r = or + 22;
            const x = cx + r * Math.cos(rad);
            const y = cy - r * Math.sin(rad);
            return (
              <text key={`label-${tick}`} x={x} y={y}
                textAnchor="middle" dominantBaseline="middle"
                fill="var(--text-muted)" fontSize={9} fontFamily="var(--font-mono)"
              >
                {tick}
              </text>
            );
          })}

          {/* Needle */}
          {(() => {
            const angle = 180 - probability * 1.8;
            const rad = (angle * Math.PI) / 180;
            const tipR = ir - 8;
            const x = cx + tipR * Math.cos(rad);
            const y = cy - tipR * Math.sin(rad);
            return (
              <>
                <line x1={cx} y1={cy} x2={x} y2={y}
                  stroke={color} strokeWidth={2.5} strokeLinecap="round" />
                <circle cx={cx} cy={cy} r={5} fill={color} />
              </>
            );
          })()}
        </svg>
      </div>

      <div className="win-gauge-value" style={{ color }}>
        {probability}<span style={{ fontSize: 24, color: 'var(--text-muted)' }}>%</span>
      </div>
      <div className="win-gauge-sub">Win Probability</div>
    </div>
  );
}
