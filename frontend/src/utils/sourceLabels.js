// Source attribution constants for NETA.AI
// All data in the platform must carry a source label so users know whether
// they are looking at verified data, live API data, or demo fallback data.

export const DATA_SOURCES = {
  CENSUS_2011: {
    id: 'census_2011',
    label: 'Census India 2011',
    shortLabel: 'Census 2011',
    color: '#6366f1',
    bg: 'rgba(99,102,241,0.12)',
    border: 'rgba(99,102,241,0.3)',
  },
  ECI: {
    id: 'eci',
    label: 'Election Commission of India',
    shortLabel: 'ECI Electoral Data',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    border: 'rgba(16,185,129,0.3)',
  },
  GHMC: {
    id: 'ghmc',
    label: 'GHMC Ward Data',
    shortLabel: 'GHMC',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    border: 'rgba(245,158,11,0.3)',
  },
  VAYU: {
    id: 'vayu',
    label: 'VAYU Ground Reports',
    shortLabel: 'VAYU',
    color: '#3b82f6',
    bg: 'rgba(59,130,246,0.12)',
    border: 'rgba(59,130,246,0.3)',
  },
  VANI: {
    id: 'vani',
    label: 'VANI Media Intelligence',
    shortLabel: 'VANI',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.12)',
    border: 'rgba(139,92,246,0.3)',
  },
  VIVEK: {
    id: 'vivek',
    label: 'VIVEK Opposition Monitor',
    shortLabel: 'VIVEK',
    color: '#ef4444',
    bg: 'rgba(239,68,68,0.12)',
    border: 'rgba(239,68,68,0.3)',
  },
  VISHLESHAN: {
    id: 'vishleshan',
    label: 'VISHLESHAN Predictive Analytics',
    shortLabel: 'VISHLESHAN',
    color: '#f97316',
    bg: 'rgba(249,115,22,0.12)',
    border: 'rgba(249,115,22,0.3)',
  },
  DEMO: {
    id: 'demo',
    label: 'Demo Data · Backend Offline',
    shortLabel: 'Demo Mode',
    color: '#64748b',
    bg: 'rgba(100,116,139,0.1)',
    border: 'rgba(100,116,139,0.25)',
  },
};

// Source credibility tiers for Telangana news outlets
// A = High credibility (national/established regional), B = Verified regional, C = Monitor/unverified
export const NEWS_CREDIBILITY = {
  'Deccan Chronicle':   'A',
  'Times of India':     'A',
  'Eenadu':             'A',
  'Sakshi':             'B',
  'Telangana Today':    'B',
  'The Hans India':     'B',
  'TV9 Telugu':         'B',
  'V6 News':            'B',
  'NTV Telugu':         'B',
  'Telangana Journal':  'C',
  'WhatsApp Forward':   'C',
};

export const CREDIBILITY_STYLE = {
  A: { label: 'High Credibility', color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
  B: { label: 'Verified Source',  color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.25)' },
  C: { label: 'Monitor',          color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.25)' },
};

export function getCredibilityTier(sourceName) {
  return NEWS_CREDIBILITY[sourceName] || 'B';
}
