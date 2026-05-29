import client from './client';

const CID = '11111111-0052-4000-8000-000000000001';

// Zone UUID → display name mapping (matches DB campaign_zones)
const ZONE_NAMES = {
  '22222222-0001-4000-8000-000000000001': 'Kondapur',
  '22222222-0002-4000-8000-000000000002': 'Madhapur',
  '22222222-0003-4000-8000-000000000003': 'Gachibowli',
  '22222222-0004-4000-8000-000000000004': 'HITEC City',
  '22222222-0005-4000-8000-000000000005': 'Hafeezpet',
  '22222222-0006-4000-8000-000000000006': 'Chandanagar',
  '22222222-0007-4000-8000-000000000007': 'Nallagandla',
};

// Derive a main issue label from booth scores when no explicit issue data exists
function deriveIssue(risk, contact, health) {
  if (risk > 70) return 'High Risk';
  if (contact < 20) return 'Low Coverage';
  if (health < 35) return 'Low Engagement';
  return 'Monitored';
}

// Map /api/v1/booths fields → BoothIntelligence.jsx expected shape
function toIntelligenceShape(b) {
  const health = parseFloat(b.health_score) || 50;
  const contact = parseFloat(b.contact_rate) || 0;
  const risk = parseFloat(b.risk_score) || 50;

  // health_score (0–100) → mood_score (1–5 scale)
  const mood_score = Math.min(5, Math.max(1, Math.round((1 + health / 25) * 10) / 10));

  // contact_rate → support_trend
  const support_trend = contact > 50 ? 'rising' : contact > 25 ? 'stable' : 'falling';

  return {
    id: b.booth_number,
    constituency: 'Serilingampally',
    area: b.booth_name || `Booth ${b.booth_number}`,
    zone: ZONE_NAMES[b.zone_id] || 'Unknown',
    total_voters: b.total_voters || 0,
    male_voters: b.male_voters || 0,
    female_voters: b.female_voters || 0,
    mood_score,
    main_issue: deriveIssue(risk, contact, health),
    support_trend,
    last_updated: b.updated_at || b.last_report_at || b.created_at,
    risk_score: risk,
    health_score: health,
    contact_rate: contact,
    swing_booth: b.swing_booth,
  };
}

export async function getBoothIntelligence(params = {}) {
  const { data } = await client.get('/v1/booths', {
    params: { constituency_id: CID, limit: 500, ...params },
  });
  const raw = Array.isArray(data) ? data : data.booths || [];
  return { booths: raw.map(toIntelligenceShape), total: data.total || raw.length };
}
