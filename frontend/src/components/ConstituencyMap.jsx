import { useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, ZoomControl, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Geographic centre of Serilingampally AC-52, Telangana
const CENTRE = [17.4725, 78.3300];
const INITIAL_ZOOM = 13;

// Approximate constituency boundary polygon — AC-52 Serilingampally
// Covers Chandanagar, Miyapur, Kondapur, Gachibowli, Manikonda, Nallagandla
const CONSTITUENCY_GEO = {
  type: 'Feature',
  properties: { name: 'Serilingampally AC-52', type: 'constituency' },
  geometry: {
    type: 'Polygon',
    coordinates: [[
      [78.2780, 17.5050],
      [78.3050, 17.5120],
      [78.3420, 17.5100],
      [78.3700, 17.4950],
      [78.4000, 17.4720],
      [78.4050, 17.4420],
      [78.3950, 17.4050],
      [78.3650, 17.3830],
      [78.3280, 17.3780],
      [78.2980, 17.3950],
      [78.2780, 17.4300],
      [78.2680, 17.4700],
      [78.2780, 17.5050],
    ]],
  },
};

// Ward-level zone boundaries (approximate, based on GHMC ward clusters)
const WARD_GEO = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { zone: 'North', label: 'Miyapur / Bachupally' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.3050, 17.5120], [78.3420, 17.5100],
          [78.3550, 17.4900], [78.3350, 17.4750],
          [78.3050, 17.4800], [78.2900, 17.4950],
          [78.3050, 17.5120],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { zone: 'West', label: 'Chandanagar / Hafeezpet' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.2780, 17.5050], [78.3050, 17.5120],
          [78.2900, 17.4950], [78.2780, 17.4700],
          [78.2680, 17.4700], [78.2780, 17.5050],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { zone: 'Central', label: 'Serilingampally / Nallagandla' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.2900, 17.4950], [78.3350, 17.4750],
          [78.3500, 17.4550], [78.3300, 17.4300],
          [78.2980, 17.4250], [78.2780, 17.4300],
          [78.2680, 17.4700], [78.2900, 17.4950],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { zone: 'East', label: 'Kondapur / Gachibowli' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.3550, 17.4900], [78.3700, 17.4950],
          [78.4050, 17.4720], [78.4050, 17.4420],
          [78.3950, 17.4050], [78.3700, 17.4050],
          [78.3500, 17.4200], [78.3300, 17.4300],
          [78.3500, 17.4550], [78.3550, 17.4900],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { zone: 'South', label: 'Manikonda / Puppalaguda' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.2980, 17.3950], [78.3280, 17.3780],
          [78.3650, 17.3830], [78.3700, 17.4050],
          [78.3500, 17.4200], [78.3300, 17.4300],
          [78.2980, 17.4250], [78.2780, 17.4300],
          [78.2980, 17.3950],
        ]],
      },
    },
  ],
};

const ZONE_COLOURS = {
  North:   '#3b82f6',
  South:   '#8b5cf6',
  East:    '#f59e0b',
  West:    '#10b981',
  Central: '#f97316',
};

// Real-world locality centres for each zone in Serilingampally AC-52
const ZONE_CENTRES = {
  North:   [17.4953, 78.3350],  // Miyapur / Bachupally
  South:   [17.3950, 78.3280],  // Manikonda
  East:    [17.4480, 78.3820],  // Kondapur / Gachibowli
  West:    [17.4870, 78.2930],  // Chandanagar
  Central: [17.4780, 78.3150],  // Serilingampally / Nallagandla
};

const ZONE_LOCALITIES = {
  North:   'Miyapur / Bachupally',
  South:   'Manikonda / Puppalaguda',
  East:    'Kondapur / Gachibowli',
  West:    'Chandanagar / Hafeezpet',
  Central: 'Serilingampally / Nallagandla',
};

const ZONES = Object.keys(ZONE_CENTRES);

// Seeded PRNG — booth positions are deterministic across renders
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = t + Math.imul(t ^ (t >>> 7), 61 | t) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function generateBooths(count = 150) {
  const rand = mulberry32(0xDEADBEEF);
  return Array.from({ length: count }, (_, i) => {
    const zone = ZONES[i % ZONES.length];
    const [cLat, cLng] = ZONE_CENTRES[zone];
    const lat = cLat + (rand() - 0.5) * 0.016;
    const lng = cLng + (rand() - 0.5) * 0.016;
    const contactRate = Math.round(rand() * 100);
    const support = rand();
    const voters = 1400 + Math.round(rand() * 900);
    const riskLevel = contactRate < 40 || support < 0.4 ? 'high'
      : contactRate < 65 || support < 0.6 ? 'medium' : 'low';
    return {
      id: i + 1,
      name: `Booth B${String(i + 1).padStart(3, '0')}`,
      lat, lng, zone,
      locality: ZONE_LOCALITIES[zone],
      contactRate,
      support: Math.round(support * 100),
      voters,
      riskLevel,
      ppName: `PP-${zone.slice(0, 1)}${String(i + 1).padStart(2, '0')}`,
    };
  });
}

const ALL_BOOTHS = generateBooths(150);

function markerColor(riskLevel) {
  if (riskLevel === 'high')   return '#ef4444';
  if (riskLevel === 'medium') return '#f59e0b';
  return '#10b981';
}

const CONSTITUENCY_STYLE = {
  color: '#f97316',
  weight: 2,
  opacity: 0.7,
  fillOpacity: 0,
  dashArray: '6 4',
};

function wardStyle(feature) {
  const color = ZONE_COLOURS[feature.properties.zone] || '#666';
  return {
    color,
    weight: 1,
    opacity: 0.4,
    fillColor: color,
    fillOpacity: 0.06,
    dashArray: '3 3',
  };
}

function FitBounds({ booths }) {
  const map = useMap();
  useEffect(() => {
    if (!booths.length) return;
    const lats = booths.map(b => b.lat);
    const lngs = booths.map(b => b.lng);
    map.fitBounds(
      [[Math.min(...lats) - 0.004, Math.min(...lngs) - 0.004],
       [Math.max(...lats) + 0.004, Math.max(...lngs) + 0.004]],
      { padding: [24, 24] },
    );
  }, [booths, map]);
  return null;
}

export default function ConstituencyMap({ filterZone = 'All', filterRisk = 'All', onZoneChange, onRiskChange, height = 520 }) {
  const booths = useMemo(() => {
    return ALL_BOOTHS.filter(b => {
      if (filterZone !== 'All' && b.zone !== filterZone) return false;
      if (filterRisk !== 'All' && b.riskLevel !== filterRisk) return false;
      return true;
    });
  }, [filterZone, filterRisk]);

  const counts = useMemo(() => ({
    high:   ALL_BOOTHS.filter(b => b.riskLevel === 'high').length,
    medium: ALL_BOOTHS.filter(b => b.riskLevel === 'medium').length,
    low:    ALL_BOOTHS.filter(b => b.riskLevel === 'low').length,
  }), []);

  return (
    <div style={{ position: 'relative' }}>
      {/* Filters */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
        marginBottom: 12,
      }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
          Zone
        </span>
        {['All', ...ZONES].map(z => (
          <FilterChip
            key={z} label={z}
            active={filterZone === z}
            dotColor={z !== 'All' ? ZONE_COLOURS[z] : undefined}
            onClick={() => onZoneChange?.(z)}
          />
        ))}
        <div style={{ width: 1, height: 16, background: 'var(--border)' }} />
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
          Risk
        </span>
        {[
          { label: 'All', value: 'All' },
          { label: `High (${counts.high})`, value: 'high', color: '#ef4444' },
          { label: `Med (${counts.medium})`, value: 'medium', color: '#f59e0b' },
          { label: `Low (${counts.low})`, value: 'low', color: '#10b981' },
        ].map(({ label, value, color }) => (
          <FilterChip key={value} label={label} active={filterRisk === value} dotColor={color} onClick={() => onRiskChange?.(value)} />
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-muted)' }}>
          {booths.length} booths
        </span>
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute', top: 44, right: 10, zIndex: 1000,
        background: 'rgba(11,19,33,0.92)', border: '1px solid var(--border)',
        borderRadius: 8, padding: '8px 12px', fontSize: 10,
        backdropFilter: 'blur(8px)',
      }}>
        <div style={{ fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 }}>
          Booth Risk
        </div>
        {[
          { color: '#10b981', label: 'Secured',    desc: '≥ 65% contact' },
          { color: '#f59e0b', label: 'Watch',      desc: '40–65%' },
          { color: '#ef4444', label: 'Critical',   desc: '< 40%' },
        ].map(({ color, label, desc }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{label}</span>
            <span style={{ color: 'var(--text-muted)' }}>· {desc}</span>
          </div>
        ))}
        <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3 }}>
            <div style={{ width: 16, height: 2, background: '#f97316', borderTop: '2px dashed #f97316' }} />
            <span style={{ color: 'var(--text-muted)' }}>AC-52 boundary</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 16, height: 2, borderTop: '1px dashed #666' }} />
            <span style={{ color: 'var(--text-muted)' }}>Ward zones</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={CENTRE}
        zoom={INITIAL_ZOOM}
        zoomControl={false}
        style={{
          height: height,
          borderRadius: 12,
          border: '1px solid var(--border)',
          background: '#0c1525',
        }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={18}
        />
        <ZoomControl position="bottomright" />
        <FitBounds booths={booths} />

        {/* Constituency boundary */}
        <GeoJSON
          data={CONSTITUENCY_GEO}
          style={CONSTITUENCY_STYLE}
        />

        {/* Ward zone overlays */}
        <GeoJSON
          data={WARD_GEO}
          style={wardStyle}
          onEachFeature={(feature, layer) => {
            layer.bindTooltip(
              `<div style="font-size:11px;font-weight:700;color:#e2e8f0">${feature.properties.zone}</div>` +
              `<div style="font-size:10px;color:#94a3b8">${feature.properties.label}</div>`,
              { sticky: true, opacity: 0.95 },
            );
          }}
        />

        {/* Booth markers */}
        {booths.map(booth => (
          <CircleMarker
            key={booth.id}
            center={[booth.lat, booth.lng]}
            radius={5}
            pathOptions={{
              color: markerColor(booth.riskLevel),
              fillColor: markerColor(booth.riskLevel),
              fillOpacity: 0.82,
              weight: 1.5,
              opacity: 0.9,
            }}
          >
            <Tooltip direction="top" offset={[0, -4]} opacity={0.97}>
              <div style={{ minWidth: 170 }}>
                <div style={{ fontWeight: 700, marginBottom: 3, color: '#e2e8f0' }}>
                  {booth.name}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2, fontSize: 11 }}>
                  <span><b>Locality:</b> {booth.locality}</span>
                  <span><b>Zone:</b> {booth.zone}</span>
                  <span><b>Voters:</b> {booth.voters.toLocaleString()}</span>
                  <span><b>Contact Rate:</b> {booth.contactRate}%</span>
                  <span><b>Support:</b> {booth.support}%</span>
                  <span><b>PP:</b> {booth.ppName}</span>
                  <span style={{ color: markerColor(booth.riskLevel), fontWeight: 700, textTransform: 'uppercase', fontSize: 10, marginTop: 2 }}>
                    {booth.riskLevel === 'high' ? 'critical' : booth.riskLevel} risk
                  </span>
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Stats bar */}
      <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
        {[
          { label: 'Total Booths', value: ALL_BOOTHS.length, color: 'var(--blue)' },
          { label: 'Critical', value: counts.high, color: '#ef4444' },
          { label: 'Watch', value: counts.medium, color: '#f59e0b' },
          { label: 'Secured', value: counts.low, color: '#10b981' },
          { label: 'Avg Contact', value: `${Math.round(ALL_BOOTHS.reduce((s, b) => s + b.contactRate, 0) / ALL_BOOTHS.length)}%`, color: 'var(--text-secondary)' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            flex: '1 1 auto', padding: '8px 12px', borderRadius: 8,
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 17, fontWeight: 800, fontFamily: 'var(--font-mono)', color }}>{value}</div>
            <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.6, marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FilterChip({ label, active, dotColor, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '3px 9px', borderRadius: 20, fontSize: 10, fontWeight: 600,
        cursor: onClick ? 'pointer' : 'default',
        background: active ? 'rgba(249,115,22,0.15)' : 'var(--bg-elevated)',
        border: `1px solid ${active ? 'rgba(249,115,22,0.5)' : 'var(--border)'}`,
        color: active ? 'var(--saffron)' : 'var(--text-secondary)',
        display: 'inline-flex', alignItems: 'center', gap: 5,
        transition: 'all 0.15s',
      }}
    >
      {dotColor && <span style={{ width: 6, height: 6, borderRadius: '50%', background: dotColor, display: 'inline-block' }} />}
      {label}
    </button>
  );
}
