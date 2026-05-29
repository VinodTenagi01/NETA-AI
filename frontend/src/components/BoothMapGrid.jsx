import { useState } from 'react';
import { booths } from '../data/mockData';

const ZONE_ORDER = ['Central', 'North', 'South', 'East', 'West'];
const ZONE_COLORS = {
  Central: 'var(--purple)',
  North:   'var(--blue)',
  South:   'var(--green)',
  East:    'var(--red)',
  West:    'var(--yellow)',
};

const STATUS_COLOR = {
  fortress: '#059669',
  swing:    '#d97706',
  hostile:  '#dc2626',
};

export default function BoothMapGrid({ compact = false }) {
  const [hovered, setHovered] = useState(null);
  const cellSize = compact ? 14 : 18;
  const gap = compact ? 2 : 3;
  const cols = 15;

  // Arrange 150 booths in 15x10 grid, grouped loosely by zone
  const grid = booths;

  // Summary counts
  const fortress = booths.filter(b => b.status === 'fortress').length;
  const swing    = booths.filter(b => b.status === 'swing').length;
  const hostile  = booths.filter(b => b.status === 'hostile').length;
  const uncovered = booths.filter(b => !b.covered).length;

  return (
    <div>
      {/* Zone label row */}
      <div
        style={{
          display: 'flex', gap: 8, flexWrap: 'wrap',
          marginBottom: 10, paddingLeft: compact ? 8 : 12,
        }}
      >
        {ZONE_ORDER.map(z => (
          <span key={z}
            style={{
              fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
              color: ZONE_COLORS[z], textTransform: 'uppercase',
            }}
          >
            ● {z}
          </span>
        ))}
      </div>

      {/* Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
          gap: `${gap}px`,
          padding: compact ? '8px' : '12px',
        }}
      >
        {grid.map((booth) => (
          <div
            key={booth.id}
            onMouseEnter={() => setHovered(booth)}
            onMouseLeave={() => setHovered(null)}
            title={`${booth.code} — ${booth.zone}\nStatus: ${booth.status}\nContact: ${booth.contactRate}%\nPulse: ${booth.pulseScore}/5`}
            style={{
              width: cellSize,
              height: cellSize,
              borderRadius: 2,
              cursor: 'pointer',
              background: booth.covered
                ? STATUS_COLOR[booth.status]
                : '#1e2d45',
              opacity: booth.covered ? 1 : 0.45,
              border: hovered?.id === booth.id ? '1.5px solid #fff' : '1px solid transparent',
              transition: 'all 0.15s',
              transform: hovered?.id === booth.id ? 'scale(1.5)' : 'scale(1)',
              zIndex: hovered?.id === booth.id ? 5 : 1,
              position: 'relative',
            }}
          />
        ))}
      </div>

      {/* Tooltip */}
      {hovered && (
        <div
          style={{
            margin: '6px 12px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-bright)',
            borderRadius: 6,
            padding: '8px 12px',
            fontSize: 11,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 2 }}>
            {hovered.code} — {hovered.name.split(' — ')[1]}
          </div>
          <div style={{ color: 'var(--text-secondary)', display: 'flex', gap: 14 }}>
            <span>Status: <b style={{ color: STATUS_COLOR[hovered.status], textTransform: 'capitalize' }}>{hovered.status}</b></span>
            <span>Contact: <b>{hovered.contactRate}%</b></span>
            <span>Pulse: <b>{hovered.pulseScore}/5</b></span>
            <span>Voters: <b>{hovered.voters.toLocaleString()}</b></span>
          </div>
          {hovered.pannaPramukh && (
            <div style={{ color: 'var(--text-muted)', marginTop: 2, fontSize: 10 }}>
              Panna Pramukh: {hovered.pannaPramukh}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          display: 'flex', gap: 14, padding: `4px ${compact ? 8 : 12}px`,
          marginTop: 6, borderTop: '1px solid var(--border)',
          paddingTop: 10,
        }}
      >
        {[
          { color: '#059669', label: `Fortress (${fortress})` },
          { color: '#d97706', label: `Swing (${swing})` },
          { color: '#dc2626', label: `Hostile (${hostile})` },
          { color: '#1e2d45', label: `Uncovered (${uncovered})`, opacity: 0.5 },
        ].map(({ color, label, opacity = 1 }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color, opacity, flexShrink: 0 }} />
            <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
