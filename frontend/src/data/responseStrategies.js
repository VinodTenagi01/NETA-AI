// ── NETA.AI Instant Response Strategy Engine ─────────────────────────────────
// Maps detected campaign issues to actionable response strategies.
// All strategies are generic campaign intelligence patterns — no fabricated events.

const STRATEGY_TEMPLATES = {
  water: {
    category: 'Civic Issue — Water Supply',
    actions: [
      'Send ward coordinators to top complaint booths immediately',
      'Release public update on water infrastructure progress within 2 hours',
      'Deploy volunteer grievance collection at key junction points',
      'Highlight existing water delivery timeline in all speeches today',
      'Schedule evening public interaction at the most affected locality',
    ],
    fieldResponse:
      'Mobilize ward coordinators to door-knock 50 priority households. Document complaints digitally for same-day war room review.',
    commsStrategy:
      'Post factual pipeline progress update on WhatsApp worker network and social media. Reinforce existing commitment with concrete timeline — avoid new promises.',
    handlers: ['Ground Team Alpha', 'Ward Coordinators', 'PR Team'],
    deadline: '2 hours',
    impactDesc: 'Reduce negative sentiment by 12–18%',
    impactType: 'Voter trust recovery + removes opposition talking point',
    confidenceScore: 87,
    nextBestAction:
      'Deploy ward coordinators to the 5 highest-complaint booths and collect documented grievances by noon.',
  },

  youth: {
    category: 'Demographic Risk — Youth Engagement',
    actions: [
      'Launch targeted campus and college outreach in the zone today',
      'Increase Instagram/YouTube campaign content frequency to 3× daily',
      'Schedule an exclusive candidate youth interaction session by evening',
      'Circulate employment commitment data through youth WhatsApp groups',
      'Activate youth volunteer brigade for peer-to-peer contact drive',
    ],
    fieldResponse:
      'Identify top 10 youth influencers in the zone. Brief them on employment commitments. Request social amplification from each.',
    commsStrategy:
      'VANI to draft youth-specific social content highlighting job creation data. Keep tone aspirational — not defensive. Use video format.',
    handlers: ['Youth Cell', 'Social Media Team', 'VANI Cell'],
    deadline: 'Before 6 PM today',
    impactDesc: 'Improve youth turnout intention by 10–15 pts',
    impactType: 'Youth voter mobilization + social media narrative',
    confidenceScore: 79,
    nextBestAction:
      'Schedule a 30-minute unscripted Q&A with local youth groups before the evening rally — no prepared script.',
  },

  roads: {
    category: 'Civic Issue — Road Infrastructure',
    actions: [
      'Share road project completion photos and data across all platforms immediately',
      'Arrange candidate to publicly inspect and highlight completed road stretch',
      'Deploy team to gather voter testimonials from road-adjacent households',
      'Counter delay allegations with factual contractor timeline documentation',
      'Include road delivery as the lead proof point in tonight\'s speech',
    ],
    fieldResponse:
      'Ground team to photograph completed road sections with date/location metadata. Submit to PR team before noon for social packaging.',
    commsStrategy:
      'Publish "Roads Delivered" factsheet across WhatsApp, Twitter/X, and Facebook. Before/after photos for maximum credibility.',
    handlers: ['Ground Team', 'PR Team', 'Candidate Office'],
    deadline: 'Before evening rally',
    impactDesc: 'Reinforce development narrative — 8–12% credibility boost',
    impactType: 'Development proof-of-delivery + incumbent contrast',
    confidenceScore: 91,
    nextBestAction:
      'Arrange a 15-minute candidate walkthrough of the completed road stretch — photograph and publish on social before 5 PM.',
  },

  opposition: {
    category: 'Political Risk — Opposition Activity',
    actions: [
      'Brief all booth agents on opposition narrative and counter-talking points within the hour',
      'Activate VANI counter-narrative on WhatsApp networks within 60 minutes',
      'Deploy experienced workers to zones with highest opposition activity',
      'Publish rapid fact-check post on opposition\'s unfulfillable promises',
      'Ensure candidate has crisp counter-response ready for press questions',
    ],
    fieldResponse:
      'Zone coordinators into opposition-active areas for ground pulse. Report mood shift data back to war room within 2 hours.',
    commsStrategy:
      'VANI to publish factual counter narrative using budget math to expose promise gap. Avoid emotional tone — stay factual and shareable.',
    handlers: ['War Room', 'VANI Cell', 'Booth Coordinators'],
    deadline: '1 hour',
    impactDesc: 'Neutralize opposition momentum — prevent estimated 15-pt swing',
    impactType: 'Opposition counter + media narrative control',
    confidenceScore: 83,
    nextBestAction:
      'Activate VANI counter-narrative post on the opposition\'s key promise within 60 minutes — before it trends further on social media.',
  },

  sentiment: {
    category: 'Campaign Risk — Sentiment Decline',
    actions: [
      'Initiate targeted door-to-door contact in the declining zone immediately',
      'Schedule candidate visit or 3 corner meetings in zone before 8 PM',
      'Brief all workers on top reported concerns and provide talking-point cards',
      'Deploy rapid feedback collection to identify root cause of decline',
      'Engage senior community leaders in zone for trust reinforcement',
    ],
    fieldResponse:
      'Redeploy 15–20 workers from higher-sentiment zones. Conduct corner meetings in top-3 affected ward clusters before sunset.',
    commsStrategy:
      'Tailor evening speech to directly address top concerns from declining zone. Show empathy and specificity — not generic assurances.',
    handlers: ['Ground Team Alpha', 'Candidate Direct Visit', 'Zone Coordinator'],
    deadline: 'Before 8 PM today',
    impactDesc: 'Arrest decline and recover 8–14 sentiment points over 48 hours',
    impactType: 'Voter retention + ground morale recovery',
    confidenceScore: 76,
    nextBestAction:
      'Candidate must personally visit the top-declining zone and conduct at least 2 unscripted public interactions before the main rally.',
  },

  booth: {
    category: 'Operational Risk — Booth Coverage Gap',
    actions: [
      'Identify all uncovered booth slots and fill by redeployment from over-covered zones',
      'Cross-check voter contact targets vs actuals and bridge the gap immediately',
      'Activate reserve volunteer list for emergency coverage of weak booths',
      'Assign a zone supervisor for hourly check-in from each weak booth',
      'Escalate contact rate issue to operations cell for same-day fix',
    ],
    fieldResponse:
      'Operations cell to identify available workers within 5 km of each uncovered booth. Deploy before afternoon field shift begins.',
    commsStrategy:
      'Internal communications only — do not publicize booth coverage gap. Focus messaging on voter contact milestones achieved so far.',
    handlers: ['Operations Cell', 'Booth Coordinators', 'Zone Supervisor'],
    deadline: 'Before noon',
    impactDesc: 'Close voter contact gap — recover 800–1,200 contacts by day end',
    impactType: 'Booth stabilization + contact rate normalization',
    confidenceScore: 88,
    nextBestAction:
      'Redeploy 20 workers from over-covered zones to the 5 weakest booths — complete by 11 AM to capture peak contact window.',
  },

  power: {
    category: 'Civic Issue — Power Supply',
    actions: [
      'Acknowledge the power issue directly — do not minimize or ignore it',
      'Commit to formal escalation to TSECPDCL leadership in writing today',
      'Share the documented escalation letter publicly via media and social',
      'Counter opposition power promises with concrete budget feasibility facts',
      'Position candidate as the honest voice versus empty opposition promises',
    ],
    fieldResponse:
      'Workers to empathize and acknowledge the power issue. Do not promise 24-hr power. Focus on documented escalation and accountability.',
    commsStrategy:
      'Publish TSECPDCL escalation letter on social media. Frame as "fighting for you, not just promising you." Contrast with opposition rhetoric.',
    handlers: ['Candidate Office', 'PR Team', 'War Room'],
    deadline: 'Within 24 hours',
    impactDesc: 'Build honest-broker credibility — prevent 5–8% voter erosion',
    impactType: 'Credibility protection + opposition counter on power narrative',
    confidenceScore: 72,
    nextBestAction:
      'Draft and publish an official TSECPDCL escalation letter today — share proof of action, not just verbal commitment.',
  },

  healthcare: {
    category: 'Civic Issue — Healthcare Access',
    actions: [
      'Announce concrete plan for urban health sub-centre expansion with timeline',
      'Partner with hospital for a free diagnostics camp this week — fix the date',
      'Activate women SHG networks in zone as healthcare advocates and multipliers',
      'Brief candidate with health commitment talking points for women voter interactions',
      'Ensure healthcare commitment leads the agenda in tonight\'s speech',
    ],
    fieldResponse:
      'Target women SHG group leaders for 1-on-1 outreach. Healthcare is a trust issue for women voters — personal contact matters most.',
    commsStrategy:
      'Announce free diagnostics camp date publicly via WhatsApp and social. Frame as proof of commitment — not a future promise.',
    handlers: ['Women Cell', 'Ground Team', 'Candidate Office'],
    deadline: 'Before evening rally',
    impactDesc: 'Improve women voter trust by 12–16 pts',
    impactType: 'Women voter retention + healthcare delivery credibility',
    confidenceScore: 81,
    nextBestAction:
      'Confirm and publicly announce the free diagnostics camp date in today\'s evening interaction — specific date, not "soon."',
  },

  drainage: {
    category: 'Civic Issue — Drainage & Flooding',
    actions: [
      'Acknowledge the drainage issue directly and without minimizing it',
      'Commit to a storm-water drain project for the most affected wards with specs',
      'Validate feasibility with an engineer before announcing project details',
      'Share documented evidence that the issue has been escalated to GHMC',
      'Candidate to visit the worst-affected drainage area publicly before sunset',
    ],
    fieldResponse:
      'Ground team to photograph and document worst-affected drainage spots. Submit evidence to PR and war room by noon for same-day use.',
    commsStrategy:
      'Publish GHMC escalation proof. Announce site visit time publicly. Frame as responsive leadership vs 3 years of incumbent neglect.',
    handlers: ['Ground Team', 'Candidate Direct Visit', 'PR Team'],
    deadline: 'Before evening',
    impactDesc: 'Convert frustrated voters from hostile to undecided — prevent 8–10% loss',
    impactType: 'Civic credibility + turnout protection in low-income areas',
    confidenceScore: 78,
    nextBestAction:
      'Candidate to visit the worst-affected drainage spot publicly before 5 PM — with photos shared in real time on all platforms.',
  },

  rumour: {
    category: 'Narrative Risk — Rumour / Disinformation',
    actions: [
      'Document the exact rumour text and identify its origin channels immediately',
      'Brief all booth workers on the counter-narrative within 30 minutes',
      'Activate VANI counter-narrative post across all WhatsApp networks',
      'Engage 3–5 credible community voices to publicly refute the rumour',
      'Prepare candidate with a crisp one-liner counter for press and public use',
    ],
    fieldResponse:
      'Each booth worker to personally counter-brief 5 known influencers in their cluster. Focus on trust and relationships — not just facts.',
    commsStrategy:
      'VANI counter post must be factual, crisp, and shareable. Avoid defensive tone. Use community voice format for higher credibility.',
    handlers: ['VANI Cell', 'War Room', 'Booth Coordinators'],
    deadline: '30 minutes',
    impactDesc: 'Contain spread — limit voter impact to under 3%',
    impactType: 'Narrative control + voter trust protection',
    confidenceScore: 84,
    nextBestAction:
      'Activate VANI counter-narrative on the primary rumour within 30 minutes — speed is the single most critical factor in rumour containment.',
  },

  default: {
    category: 'General Campaign Risk',
    actions: [
      'Escalate to war room for immediate situation assessment',
      'Brief zone supervisor and all ground team leads on the issue',
      'Collect detailed field reports from affected area within 1 hour',
      'Prepare candidate with full context and response talking points',
      'Monitor situation and report back to campaign command within 2 hours',
    ],
    fieldResponse:
      'Zone coordinator to conduct rapid field assessment. Document voter mood and specific complaints. Report by next check-in window.',
    commsStrategy:
      'Hold external communication until war room assessment is complete. Prepare response draft in parallel so it is ready to deploy.',
    handlers: ['War Room', 'Zone Coordinator', 'Ground Team'],
    deadline: 'Within 2 hours',
    impactDesc: 'Prevent escalation — stabilize before the issue spreads',
    impactType: 'General risk containment + campaign continuity',
    confidenceScore: 65,
    nextBestAction:
      'Convene a 15-minute war room call to assess situation and agree on a unified response strategy before any external communication.',
  },
};

const KEYWORD_MAP = [
  { key: 'water',     keywords: ['water', 'supply', 'pipeline', 'drinking', 'tap', 'bore'] },
  { key: 'youth',     keywords: ['youth', 'unemploy', 'job', 'employ', 'campus', 'college', 'engagement'] },
  { key: 'roads',     keywords: ['road', 'pothole', 'infrastructure', 'traffic', 'street', 'connectivity'] },
  { key: 'opposition',keywords: ['opposition', 'bnp', 'inc', 'rally', 'counter', 'rival', 'priya', 'mehta'] },
  { key: 'sentiment', keywords: ['sentiment', 'decline', 'drop', 'fall', 'mood', 'score'] },
  { key: 'booth',     keywords: ['booth', 'worker', 'coverage', 'contact', 'volunteer', 'voter contact', 'gap'] },
  { key: 'power',     keywords: ['power', 'electric', 'load shed', 'outage', 'tsecpdcl'] },
  { key: 'healthcare',keywords: ['health', 'hospital', 'medical', 'clinic', 'doctor'] },
  { key: 'drainage',  keywords: ['drain', 'flood', 'water log', 'monsoon', 'sewage'] },
  { key: 'rumour',    keywords: ['rumour', 'rumor', 'whatsapp', 'fake', 'narrative', 'disinform', 'spread'] },
];

export function generateStrategy(concern) {
  if (!concern) return STRATEGY_TEMPLATES.default;

  const text = `${concern.title || ''} ${concern.detail || ''}`.toLowerCase();
  for (const { key, keywords } of KEYWORD_MAP) {
    if (keywords.some(kw => text.includes(kw))) {
      return STRATEGY_TEMPLATES[key];
    }
  }
  return STRATEGY_TEMPLATES.default;
}

export function getGlobalNextBestAction(concerns) {
  if (!concerns?.length) return null;

  const RANK = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const top  = [...concerns].sort(
    (a, b) => (RANK[a.priority] ?? 9) - (RANK[b.priority] ?? 9)
  )[0];

  if (!top) return null;
  const strategy = generateStrategy(top);

  return {
    action:      strategy.nextBestAction,
    priority:    top.priority,
    zone:        top.zone,
    impactDesc:  strategy.impactDesc,
    issueTitle:  top.title,
    handlers:    strategy.handlers,
    confidence:  strategy.confidenceScore,
  };
}
