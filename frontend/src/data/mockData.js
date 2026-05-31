// ─── NETA.AI Mock Data ─────────────────────────────────────────────
// All data is hardcoded for Phase 1 client mockup presentation.

export const constituency = {
  name: 'Serilingampally',
  fullName: 'Serilingampally Assembly Constituency (AC-52)',
  state: 'Telangana',
  district: 'Rangareddy / GHMC',
  assemblyNumber: 'AC-52',
  type: 'State Assembly',
  totalVoters: 276434,
  maleVoters: 141982,
  femaleVoters: 133812,
  otherVoters: 640,
  totalBooths: 225,
  electionDate: '28 May 2027',
  daysToElection: 7,
  lastUpdated: '21 May 2026, 06:47 AM',
  areas: ['Kondapur', 'Madhapur', 'Hafeezpet', 'Miyapur', 'Lingampally', 'Chandanagar', 'JNTU', 'Nizampet', 'Gachibowli', 'Nallagandla'],
};

export const candidate = {
  name: 'Arjun Kumar Reddy',
  shortName: 'A.K. Reddy',
  initials: 'AR',
  party: 'Telangana Rashtra Party',
  partyShort: 'TRP',
  partyColor: '#f97316',
  caste: 'OBC (Yadav)',
  age: 52,
  profession: 'Former IAS Officer, Philanthropist',
  suitabilityScore: 82,
  incumbent: false,
  priorWins: 1,
  education: 'IAS, MA Political Science — JNU',
};

export const winProbability = {
  current: 67,
  yesterday: 64,
  weekAgo: 58,
  trend: [55, 57, 59, 58, 60, 62, 61, 63, 65, 64, 65, 66, 67, 67],
  trendLabels: ['May 7','8','9','10','11','12','13','14','15','16','17','18','19','20'],
  marginRange: { low: 9800, high: 16400 },
  confidence: 74,
  boothProjection: {
    fortress: 63,
    swing: 71,
    hostile: 91,
  },
};

export const alerts = [
  {
    id: 1,
    type: 'critical',
    agent: 'VICHARAK',
    time: '06:32 AM',
    message:
      'Win probability dropped 4 pts in North cluster booths (B031–B048) over last 48 hrs. Opposition rally at Balanagar yesterday caused sentiment shift. Ground pulse score fell from 3.9 → 3.1.',
    action: 'Schedule candidate visit to Ward 7, North Zone — today or tomorrow',
    actionDone: false,
  },
  {
    id: 2,
    type: 'warning',
    agent: 'VIVEK',
    time: '05:55 AM',
    message:
      'Opposition candidate Priya Mehta made unverified promise of ₹6,000/month unemployment allowance at Balanagar rally. Promise trending on local WhatsApp groups.',
    action: 'VANI generating counter-narrative draft — review in Content Hub',
    actionDone: false,
  },
  {
    id: 3,
    type: 'warning',
    agent: 'VANI',
    time: '05:30 AM',
    message:
      'Negative media coverage spiked yesterday. TOI Hyderabad and Deccan Chronicle covered opposition press conference. Our media sentiment: −0.34 (3-day low).',
    action: 'Issue press release on Chandanagar road project completion',
    actionDone: false,
  },
  {
    id: 4,
    type: 'critical',
    agent: 'VAYU',
    time: '04:15 AM',
    message:
      'Booth contact rate below 40% in 18 booths (East Zone: B091–B108). Campaign is 3 days behind contact schedule in this zone.',
    action: 'Redeploy 20 workers from West Zone to East Zone immediately',
    actionDone: false,
  },
  {
    id: 5,
    type: 'info',
    agent: 'VAYU',
    time: '03:48 AM',
    message:
      'Ground pulse score improved to 3.9/5 in South cluster (4-day high). Recent ₹12Cr road infrastructure announcement resonating strongly with voters in B061–B080.',
    action: null,
    actionDone: true,
  },
  {
    id: 6,
    type: 'info',
    agent: 'VISHLESHAN',
    time: '02:00 AM',
    message:
      'Daily model update complete. Win probability updated to 67% (+3 from yesterday). Key driver: improved SC/ST community sentiment in Central zone.',
    action: null,
    actionDone: true,
  },
];

// ─── 150 Booths ───────────────────────────────────────────────────
const ZONES = ['Central', 'North', 'South', 'East', 'West'];

const zoneStatusMap = {
  Central: ['fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','hostile','hostile','hostile','hostile'],
  North:   ['fortress','fortress','fortress','fortress','fortress','fortress','fortress','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','hostile','hostile','hostile','hostile','hostile','hostile','hostile'],
  South:   ['fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','fortress','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','hostile','hostile','hostile','hostile','hostile','hostile'],
  East:    ['fortress','fortress','fortress','fortress','swing','swing','swing','swing','swing','swing','swing','swing','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile','hostile'],
  West:    ['fortress','fortress','fortress','fortress','fortress','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','swing','hostile','hostile','hostile','hostile','hostile','hostile'],
};

const pannaPramukhNames = [
  'Ravi Shankar','Lakshmi Devi','Suresh Babu','Anitha Kumari','Venkat Rao',
  'Padmavathi','Krishnarao','Saritha','Naresh','Rekha','Srinivas','Usha',
  'Mahesh','Kavitha','Balaji','Geeta','Ramesh','Sudha','Prasad','Hema',
  'Kishore','Nirmala','Vijay','Asha','Sunder','Latha','Mohan','Priya',
  'Gopala','Meena','Kiran','Swathi','Ganesh','Radha','Arjun','Deepa',
  'Narayana','Jyothi','Satish','Vimala',
];

const topIssues = ['Water supply','Road connectivity','Unemployment','Power cuts','Healthcare','School quality','Drainage','Housing'];

const generateBoothVoters = (zone, idx) => {
  const bases = { Central: 1600, North: 1400, South: 1500, East: 1300, West: 1450 };
  return bases[zone] + (idx % 7) * 80 - 200;
};

export const booths = ZONES.flatMap((zone, zi) =>
  zoneStatusMap[zone].map((status, i) => {
    const id = zi * 30 + i + 1;
    const coverageThreshold = { Central: 0.88, North: 0.72, South: 0.80, East: 0.58, West: 0.78 };
    const covered = (i / 30) < coverageThreshold[zone];
    const baseShare = status === 'fortress' ? 58 : status === 'swing' ? 45 : 31;
    const jitter = ((id * 17 + i * 7) % 14) - 7;
    const pulseBase = status === 'fortress' ? 3.8 : status === 'swing' ? 3.3 : 2.7;
    const pulseJitter = ((id * 13) % 10) / 10 - 0.5;
    const pannaNamesFiltered = pannaPramukhNames.filter((_, ni) => ni % 5 === id % 5);
    return {
      id,
      code: `B${String(id).padStart(3,'0')}`,
      name: `Booth ${String(id).padStart(3,'0')} — ${zone} ${Math.ceil((i+1)/5)}`,
      zone,
      status,
      covered,
      voters: generateBoothVoters(zone, i),
      expectedVoteShare: Math.min(Math.max(baseShare + jitter, 20), 78),
      pulseScore: Math.round(Math.min(Math.max(pulseBase + pulseJitter, 1.5), 5.0) * 10) / 10,
      contactRate: covered ? Math.min(Math.max(30 + ((id * 11) % 65), 30), 95) : 0,
      pannaPramukh: covered ? pannaPramukhNames[(id * 3) % pannaPramukhNames.length] : null,
      workers: covered ? 2 + (id % 4) : 0,
      lastVisit: covered ? `May ${Math.max(1, 7 - (id % 6))}` : '—',
      topIssue: topIssues[id % topIssues.length],
      oppositionActivity: status === 'hostile' ? 'High' : status === 'swing' ? 'Medium' : 'Low',
    };
  })
);

// ─── Demographics ─────────────────────────────────────────────────
export const demographics = {
  // Serilingampally AC-52 — urban Cyberabad belt, Ranga Reddy / GHMC
  casteComposition: [
    { name: 'OBC (Yadav, Kuruma, Mudaliar)', value: 28, color: '#f97316' },
    { name: 'General / Upper Caste',          value: 20, color: '#3b82f6' },
    { name: 'Muslim',                          value: 22, color: '#8b5cf6' },
    { name: 'SC (Mala, Madiga)',               value: 14, color: '#10b981' },
    { name: 'ST (Lambada, Koya)',              value:  6, color: '#f59e0b' },
    { name: 'Christian / IT Migrant / Other',  value: 10, color: '#6b7280' },
  ],
  economicStrata: [
    { name: 'BPL (Below Poverty Line)', value: 18 },
    { name: 'Lower Middle',             value: 29 },
    { name: 'Middle',                   value: 30 },
    { name: 'Upper Middle',             value: 16 },
    { name: 'Upper (IT/Professional)',  value:  7 },
  ],
  ageGroups: [
    { name: '18–25 (First voters)', value: 22 },
    { name: '26–35 (IT workforce)', value: 28 },
    { name: '36–50',                value: 28 },
    { name: '51–65',                value: 15 },
    { name: '65+',                   value:  7 },
  ],
  gender: { male: 51, female: 48, other: 1 },
  literacy: 82,
  urbanRural: { urban: 89, semiUrban: 9, rural: 2 },
  keyInfluencers: [
    { name: 'Haji Mohammed Bashir', role: 'Head, Muslim Welfare Board', community: 'Muslim', alignment: 'Neutral' },
    { name: 'Swami Ramananda',       role: 'Temple Trust Chairman',       community: 'General', alignment: 'Friendly' },
    { name: 'Narsimha Rao Yadav',    role: 'OBC Federation Leader',        community: 'OBC',    alignment: 'Friendly' },
    { name: 'Dr. Sulochana Bai',     role: 'SC Welfare Association',       community: 'SC',     alignment: 'Neutral' },
    { name: 'Smt. Padma Lakshmi',    role: 'Women SHG Network Head',       community: 'Mixed',  alignment: 'Friendly' },
    { name: 'Raju Goud',             role: 'Trade Union Leader (APSRTC)',   community: 'OBC',    alignment: 'Hostile' },
  ],
};

// ─── Historical Results ───────────────────────────────────────────
export const historicalResults = [
  {
    year: 2023,
    winner: 'TRS (Incumbent)',
    winnerVotes: 92400,
    ourVotes: 78100,
    margin: -14300,
    turnout: 68.4,
    ourShare: 31.4,
    result: 'Loss',
  },
  {
    year: 2018,
    winner: 'TRS (Incumbent)',
    winnerVotes: 88200,
    ourVotes: 75600,
    margin: -12600,
    turnout: 71.2,
    ourShare: 30.4,
    result: 'Loss',
  },
  {
    year: 2014,
    winner: 'Congress',
    winnerVotes: 81000,
    ourVotes: 68500,
    margin: -12500,
    turnout: 65.8,
    ourShare: 29.3,
    result: 'Loss',
  },
];

export const swingAnalysis = [
  { zone: 'Central',  currentShare: 58, lastElectionShare: 52, swing: '+6', direction: 'up' },
  { zone: 'North',    currentShare: 45, lastElectionShare: 48, swing: '-3', direction: 'down' },
  { zone: 'South',    currentShare: 53, lastElectionShare: 49, swing: '+4', direction: 'up' },
  { zone: 'East',     currentShare: 34, lastElectionShare: 37, swing: '-3', direction: 'down' },
  { zone: 'West',     currentShare: 48, lastElectionShare: 44, swing: '+4', direction: 'up' },
];

// ─── Issue Matrix ─────────────────────────────────────────────────
export const issueMatrix = [
  { rank: 1, issue: 'Drinking Water Supply', salience: 88, sentiment: -0.62, communities: 'All', ourPosition: 'Strong', riskLevel: 'low', recommendation: 'Commit to 24/7 piped water in all wards within 18 months. Announce contractor name.' },
  { rank: 2, issue: 'Road Connectivity & Pothole Repair', salience: 81, sentiment: -0.48, communities: 'All', ourPosition: 'Strong', riskLevel: 'low', recommendation: 'Leverage ₹12Cr road project — show progress photos. Commit remaining 3 km by Dec 2026.' },
  { rank: 3, issue: 'Youth Unemployment', salience: 76, sentiment: -0.71, communities: 'Youth (18–35)', ourPosition: 'Developing', riskLevel: 'medium', recommendation: 'Announce IT park partnership for 2,000 jobs. Candidate\'s IAS background makes this credible.' },
  { rank: 4, issue: 'Power Cuts (4–6 hrs daily)', salience: 72, sentiment: -0.55, communities: 'All', ourPosition: 'Weak', riskLevel: 'high', recommendation: 'Do NOT make a promise we cannot keep. Commit to escalation to TSECPDCL leadership. Risk: opponent already promised 24-hr power.' },
  { rank: 5, issue: 'Primary Healthcare Access', salience: 64, sentiment: -0.42, communities: 'Women, Seniors', ourPosition: 'Developing', riskLevel: 'medium', recommendation: 'Commit to 2 new urban health sub-centres. Partner with private hospital for free diagnostics camp.' },
  { rank: 6, issue: 'Government School Quality', salience: 59, sentiment: -0.38, communities: 'SC/ST, BPL', ourPosition: 'Neutral', riskLevel: 'low', recommendation: 'Commit to smart classroom upgrades in 5 government schools. Aligns well with SC/ST voter base.' },
  { rank: 7, issue: 'Drainage & Flooding (Monsoon)', salience: 54, sentiment: -0.44, communities: 'Low-income areas', ourPosition: 'Neutral', riskLevel: 'medium', recommendation: 'Promise storm-water drain project for wards 4 and 9. Get engineer to validate feasibility first.' },
  { rank: 8, issue: 'Affordable Housing', salience: 47, sentiment: -0.29, communities: 'BPL, Migrants', ourPosition: 'Weak', riskLevel: 'high', recommendation: 'Do not over-promise. Refer to state housing scheme enrollment — safer ground.' },
];

// ─── Candidate Suitability ────────────────────────────────────────
export const candidateScoring = {
  overall: 82,
  breakdown: [
    { factor: 'Caste Fit (OBC in OBC-majority constituency)', score: 90 },
    { factor: 'Professional Credibility (Ex-IAS)', score: 95 },
    { factor: 'Media Presence & Likability', score: 74 },
    { factor: 'Community Relations (Ground reputation)', score: 78 },
    { factor: 'Incumbency Advantage', score: 40 },
    { factor: 'Financial Health (EC declaration clean)', score: 92 },
    { factor: 'No Criminal Cases', score: 100 },
    { factor: 'Age Profile (52, peak credibility)', score: 85 },
    { factor: 'Alliance Support', score: 80 },
    { factor: 'Social Media Reach', score: 62 },
  ],
  vsOpposition: [
    { factor: 'Caste Alignment', ours: 90, theirs: 65 },
    { factor: 'Credibility', ours: 95, theirs: 58 },
    { factor: 'Media Presence', ours: 74, theirs: 88 },
    { factor: 'Community Reach', ours: 78, theirs: 72 },
    { factor: 'Party Machinery', ours: 80, theirs: 85 },
  ],
  redFlags: [],
  greenFlags: ['Clean criminal record', 'IAS career gives development credibility', 'OBC-Yadav caste aligns with 32% voter base', 'Alliance with local trade body secured'],
};

// ─── Ground Pulse Data ────────────────────────────────────────────
export const groundPulse = {
  today: {
    overallMood: 3.7,
    totalReports: 342,
    timestamp: '21 May 2026, 05:00 AM',
  },
  moodTrend: [
    { date: 'Apr 24', score: 3.3 }, { date: 'Apr 25', score: 3.4 },
    { date: 'Apr 26', score: 3.2 }, { date: 'Apr 27', score: 3.5 },
    { date: 'Apr 28', score: 3.6 }, { date: 'Apr 29', score: 3.7 },
    { date: 'Apr 30', score: 3.5 }, { date: 'May 1',  score: 3.8 },
    { date: 'May 2',  score: 3.7 }, { date: 'May 3',  score: 3.9 },
    { date: 'May 4',  score: 3.8 }, { date: 'May 5',  score: 3.6 },
    { date: 'May 6',  score: 3.5 }, { date: 'May 7',  score: 3.7 },
  ],
  zoneMood: [
    { zone: 'Central', score: 4.1, reports: 82, trend: 'up',   sentiment: 'Positive' },
    { zone: 'North',   score: 3.1, reports: 71, trend: 'down', sentiment: 'Declining' },
    { zone: 'South',   score: 3.9, reports: 68, trend: 'up',   sentiment: 'Positive' },
    { zone: 'East',    score: 2.9, reports: 54, trend: 'flat', sentiment: 'Weak' },
    { zone: 'West',    score: 3.8, reports: 67, trend: 'up',   sentiment: 'Improving' },
  ],
  topIssuesToday: [
    { issue: 'Drinking Water',     count: 234, pct: 68 },
    { issue: 'Unemployment',       count: 189, pct: 55 },
    { issue: 'Road Potholes',      count: 167, pct: 49 },
    { issue: 'Power Cuts',         count: 143, pct: 42 },
    { issue: 'Opposition Promises',count: 118, pct: 35 },
    { issue: 'Healthcare',         count:  94, pct: 27 },
  ],
  oppositionObserved: [
    { zone: 'North',   activity: 'Large rally at Balanagar Chowk (est. 1,200 attendees)', severity: 'high' },
    { zone: 'East',    activity: 'Door-to-door campaign in B091–B100 with free materials', severity: 'medium' },
    { zone: 'Central', activity: 'Rumour spread on WhatsApp: "AK Reddy will not deliver"', severity: 'medium' },
    { zone: 'West',    activity: 'INC candidate distributed free bags in B135 area', severity: 'low' },
  ],
  rumours: [
    { rumour: '"Arjun Reddy only cares about upper castes"', status: 'Counter needed', zone: 'North' },
    { rumour: '"TRP will get only 40 seats — no use voting for them"', status: 'Counter needed', zone: 'East' },
    { rumour: '"Opposition will give ₹6,000/month to all youth"', status: 'Counter ready', zone: 'North' },
  ],
  fieldReports: [
    { id: 1, booth: 'B007', worker: 'Suresh Babu', time: '07:30 PM', mood: 4, issue: 'Water supply', oppoActivity: 'None', note: 'Positive response to road work update. 5 voters pledged support.' },
    { id: 2, booth: 'B035', worker: 'Lakshmi Devi', time: '07:15 PM', mood: 3, issue: 'Unemployment', oppoActivity: 'BNP posters pasted overnight', note: 'Youth group asking about job creation. Need candidate visit.' },
    { id: 3, booth: 'B062', worker: 'Venkat Rao', time: '06:55 PM', mood: 4, issue: 'Road quality', oppoActivity: 'None', note: 'Road project announcement very well received. Area mood improved.' },
    { id: 4, booth: 'B091', worker: 'Anitha Kumari', time: '06:30 PM', mood: 2, issue: 'Power cuts', oppoActivity: 'BNP door-to-door ongoing', note: 'Hostile reception. 3 voters expressed preference for opposition. Contact rate too low.' },
    { id: 5, booth: 'B108', worker: 'Ravi Shankar', time: '06:00 PM', mood: 2, issue: 'Drainage', oppoActivity: 'INC materials distributed', note: 'Old drainage complaint unresolved for 3 years. Very frustrated voters.' },
    { id: 6, booth: 'B122', worker: 'Padmavathi', time: '05:45 PM', mood: 4, issue: 'Healthcare', oppoActivity: 'None', note: 'Women SHG meeting went well. 22 women committed to vote.' },
    { id: 7, booth: 'B143', worker: 'Naresh', time: '05:30 PM', mood: 3, issue: 'Unemployment', oppoActivity: 'None', note: 'Youth engagement moderate. Promise of IT park got positive reaction.' },
    { id: 8, booth: 'B015', worker: 'Krishnarao', time: '05:00 PM', mood: 5, issue: 'None', oppoActivity: 'None', note: 'Fortress booth. All 28 panna voters confirmed. Strong support.' },
  ],
};

// ─── Media Monitoring ─────────────────────────────────────────────
export const mediaMonitoring = {
  overallSentiment: -0.12,
  sentimentTrend: [
    { date: 'May 1',  ours: 0.21,  oppo: -0.15 },
    { date: 'May 2',  ours: 0.18,  oppo: -0.18 },
    { date: 'May 3',  ours: 0.05,  oppo: 0.10 },
    { date: 'May 4',  ours: -0.08, oppo: 0.22 },
    { date: 'May 5',  ours: -0.14, oppo: 0.31 },
    { date: 'May 6',  ours: -0.34, oppo: 0.28 },
    { date: 'May 7',  ours: -0.12, oppo: 0.18 },
  ],
  coverageVolume: { ours: 47, opposition: 68, neutral: 29 },
  recentCoverage: [
    { outlet: 'Deccan Chronicle', headline: 'BNP\'s Priya Mehta launches "Rozgar Guarantee" at packed rally', sentiment: 'positive_oppo', time: '3h ago' },
    { outlet: 'Times of India (Hyd)', headline: 'Chandanagar development projects face delay accusations', sentiment: 'negative_ours', time: '5h ago' },
    { outlet: 'Eenadu', headline: 'ఛందన్నగర్ నీటి సరఫరా సమస్యపై రెడ్డి వాగ్దానం', sentiment: 'positive_ours', time: '8h ago' },
    { outlet: 'Sakshi TV', headline: 'అర్జున్ రెడ్డి మహిళా బృందాలతో సమావేశం', sentiment: 'positive_ours', time: '10h ago' },
    { outlet: 'The Hans India', headline: 'TRP faces headwinds in North Chandanagar, poll sources say', sentiment: 'negative_ours', time: '14h ago' },
  ],
};

// ─── Opposition Candidates ────────────────────────────────────────
export const oppositionCandidates = [
  {
    id: 1,
    name: 'Priya Mehta',
    initials: 'PM',
    party: 'Bharatiya Nayak Party',
    partyShort: 'BNP',
    partyColor: '#f97316',
    age: 44,
    caste: 'General (Khatri)',
    profession: 'Businesswoman, Former Corporator',
    incumbent: false,
    winProbability: 24,
    threatLevel: 'High',
    avatar_bg: '#be185d',
    strengths: ['Active social media presence', 'Well-funded campaign', 'Women voter appeal', 'Strong in North & East zones'],
    weaknesses: ['No governance track record', 'Caste mismatch with OBC majority', 'Questionable land deal (pending probe)', 'External candidate — not from constituency'],
    recentPromises: [
      { promise: '₹6,000/month unemployment allowance for youth', feasibility: 'Low', ourResponse: 'State budget constraint — impossible without Centre support' },
      { promise: 'Free electricity up to 300 units', feasibility: 'Medium', ourResponse: 'Already a state scheme — taking credit for existing policy' },
      { promise: 'New hospital in North Zone within 6 months', feasibility: 'Very Low', ourResponse: 'Hospital construction takes 3–5 years minimum — ask for blueprint' },
    ],
    recentActivity: [
      { date: 'May 6', event: 'Mega rally at Balanagar — est. 1,200 attendees', zone: 'North' },
      { date: 'May 5', event: 'Press conference at BNP HQ on "TRP corruption"', zone: 'City' },
      { date: 'May 4', event: 'Door-to-door campaign in East Zone (B091–B110)', zone: 'East' },
      { date: 'May 3', event: 'Women\'s meet at Chandanagar Community Hall', zone: 'Central' },
    ],
    criminalCases: 0,
    ecFilingIssues: 'Pending — land deal query',
    vulnerabilities: 'Land encroachment controversy in 2023 (documented, media has evidence)',
  },
  {
    id: 2,
    name: 'Suresh Kumar Pillai',
    initials: 'SK',
    party: 'Indian National Congress (Telangana)',
    partyShort: 'INC',
    partyColor: '#3b82f6',
    age: 61,
    caste: 'SC (Mala)',
    profession: 'Retired Teacher, Long-time party worker',
    incumbent: false,
    winProbability: 9,
    threatLevel: 'Low',
    avatar_bg: '#1d4ed8',
    strengths: ['SC community loyalty', 'Long-standing local presence', 'Gandhi family connection', 'Clean image'],
    weaknesses: ['Weak party machinery post-2018', 'Poor funding', 'Limited social media', 'Low youth appeal'],
    recentPromises: [
      { promise: 'MGNREGA expansion to urban areas', feasibility: 'Medium', ourResponse: 'Good policy — we agree. But INC had power for 10 years and didn\'t do it.' },
      { promise: 'SC student scholarship enhancement', feasibility: 'High', ourResponse: 'TRP has already committed ₹20,000/year scholarship — we go further' },
    ],
    recentActivity: [
      { date: 'May 6', event: 'Small meeting with SC elders at Ambedkar statue', zone: 'East' },
      { date: 'May 4', event: 'Road show through Central markets', zone: 'Central' },
    ],
    criminalCases: 0,
    ecFilingIssues: 'None',
    vulnerabilities: 'Vote split risk: may pull SC votes from us; minimal threat to BNP',
  },
];

// ─── Workers ──────────────────────────────────────────────────────
export const workerSummary = {
  total: 450,
  active: 342,
  onLeave: 24,
  inactive: 84,
  boothsCovered: 112,
  boothsUncovered: 38,
  avgContactRate: 68,
  topPerformers: [
    { name: 'Suresh Babu',  zone: 'Central', boothsManaged: 3, votersContacted: 287, rating: 5 },
    { name: 'Lakshmi Devi', zone: 'South',   boothsManaged: 2, votersContacted: 241, rating: 5 },
    { name: 'Venkat Rao',   zone: 'West',    boothsManaged: 4, votersContacted: 312, rating: 5 },
    { name: 'Padmavathi',   zone: 'West',    boothsManaged: 2, votersContacted: 198, rating: 4 },
  ],
};

// ─── Content Queue ────────────────────────────────────────────────
export const contentQueue = [
  {
    id: 1, type: 'Social Media',
    title: 'Counter: BNP "Rozgar Guarantee" Claim',
    agent: 'VANI', status: 'pending_approval',
    platform: 'Twitter/X + Facebook',
    preview: '"₹6,000/month sounds great. But Telangana\'s total annual budget is ₹2.9 lakh crore. Do the math: BNP promise costs ₹18,000 crore/month. Where is the money? #FactCheck #Chandanagar"',
    createdAt: '06:01 AM',
    urgency: 'high',
  },
  {
    id: 2, type: 'Press Release',
    title: 'Chandanagar Road Project Phase 2 Completion',
    agent: 'VANI', status: 'pending_approval',
    platform: 'All Media',
    preview: 'FOR IMMEDIATE RELEASE: Arjun Kumar Reddy today announced the completion of 8.2 km of road infrastructure in Chandanagar assembly constituency under the ₹12 crore HMDA-funded...',
    createdAt: '04:30 AM',
    urgency: 'medium',
  },
  {
    id: 3, type: 'WhatsApp Forward',
    title: 'Morning Motivation — Candidate Message (Telugu)',
    agent: 'VANI', status: 'pending_approval',
    platform: 'WhatsApp Worker Network',
    preview: 'నమస్కారం! మన చందన్నగర్ ప్రజలకు — మీ నమ్మకమే నా శక్తి. రేపటి మన నీళ్ళ సమస్య పరిష్కారానికి నేను నిబద్ధుడిని. — అర్జున్ రెడ్డి',
    createdAt: '03:15 AM',
    urgency: 'medium',
  },
  {
    id: 4, type: 'Speech Brief',
    title: 'North Zone Rally Brief — 8 May 2026',
    agent: 'VANI', status: 'draft',
    platform: 'Internal — Candidate',
    preview: 'Rally at Balanagar Sports Ground. Audience: ~800 (largely youth 18–35, significant OBC + Muslim mix). Key concerns: unemployment, power cuts. Tone: assertive, aspirational...',
    createdAt: '02:00 AM',
    urgency: 'high',
  },
];

// ─── Agents Status ────────────────────────────────────────────────
export const agentStatus = [
  { id: 'VAYU',       name: 'VAYU',       role: 'Ground Intelligence',     color: '#10b981', bg: '#064e3b', status: 'active', lastAction: 'Aggregated 342 field reports',         activity: '05:00 AM' },
  { id: 'VANI',       name: 'VANI',       role: 'Communications',           color: '#3b82f6', bg: '#1e3a5f', status: 'active', lastAction: 'Generated 4 content drafts',            activity: '06:01 AM' },
  { id: 'VIVEK',      name: 'VIVEK',      role: 'Opposition Research',       color: '#8b5cf6', bg: '#3b1f6e', status: 'active', lastAction: 'Monitoring 2 opponent social accounts', activity: '05:55 AM' },
  { id: 'VISHLESHAN', name: 'VISHLESHAN', role: 'Analytics & Prediction',    color: '#f59e0b', bg: '#451a03', status: 'active', lastAction: 'Updated win probability to 67%',        activity: '02:00 AM' },
  { id: 'VICHAR',     name: 'VICHAR',     role: 'Strategy & Manifesto',      color: '#ec4899', bg: '#500724', status: 'standby', lastAction: 'Manifesto v2 awaiting review',         activity: '22:00 PM' },
  { id: 'VICHARAK',   name: 'VICHARAK',   role: 'Course Correction & Alerts',color: '#ef4444', bg: '#450a0a', status: 'active', lastAction: 'Issued 2 critical alerts',              activity: '06:32 AM' },
];

// ─── Candidate Daily Brief ────────────────────────────────────────
export const candidateBrief = {
  date: '21 May 2026 — Thursday',
  greeting: 'Good morning, Arjun ji.',
  winProbability: 67,
  winTrend: '+3 from yesterday',
  positives: [
    'South Zone ground pulse at 3.9/5 — voters responding to road project announcement.',
    'SC/ST community sentiment improved by 12 pts over last week in Central zone.',
    'VANI counter-narrative on water supply promise performing well — 2,400 shares on WhatsApp.',
  ],
  concerns: [
    'North Zone (Balanagar cluster) sentiment fell sharply after BNP rally yesterday. Needs your presence — today or tomorrow at the latest.',
    'East Zone booth contact rate still below 40% in 18 booths. Workers need direction.',
  ],
  agenda: [
    {
      time: '8:00 AM',
      event: 'Meeting with OBC Federation Leaders',
      location: 'Campaign Office, Serilingampally',
      prep: 'Narsimha Rao Yadav is the key person. Emphasise OBC quota protection and the IT park jobs initiative. Ask for active mobilisation in Central and West zones.',
      type: 'Community',
    },
    {
      time: '11:00 AM',
      event: 'Road Project Inauguration (Phase 2)',
      location: 'Main Road Junction, Ward 6, South Zone',
      prep: 'Speak for 12–15 minutes max. Key message: "₹12 crore delivered — not promised, DELIVERED." Bring project engineer for photo op. Press will be there.',
      type: 'Public Event',
    },
    {
      time: '4:00 PM',
      event: 'Women\'s SHG Network Meet',
      location: 'Mahila Samajam Hall, West Zone',
      prep: 'Audience: 80+ women, SHG leaders. Key ask: their vote + mobilise 10 other women each. Emphasise healthcare sub-centre promise. Smt. Padma Lakshmi will introduce you — acknowledge her work.',
      type: 'Community',
    },
    {
      time: '7:00 PM',
      event: 'North Zone Street Corner Meetings (3 locations)',
      location: 'Balanagar, Hafeezpet, Pragathi Nagar',
      prep: 'Critical: counter BNP rally momentum from last night. Stick to water supply, road work proof. Do NOT mention ₹6,000 promise — it elevates it. Youth in audience — mention IT park jobs. Keep it sharp, 8 minutes per spot.',
      type: 'Rally',
    },
  ],
  keyMessage: '"Serilingampally ka paani, sadak, rozgar — teen kaam, ek naam: Arjun Kumar Reddy. Maine kaha, maine kiya."',
  whoToThank: [
    'Smt. Padma Lakshmi — Women SHG Network (publicly at evening meeting)',
    'Suresh Babu — Top ground worker, 287 voters contacted this week',
  ],
  thingsToAvoid: [
    'Do not engage with BNP\'s ₹6,000 promise directly — it gives it oxygen.',
    'Do not comment on Priya Mehta\'s land deal case — let media handle it.',
    'Do not commit on power cuts — we cannot deliver that promise.',
  ],
};

// ─── Prediction model factor weights ────────────────────────────
export const predictionFactors = [
  { factor: 'Historical Voting Pattern',   weight: 25, currentScore: 68, impact: 'positive' },
  { factor: 'Ground Pulse Sentiment',      weight: 22, currentScore: 72, impact: 'positive' },
  { factor: 'Caste / Community Arithmetic',weight: 18, currentScore: 75, impact: 'positive' },
  { factor: 'Opposition Strength',         weight: 12, currentScore: 38, impact: 'negative' },
  { factor: 'Social Media Sentiment',      weight: 10, currentScore: 44, impact: 'neutral' },
  { factor: 'Voter Contact Rate',          weight:  8, currentScore: 68, impact: 'positive' },
  { factor: 'Media Coverage Sentiment',    weight:  5, currentScore: 35, impact: 'negative' },
];

// ─── AI Intelligence Brief (VICHARAK) ────────────────────────
export const aiIntelligenceBrief = {
  text: `Win probability stands at 67% (+3 pts from yesterday), driven by SC/ST sentiment recovery in Central Zone (+12 pts this week). However, North Zone is critically exposed after BNP's Balanagar rally — ground pulse in B031–B048 dropped from 3.9 → 3.1 in 48 hours.

The 18-booth East Zone contact deficit remains the highest-priority operational gap: 3 days behind schedule at current worker deployment. Voter contact below 40% in those booths means we are not in the conversation with ~27,000 voters.

Watch: BNP's ₹6,000/month youth allowance promise is spreading on WhatsApp groups. VANI counter-narrative is ready but needs candidate endorsement. Every 24-hour delay allows the claim to embed further into voter memory.`,
  generated_at: '09:58 AM · 21 May 2026',
  agent: 'VICHARAK',
};

// ─── Campaign Recommendations (VISHLESHAN) ───────────────────
export const campaignRecommendations = [
  {
    priority: 'critical',
    action: 'Candidate to North Zone tonight — 3 corner meetings',
    detail: 'Balanagar, Hafeezpet, Pragathi Nagar. Mood at 3.1/5 and falling. BNP rally momentum must be countered within 24 hours or the zone tips hostile.',
    eta: 'By 7:00 PM today',
  },
  {
    priority: 'critical',
    action: 'Redeploy 20 workers from West → East Zone now',
    detail: '18 East Zone booths below 40% contact rate. West Zone is above target and can absorb the loss. Deploy before noon to close the gap.',
    eta: 'Before 12:00 noon',
  },
  {
    priority: 'high',
    action: 'Approve VANI counter-narrative on BNP promise',
    detail: 'WhatsApp fact-check content ready — shows state budget impossibility of ₹6,000/month. Candidate endorsement needed to authorise distribution on worker network.',
    eta: 'Before noon today',
  },
  {
    priority: 'medium',
    action: 'SC/ST consolidation event in Central Zone',
    detail: 'Sentiment up 12 pts — lock in the gain with a targeted community engagement. A temple or community hall meeting with 50+ attendees is sufficient.',
    eta: 'Within 3 days',
  },
];

// ─── Zone Sentiment ───────────────────────────────────────────
export const zoneSentiment = [
  { zone: 'South',   score: 78, delta: +5,  trend: 'up',   status: 'strong',   booths: 28 },
  { zone: 'Central', score: 71, delta: +12, trend: 'up',   status: 'good',     booths: 32 },
  { zone: 'West',    score: 65, delta:  0,  trend: 'flat', status: 'moderate', booths: 31 },
  { zone: 'East',    score: 52, delta: -3,  trend: 'down', status: 'weak',     booths: 29 },
  { zone: 'North',   score: 38, delta: -13, trend: 'down', status: 'critical', booths: 30 },
];

// ─── Booth Performance ────────────────────────────────────────
export const boothPerformance = {
  total: 225, covered: 178, weak: 34, strong: 101,
  volunteerAttendance: 81, outreachCompletion: 67,
  voterContactToday: 5130, voterContactTarget: 7650,
  lastUpdated: '09:30 AM',
};

// ─── Operational Concerns (structured for ActionableConcernCard) ──────
export const operationalConcerns = [
  {
    id: 'oc-1', priority: 'HIGH',
    title: 'North Zone sentiment decline',
    detail: 'Ground pulse dropped 3.9→3.1 after opposition rally at Balanagar. Booths B031–B048 showing fastest decline. If unaddressed within 24 hrs, zone risks flipping hostile.',
    action: 'Candidate visit tonight — 3 corner meetings at Balanagar, Hafeezpet, Pragathi Nagar',
    team: 'Ground Team Alpha', deadline: 'Before 8:00 PM today', zone: 'North', status: 'Pending',
  },
  {
    id: 'oc-2', priority: 'HIGH',
    title: 'East Zone voter contact gap',
    detail: '18 booths at sub-40% contact rate — 3 days behind schedule. ~27,000 voters not yet reached. West Zone is above target and can absorb redeployment.',
    action: 'Redeploy 20 workers from West Zone to East before noon',
    team: 'Operations Cell', deadline: 'Before 12:00 noon', zone: 'East', status: 'In Progress',
  },
  {
    id: 'oc-3', priority: 'MEDIUM',
    title: 'Counter-narrative approval pending',
    detail: 'VANI WhatsApp fact-check content ready — waiting candidate sign-off. Every 24-hr delay allows opposition claim to embed further in voter memory.',
    action: 'Review and approve VANI counter-narrative draft in Content Hub',
    team: 'VANI Cell', deadline: 'Before noon today', zone: 'All', status: 'Awaiting Approval',
  },
];

// ─── Key Message Translations ─────────────────────────────────
export const keyMessageTranslations = {
  hi: 'Serilingampally ka paani, sadak, rozgar — teen kaam, ek naam: Arjun Kumar Reddy. Maine kaha, maine kiya.',
  en: "Serilingampally's water, roads, employment — three works, one name: Arjun Kumar Reddy. I promised it. I delivered it.",
  te: 'సేరిలింగంపల్లికి నీరు, రోడ్లు, ఉపాధి — మూడు పనులు, ఒక పేరు: అర్జున్ కుమార్ రెడ్డి. నేను చెప్పాను, నేను చేశాను.',
};

// ─── Enhanced Positives ───────────────────────────────────────
export const enhancedPositives = [
  { text: 'South Zone ground pulse at 3.9/5 — voters responding strongly to road project delivery', growth: '+8', unit: '% sentiment', zone: 'South' },
  { text: 'SC/ST community sentiment improved by 12 pts over the last week in Central Zone', growth: '+12', unit: 'pts', zone: 'Central' },
  { text: 'VANI counter-narrative performing well — 2,400+ shares on WhatsApp networks', growth: '+2,400', unit: 'shares', zone: 'All' },
];

// ─── Executive Dashboard Widgets — demo data ─────────────────
export const executiveDashboardWidgets = {
  priorityAlerts: [
    {
      id: 'ew-1',
      title: 'North Zone Voter Contact Below Target',
      priority: 'HIGH',
      summary: '18 booths in the East-North cluster are at sub-40% contact rate — 3 days behind schedule. Approximately 27,000 voters have not yet been personally reached.',
      action: 'Redeploy 20 workers from over-staffed West Zone to East Zone before noon today.',
      timestamp: '07:15 AM',
    },
  ],
  operations: {
    title: 'Ground Operations Status',
    subtitle: 'Worker deployment & voter contact by zone',
    lastUpdated: '09:30 AM',
    zones: [
      { zone: 'North',   workers: 8,  contactRate: 41, target: 75, status: 'critical' },
      { zone: 'East',    workers: 6,  contactRate: 55, target: 75, status: 'at-risk' },
      { zone: 'Central', workers: 11, contactRate: 79, target: 75, status: 'on-track' },
      { zone: 'West',    workers: 15, contactRate: 87, target: 75, status: 'above-target' },
      { zone: 'South',   workers: 12, contactRate: 83, target: 75, status: 'above-target' },
    ],
  },
  briefingPoints: {
    title: 'Evening Campaign Talking Points',
    subtitle: "Key messages for tonight's public engagements",
    points: [
      'Road project Phase 2 complete — ₹12 crore delivered, not promised',
      'Healthcare sub-centre: groundbreaking confirmed for next month',
      'IT park initiative: 800 local jobs, applications open June 1',
      'Voter contact milestone: 1,87,000 of 2,48,000 voters personally reached',
      'South Zone sentiment at 3.9/5 — acknowledge community response to development work',
    ],
  },
  recommendation: {
    title: 'Strategic Assessment',
    priority: 'HIGH',
    insight: 'Win probability at 67% is stable but North Zone exposure is the primary risk variable for the next 72 hours. Direct candidate presence tonight will arrest the sentiment slide. East Zone contact gap must close by May 10 to protect the margin projection.',
    actions: [
      { label: 'Candidate to 3 North Zone corner meetings tonight', urgency: 'critical' },
      { label: 'Redeploy 20 workers West → East before noon', urgency: 'critical' },
      { label: 'Approve VANI counter-narrative for WhatsApp distribution', urgency: 'high' },
    ],
  },
};

// ─── Worker Details ───────────────────────────────────────────
export const workerDetails = [
  { id: 1,  name: 'Venkat Rao',    zone: 'West',    booths: 4, voters: 312, rate: 87, status: 'active', lastSeen: '9:45 AM',  rating: 5 },
  { id: 2,  name: 'Suresh Babu',   zone: 'Central', booths: 3, voters: 287, rate: 91, status: 'active', lastSeen: '9:30 AM',  rating: 5 },
  { id: 3,  name: 'Lakshmi Devi',  zone: 'South',   booths: 2, voters: 241, rate: 83, status: 'active', lastSeen: '9:15 AM',  rating: 5 },
  { id: 4,  name: 'Padmavathi',    zone: 'West',    booths: 2, voters: 198, rate: 79, status: 'active', lastSeen: '8:50 AM',  rating: 4 },
  { id: 5,  name: 'Krishnarao',    zone: 'Central', booths: 3, voters: 176, rate: 74, status: 'active', lastSeen: '8:30 AM',  rating: 4 },
  { id: 6,  name: 'Saritha',       zone: 'South',   booths: 2, voters: 164, rate: 70, status: 'active', lastSeen: '8:15 AM',  rating: 4 },
  { id: 7,  name: 'Naresh',        zone: 'North',   booths: 3, voters: 142, rate: 58, status: 'active', lastSeen: '8:00 AM',  rating: 3 },
  { id: 8,  name: 'Rekha',         zone: 'Central', booths: 2, voters: 138, rate: 69, status: 'active', lastSeen: '7:45 AM',  rating: 4 },
  { id: 9,  name: 'Ravi Shankar',  zone: 'East',    booths: 2, voters: 98,  rate: 41, status: 'active', lastSeen: '7:30 AM',  rating: 3 },
  { id: 10, name: 'Anitha Kumari', zone: 'East',    booths: 2, voters: 87,  rate: 36, status: 'active', lastSeen: '7:15 AM',  rating: 2 },
  { id: 11, name: 'Srinivas',      zone: 'South',   booths: 2, voters: 156, rate: 73, status: 'active', lastSeen: '8:05 AM',  rating: 4 },
  { id: 12, name: 'Usha',          zone: 'North',   booths: 2, voters: 121, rate: 52, status: 'active', lastSeen: '7:50 AM',  rating: 3 },
];

// ─── Ground Pulse — Extended Intelligence Data ────────────────

export const zoneSentimentDetail = [
  { zone: 'South',   positive: 78, neutral: 14, negative:  8, swing: 12, score: 3.9, delta: +5,  trend: 'up',   risk: 'low',      booths: 28, reports: 68 },
  { zone: 'Central', positive: 71, neutral: 16, negative: 13, swing: 18, score: 4.1, delta: +12, trend: 'up',   risk: 'low',      booths: 32, reports: 82 },
  { zone: 'West',    positive: 65, neutral: 21, negative: 14, swing: 22, score: 3.8, delta:  0,  trend: 'flat', risk: 'medium',   booths: 31, reports: 67 },
  { zone: 'East',    positive: 52, neutral: 22, negative: 26, swing: 28, score: 2.9, delta: -3,  trend: 'down', risk: 'high',     booths: 29, reports: 54 },
  { zone: 'North',   positive: 38, neutral: 20, negative: 42, swing: 31, score: 3.1, delta: -13, trend: 'down', risk: 'critical', booths: 30, reports: 71 },
];

export const issueHeatmap = [
  { issue: 'Drinking Water',   count: 234, pct: 68, trend: 'up',   urgency: 'CRITICAL', delta: +34, zones: ['East', 'North', 'Central'] },
  { issue: 'Unemployment',     count: 189, pct: 55, trend: 'up',   urgency: 'HIGH',     delta: +18, zones: ['North', 'West', 'East'] },
  { issue: 'Road Potholes',    count: 167, pct: 49, trend: 'flat', urgency: 'MEDIUM',   delta:  +2, zones: ['South', 'West', 'Central'] },
  { issue: 'Power Cuts',       count: 143, pct: 42, trend: 'up',   urgency: 'HIGH',     delta: +21, zones: ['East', 'North'] },
  { issue: 'Drainage',         count: 112, pct: 33, trend: 'up',   urgency: 'HIGH',     delta: +28, zones: ['East', 'South'] },
  { issue: 'Healthcare',       count:  94, pct: 27, trend: 'flat', urgency: 'MEDIUM',   delta:  -4, zones: ['West', 'Central'] },
  { issue: 'Youth Jobs',       count:  87, pct: 25, trend: 'down', urgency: 'MEDIUM',   delta:  -8, zones: ['North', 'Central'] },
  { issue: 'Civic Complaints', count:  76, pct: 22, trend: 'up',   urgency: 'LOW',      delta: +12, zones: ['West'] },
];

export const boothIntelligence = [
  { id: 'B015', zone: 'South',   support: 88, oppoRisk: 'None',   volunteers: 6, risk: 'low',      flag: 'stronghold', note: '28 confirmed voters. No opposition seen.' },
  { id: 'B007', zone: 'Central', support: 82, oppoRisk: 'Low',    volunteers: 5, risk: 'low',      flag: 'stronghold', note: 'Fortress. All panna voters confirmed.' },
  { id: 'B044', zone: 'South',   support: 80, oppoRisk: 'None',   volunteers: 6, risk: 'low',      flag: 'stronghold', note: 'SC/ST community solid. Alliance working.' },
  { id: 'B122', zone: 'Central', support: 76, oppoRisk: 'None',   volunteers: 5, risk: 'low',      flag: 'stronghold', note: 'Women SHG strong. 22 committed votes.' },
  { id: 'B062', zone: 'West',    support: 71, oppoRisk: 'Low',    volunteers: 4, risk: 'low',      flag: 'safe',       note: 'Road project well received.' },
  { id: 'B143', zone: 'West',    support: 64, oppoRisk: 'Low',    volunteers: 3, risk: 'medium',   flag: 'watch',      note: 'Youth moderate. IT park promise positive.' },
  { id: 'B035', zone: 'North',   support: 58, oppoRisk: 'Medium', volunteers: 3, risk: 'medium',   flag: 'watch',      note: 'Youth asking about jobs. Need candidate visit.' },
  { id: 'B099', zone: 'East',    support: 52, oppoRisk: 'Medium', volunteers: 3, risk: 'high',     flag: 'watch',      note: 'Opposition materials distributed. Monitoring.' },
  { id: 'B071', zone: 'North',   support: 45, oppoRisk: 'High',   volunteers: 2, risk: 'high',     flag: 'danger',     note: 'North Zone decline epicenter. Needs visit.' },
  { id: 'B118', zone: 'North',   support: 42, oppoRisk: 'High',   volunteers: 2, risk: 'critical', flag: 'danger',     note: 'Negative trend rising. BNP rally impact visible.' },
  { id: 'B091', zone: 'East',    support: 34, oppoRisk: 'High',   volunteers: 2, risk: 'critical', flag: 'danger',     note: 'Hostile. BNP door-to-door ongoing.' },
  { id: 'B108', zone: 'East',    support: 41, oppoRisk: 'High',   volunteers: 1, risk: 'critical', flag: 'danger',     note: 'Drainage complaint unresolved 3 years.' },
];

export const trendingTopics = [
  { topic: 'Water Pipeline Delay',     mentions: 342, sentiment: 'negative', growth: '+34%', zone: 'East · North',    hot: true },
  { topic: 'Road Project Completion',  mentions: 287, sentiment: 'positive', growth: '+18%', zone: 'South · West',    hot: false },
  { topic: 'Drainage Repair Pending',  mentions: 167, sentiment: 'negative', growth: '+28%', zone: 'East',            hot: true },
  { topic: 'Youth Employment Scheme',  mentions: 198, sentiment: 'neutral',  growth: '+12%', zone: 'North · Central', hot: false },
  { topic: 'Opposition Rally Impact',  mentions: 143, sentiment: 'negative', growth: '+21%', zone: 'North',           hot: true },
  { topic: 'Women SHG Meetings',       mentions: 112, sentiment: 'positive', growth:  '+8%', zone: 'Central',         hot: false },
  { topic: 'SC/ST Community Outreach', mentions:  94, sentiment: 'positive', growth: '+15%', zone: 'South · East',    hot: false },
];

export const sentimentTrends = {
  vs_yesterday: [
    { label: 'Youth Engagement',   delta: +8,  direction: 'up',   isGood: true  },
    { label: 'SHG Support',        delta: +12, direction: 'up',   isGood: true  },
    { label: 'North Zone Trust',   delta: -5,  direction: 'down', isGood: false },
    { label: 'Water Complaints',   delta: +34, direction: 'up',   isGood: false },
    { label: 'Volunteer Activity', delta: +6,  direction: 'up',   isGood: true  },
  ],
  vs_last_week: [
    { label: 'Overall Mood',        delta: +0.4, direction: 'up', isGood: true  },
    { label: 'SC/ST Sentiment',     delta: +12,  direction: 'up', isGood: true  },
    { label: 'East Zone Risk',      delta: +8,   direction: 'up', isGood: false },
    { label: 'Women Voter Trust',   delta: +9,   direction: 'up', isGood: true  },
    { label: 'Opposition Activity', delta: +14,  direction: 'up', isGood: false },
  ],
};

export const fieldOpsMetrics = {
  teamsActive:           18,
  teamsTotal:            22,
  boothsCovered:        122,
  boothsTotal:          150,
  volunteerCheckIns:    284,
  volunteerTotal:       342,
  doorToDoorCompleted: 3420,
  doorToDoorTarget:    5100,
  coveragePct:           81,
  lastCheckIn:      '09:47 AM',
};

// ─── Anti-Incumbency Intelligence ────────────────────────────
// Source: VAYU Field Reports aggregated over 7 days
// Anti-incumbency score 0-100: higher = stronger "vote against" sentiment
export const antiIncumbencySignals = {
  overallScore: 34,
  trend: 'rising',
  lastUpdated: '09:15 AM · 21 May 2026',
  source: 'VAYU Field Intelligence · 342 reports',
  primaryDrivers: [
    { issue: 'Water Supply Failure', weight: 35, zone: 'South · East', severity: 'high' },
    { issue: 'Power Cuts (5–6 hrs)', weight: 28, zone: 'East',          severity: 'high' },
    { issue: 'Road Project Delay',   weight: 20, zone: 'Central',       severity: 'medium' },
    { issue: 'Unemployment',         weight: 12, zone: 'North',         severity: 'medium' },
    { issue: 'Healthcare Access',    weight:  5, zone: 'West',          severity: 'low' },
  ],
  byZone: [
    { zone: 'East',    score: 61, status: 'critical', primaryIssue: 'Power cuts + drainage complaints', booths: 29 },
    { zone: 'South',   score: 58, status: 'high',     primaryIssue: 'Water shortage — 11 consecutive days', booths: 28 },
    { zone: 'North',   score: 52, status: 'high',     primaryIssue: 'Unemployment + BNP rally momentum', booths: 30 },
    { zone: 'Central', score: 22, status: 'low',      primaryIssue: 'Road delay — partially mitigated', booths: 32 },
    { zone: 'West',    score: 18, status: 'low',      primaryIssue: 'SHG endorsement buffering impact', booths: 31 },
  ],
};

// ─── Volunteer Zone Attendance ────────────────────────────────
// Source: VAYU app check-ins vs. deployment register
export const volunteerZoneAttendance = [
  { zone: 'Central', assigned: 120, checkedIn: 108, target: 110, pct: 90, trend: 'stable' },
  { zone: 'West',    assigned:  75, checkedIn:  66, target:  70, pct: 88, trend: 'stable' },
  { zone: 'South',   assigned:  85, checkedIn:  71, target:  80, pct: 84, trend: 'up' },
  { zone: 'North',   assigned:  95, checkedIn:  68, target:  85, pct: 72, trend: 'down' },
  { zone: 'East',    assigned:  75, checkedIn:  52, target:  70, pct: 69, trend: 'down' },
];

// ─── Worker Escalations ────────────────────────────────────────
// Source: VAYU escalation pipeline — worker-submitted critical reports
export const workerEscalations = [
  {
    id: 'WE001', worker: 'Sanjay Kumar', booth: 'B091', zone: 'East',
    issue: 'Opposition workers distributing cash near polling booth entrance',
    severity: 'critical', time: '08:45 AM', status: 'Open',
  },
  {
    id: 'WE002', worker: 'Rekha Rao', booth: 'B043', zone: 'South',
    issue: 'HMWSSB pipe burst blocking booth access road — voters may face difficulty',
    severity: 'high', time: '07:30 AM', status: 'Open',
  },
  {
    id: 'WE003', worker: 'Mahesh Reddy', booth: 'B112', zone: 'North',
    issue: 'Voter list discrepancy — 47 names not appearing in final roll',
    severity: 'high', time: '09:00 AM', status: 'Escalated',
  },
  {
    id: 'WE004', worker: 'Priya Sharma', booth: 'B078', zone: 'West',
    issue: 'Community meeting disrupted by rival party supporters',
    severity: 'medium', time: '08:15 AM', status: 'Resolved',
  },
];

// ─── Booth Attention Priority List ────────────────────────────
// Source: VISHLESHAN Risk Algorithm — composite of contact rate, opposition
// activity, mood score, volunteer coverage and issue density
export const boothAttentionList = [
  { id: 'B091', zone: 'East',    area: 'Miyapur Sector 4',    riskScore: 88, reason: 'Hostile mood · Opposition door-to-door active · Contact 34%', urgency: 'CRITICAL', volunteers: 2, voters: 1247 },
  { id: 'B112', zone: 'North',   area: 'Hafeezpet Block A',   riskScore: 82, reason: 'Opposition momentum · Voter list discrepancy reported',       urgency: 'CRITICAL', volunteers: 2, voters: 1156 },
  { id: 'B108', zone: 'East',    area: 'Nizampet Crossroads', riskScore: 79, reason: 'Drainage complaint 3 years unresolved · 1 volunteer only',    urgency: 'CRITICAL', volunteers: 1, voters: 1089 },
  { id: 'B043', zone: 'South',   area: 'Lingampally Main',    riskScore: 76, reason: 'Water shortage 11 days · Access road blocked by pipe burst',  urgency: 'HIGH',     volunteers: 2, voters: 1034 },
  { id: 'B067', zone: 'North',   area: 'Kondapur Junction',   riskScore: 71, reason: 'BNP rally impact · Low youth contact · No candidate visit',   urgency: 'HIGH',     volunteers: 3, voters: 1312 },
];

// ─── Follow-Up Action Recommendations ─────────────────────────
// Source: VISHLESHAN Issue-to-Action Engine
// Auto-generated from issueHeatmap + zoneSentimentDetail + antiIncumbencySignals
export const followUpRecommendations = [
  {
    id: 'fa-1', priority: 'CRITICAL', zone: 'East',
    action: 'Deploy emergency water tankers to East Zone — coordinate with HMWSSB',
    detail: '68% of field reports cite water shortage. East Zone anti-incumbency score 61/100.',
    deadline: 'By 11:00 AM today', team: 'Infrastructure Cell',
    source: 'VAYU · 234 mentions',
  },
  {
    id: 'fa-2', priority: 'CRITICAL', zone: 'North',
    action: 'Candidate presence at 3 North Zone corner meetings tonight',
    detail: 'Mood dropped 3.9→3.1 after BNP rally. Every 12-hour delay increases risk.',
    deadline: 'By 7:00 PM today', team: 'Ground Team Alpha',
    source: 'VAYU · VANI analysis',
  },
  {
    id: 'fa-3', priority: 'HIGH', zone: 'East',
    action: 'Redeploy 20 workers from West Zone to East — 18 booths below 40% contact',
    detail: 'West Zone above target. East gap = ~27,000 voters unreached.',
    deadline: 'Before 12:00 noon', team: 'Operations Cell',
    source: 'VAYU deployment data',
  },
  {
    id: 'fa-4', priority: 'HIGH', zone: 'All',
    action: 'Approve and distribute VANI counter-narrative on BNP employment promise',
    detail: 'Fact-check content showing state budget constraints is ready for distribution.',
    deadline: 'Before noon today', team: 'VANI Cell',
    source: 'VANI intelligence',
  },
  {
    id: 'fa-5', priority: 'MEDIUM', zone: 'Central',
    action: 'SC/ST community consolidation event — lock in +12pt sentiment gain',
    detail: 'Central Zone sentiment at +12 pts this week. Hold a community event to solidify.',
    deadline: 'Within 2 days', team: 'Community Outreach',
    source: 'VAYU sentiment trend',
  },
];

// ─── What Changed Since Yesterday ────────────────────────────
// Source: VISHLESHAN daily delta engine — 06:00 AM comparison
export const changedSinceYesterday = [
  { metric: 'Win Probability',      current: '67%',   delta: '+3 pts', direction: 'up',   context: 'SC/ST recovery in Central Zone',       agent: 'VISHLESHAN' },
  { metric: 'North Zone Mood',      current: '3.1/5', delta: '−0.8',   direction: 'down', context: 'BNP Balanagar rally impact',            agent: 'VAYU'       },
  { metric: 'East Contact Rate',    current: '38%',   delta: '+8 pts', direction: 'up',   context: '14 booths improved coverage yesterday', agent: 'Ground Ops' },
  { metric: 'Media Sentiment',      current: '+0.22', delta: '+0.36',  direction: 'up',   context: 'SHG endorsement + road project news',  agent: 'VANI'       },
  { metric: 'Volunteer Attendance', current: '81%',   delta: '+4 pts', direction: 'up',   context: 'Zone B full mobilisation complete',    agent: 'VAYU'       },
  { metric: 'Opposition Activity',  current: '14',    delta: '+6',     direction: 'down', context: 'BNP surge in North — 6 new sightings', agent: 'VIVEK'      },
];

// ─── Issue Priority Ranking ────────────────────────────────────
// Source: VISHLESHAN multi-signal synthesis — constituency intelligence
export const issuePriorityRanking = [
  {
    rank: 1,
    issue: 'Water Supply Crisis — South & East Zones',
    severity: 'CRITICAL',
    zone: 'South · East',
    source: 'VAYU Field Reports · 234 mentions',
    impact: 'Anti-incumbency driver in 68% of field reports. Directly linked to vote defection risk.',
    suggestedAction: 'Announce HMWSSB repair timeline with specific ward-level dates. Candidate public visit to affected ward.',
    politicalEffect: 'Neutralises primary opposition attack vector. Estimated +4–6 pts South Zone sentiment if actioned within 24 hrs.',
    trend: 'worsening',
  },
  {
    rank: 2,
    issue: 'North Zone Post-Rally Sentiment Drop',
    severity: 'CRITICAL',
    zone: 'North',
    source: 'VAYU Sentiment Analysis · B031–B048',
    impact: 'Ground pulse 3.9 → 3.1 in 48 hrs. ~18,000 voters in declining trajectory.',
    suggestedAction: 'Candidate corner meetings tonight: Balanagar, Hafeezpet, Pragathi Nagar.',
    politicalEffect: '24-hour window. Zone risks flipping hostile without direct candidate presence.',
    trend: 'worsening',
  },
  {
    rank: 3,
    issue: 'East Zone Voter Contact Deficit',
    severity: 'HIGH',
    zone: 'East',
    source: 'Ground Operations Cell · 18 booths flagged',
    impact: 'Sub-40% contact rate in 18 booths. ~27,000 voters unreached — 3 days behind schedule.',
    suggestedAction: 'Redeploy 20 workers from West Zone before noon. Daily zone commander check-in.',
    politicalEffect: '+1.5 pts projected vote share per 10% contact rate improvement in this cluster.',
    trend: 'improving',
  },
  {
    rank: 4,
    issue: "BNP Youth Promise — WhatsApp Spread",
    severity: 'HIGH',
    zone: 'All Zones',
    source: 'VIVEK · VANI Media Monitor · 4 articles',
    impact: '₹6,000/month promise spreading. High traction with 18–35 male voters across North & East.',
    suggestedAction: 'Approve VANI fact-check content. Counter with IT park jobs announcement. Do NOT engage claim directly.',
    politicalEffect: 'Counter-narrative = ~40% reach reduction within 12 hrs of deployment.',
    trend: 'worsening',
  },
  {
    rank: 5,
    issue: 'INC Vote Split Risk — SC Community',
    severity: 'MEDIUM',
    zone: 'East',
    source: 'VIVEK Opposition Research',
    impact: '>8% SC vote draw tightens TRP margin by 6,000–8,000 votes.',
    suggestedAction: 'Schedule SC community engagement in Central Zone within 3 days. Leverage Dr. Sulochana Bai relationship.',
    politicalEffect: '+2 pts vote share in SC community booths if credible event held.',
    trend: 'stable',
  },
];

// ─── Candidate Visit Recommendations ──────────────────────────
// Source: VISHLESHAN strategic prioritisation algorithm
export const visitRecommendations = [
  {
    zone: 'North',
    priority: 'CRITICAL',
    location: 'Balanagar Chowk · Hafeezpet Market Area',
    rationale: 'Ground pulse dropped 3.9→3.1 in 48 hrs after BNP rally. Candidate presence is the fastest circuit-breaker.',
    voters: 18400,
    recommendedTime: 'Tonight — 7:00 PM',
    boothRange: 'B031–B048',
    expectedImpact: '+1.5 pts mood recovery within 24 hrs of visit',
    urgencyColor: 'var(--red)',
  },
  {
    zone: 'East',
    priority: 'HIGH',
    location: 'B091–B108 — Door-to-Door Walkthrough',
    rationale: '18 booths at sub-40% contact rate. Workers need visible candidate presence to boost motivation.',
    voters: 27200,
    recommendedTime: 'Tomorrow — 9:00–11:00 AM',
    boothRange: 'B091–B108',
    expectedImpact: 'Contact rate +15 pts with 2-hr candidate walkthrough + 20 workers',
    urgencyColor: 'var(--yellow)',
  },
  {
    zone: 'Central',
    priority: 'MEDIUM',
    location: 'SC Community Centre · Ambedkar Statue',
    rationale: 'SC/ST sentiment +12 pts this week. Lock in the gain before INC poaches this voter bloc.',
    voters: 9800,
    recommendedTime: 'Within 3 days',
    boothRange: 'B001–B020',
    expectedImpact: '+2 pts vote share in SC community booths',
    urgencyColor: 'var(--blue)',
  },
];
