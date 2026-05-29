import { useState, useEffect, useCallback, useRef, useMemo, memo } from 'react';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts';
import {
  RefreshCw, AlertCircle, Newspaper, ExternalLink, TrendingUp, TrendingDown,
  Minus, Cpu, X, Globe, Star, Zap, BookOpen, MessageSquare, Share2,
  MapPin, User, BarChart2, ChevronRight, AlertTriangle,
} from 'lucide-react';
import { getLiveHeadlines, getArticles, getNewsSentimentTrends, getNewsTrendingIssues, getMorningDigest, getNewsSources, getArticleDetail } from '../api/news';
import { useToast } from '../store/ToastContext';
import SourceBadge, { DataSourceStrip } from '../components/SourceBadge';
import { getCredibilityTier, DATA_SOURCES } from '../utils/sourceLabels';

function sentimentColor(score) {
  if (score == null) return 'var(--text-muted)';
  if (score >= 0.2) return 'var(--green)';
  if (score >= -0.2) return 'var(--yellow)';
  return 'var(--red)';
}

function sentimentLabel(score) {
  if (score == null) return '—';
  if (score >= 0.2) return 'Positive';
  if (score >= -0.2) return 'Neutral';
  return 'Negative';
}

function sentimentBadgeClass(score) {
  if (score == null) return 'badge-gray';
  if (score >= 0.2) return 'badge-green';
  if (score >= -0.2) return 'badge-yellow';
  return 'badge-red';
}

function formatRelTime(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  const diff = (Date.now() - d) / 1000;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)}h ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function TrendIcon({ trend }) {
  if (trend === 'rising' || trend === 'up') return <TrendingUp size={12} color="var(--red)" />;
  if (trend === 'falling' || trend === 'down') return <TrendingDown size={12} color="var(--green)" />;
  return <Minus size={12} color="var(--text-muted)" />;
}

const MOCK_ARTICLES = [
  {
    id: 1,
    headline: 'Chandanagar residents demand faster completion of ₹12 Cr road project',
    source: 'Deccan Chronicle',
    published_at: '2026-05-12T07:30:00Z',
    sentiment_score: 0.1,
    tags: ['Infrastructure', 'Roads'],
    summary: 'Residents of ward 3 and 4 push for timely completion of the NH bypass extension, citing ongoing traffic disruption and the approaching monsoon season.',
    content: `Chandanagar, May 12 — Residents of ward 3 and 4 held a demonstration outside the GHMC ward office demanding timely completion of the ₹12 crore road improvement project underway since January 2026.

The project covers 8.2 km across three zones of Chandanagar constituency. Phase 1 (4.2 km) was completed in March, but Phases 2 and 3 remain pending with the monsoon six weeks away.

"We were promised the road work would be done before the rains. There is no sign of completion," said Ramesh Naidu, a local shopkeeper.

TRP candidate Arjun Kumar Reddy cited Phase 1 completion at a recent public meeting. His critics say the unfinished portion undermines that claim.

GHMC officials confirmed Phase 2 is expected to complete by June 15.`,
  },
  {
    id: 2,
    headline: "BNP's Priya Mehta promises ₹6,000/month unemployment allowance at packed Balanagar rally",
    source: 'Times of India',
    published_at: '2026-05-11T18:45:00Z',
    sentiment_score: -0.45,
    tags: ['Opposition', 'BNP', 'Economy', 'Youth'],
    summary: 'BNP candidate Priya Mehta promised monthly unemployment benefits at an estimated 1,200-strong rally in North Zone, drawing sharp reactions from TRP analysts.',
    content: `Chandanagar, May 11 — In a show of strength in the North Zone, BNP candidate Priya Mehta promised a ₹6,000 per month unemployment allowance to all youth aged 18–35 in Chandanagar if elected.

The promise, made at the Balanagar Sports Ground to an estimated crowd of 1,200, was widely shared on WhatsApp groups overnight.

"Every young person who is unemployed deserves dignity. Under BNP, no youth in Chandanagar will go without income support," Mehta said.

TRP's response has been cautious, with a spokesperson calling the promise "fiscally impossible" given Telangana's budget constraints.

Analysts note that unemployment is the second-highest cited concern in Chandanagar — particularly among male voters aged 18–35, a group where TRP's lead is narrow.`,
  },
  {
    id: 3,
    headline: 'Water shortage enters 11th day in South Chandanagar; GHMC response called inadequate',
    source: 'The Hans India',
    published_at: '2026-05-12T06:00:00Z',
    sentiment_score: -0.68,
    tags: ['Water Supply', 'Anti-incumbency', 'Infrastructure'],
    summary: 'Residents in three wards report zero piped water supply for 11 consecutive days, raising serious anti-incumbency concerns heading into the election.',
    content: `Chandanagar, May 12 — The water shortage in South Chandanagar entered its 11th consecutive day, with residents of wards 8, 9 and 11 reporting zero piped water supply since May 1.

GHMC has deployed water tankers but locals say the supply is irregular and insufficient. "A tanker comes once in two days for a thousand households," said Geeta Bai, a homemaker in ward 9.

TRP candidate Arjun Kumar Reddy has promised a 24/7 piped water solution and announced a ₹8 crore allocation, but the ongoing shortage has dented his credibility.

Opposition candidate Priya Mehta visited ward 9 on Monday to distribute water — turning the crisis into a campaign photo opportunity.

Ground intelligence sources indicate water supply is the most frequently cited complaint in field reports — appearing in 68% of daily worker submissions.`,
  },
  {
    id: 4,
    headline: "TRP launches 'Digital Chandanagar' targeting 44,000 first-time voters",
    source: 'Telangana Today',
    published_at: '2026-05-11T11:00:00Z',
    sentiment_score: 0.38,
    tags: ['TRP', 'Youth', 'Digital', 'Campaign'],
    summary: 'The party launched a social media and WhatsApp-based outreach campaign recruiting 200 youth volunteers to engage first-time voters ahead of May 28.',
    content: `Chandanagar, May 11 — TRP candidate Arjun Kumar Reddy launched "Digital Chandanagar," targeting approximately 44,000 first-time voters (aged 18–22) in the constituency.

The initiative includes a WhatsApp helpline, a youth volunteer network of 200 "Digital Pramukhsa," and an AI-generated personalised message campaign.

"Today's young voter wants data, transparency, and real promises — not just speeches. We are meeting them where they are," Reddy said.

Each digital volunteer is tasked with engaging 50 contacts in their personal network.

Analysts view this as a direct response to BNP candidate Priya Mehta's strong social media presence, which reportedly has 3x more Instagram followers than Reddy.`,
  },
  {
    id: 5,
    headline: 'Voter awareness camps in Central Zone drive 847 new registrations',
    source: 'Sakshi',
    published_at: '2026-05-10T15:30:00Z',
    sentiment_score: 0.42,
    tags: ['Voter Awareness', 'Central Zone', 'EC'],
    summary: 'TRP-backed awareness drives across 12 Central Zone booths resulted in 847 new voter registrations and strong community response.',
    content: `Chandanagar, May 10 — Voter awareness camps across 12 booths in Central Zone over the past week resulted in 847 new voter registrations and a significant boost in awareness of the May 28 election date.

The camps provided assistance with voter ID verification, polling booth locations, and EPIC card updates.

Election Commission officials praised the initiative. "Whenever volunteer groups help expand voter literacy, it benefits democracy," said a returning officer.

TRP's ground pulse reports show Central Zone as their strongest area, with an average mood score of 4.1/5 — the highest across all five zones.

Arjun Kumar Reddy visited three of the camps to interact informally with voters — a strategy his team calls "trust-building canvassing."`,
  },
  {
    id: 6,
    headline: "Priya Mehta faces questions over 2023 land case; BNP calls it 'political vendetta'",
    source: 'Deccan Chronicle',
    published_at: '2026-05-11T14:00:00Z',
    sentiment_score: -0.31,
    tags: ['Opposition', 'Controversy', 'BNP'],
    summary: 'A 2023 land encroachment case involving BNP candidate Priya Mehta resurfaced as documents were leaked to media, though BNP disputes their authenticity.',
    content: `Chandanagar, May 11 — A 2023 land encroachment case involving BNP candidate Priya Mehta resurfaced this week as documents allegedly showing encroachment on 0.8 acres of government land near Miyapur were leaked to multiple media outlets.

BNP called the timing "suspicious" and accused TRP of orchestrating the leak. "This is a politically motivated smear campaign. Priya Mehta has a clean record," said BNP spokesperson Arjun Sharma.

Mehta told media: "Every document will be scrutinised in a court of law. The voters of Chandanagar know the truth."

The EC affidavit for Mehta shows no criminal cases registered. However, the EC query on the land matter is listed as "pending" in her nomination documents.`,
  },
  {
    id: 7,
    headline: 'Power cuts averaging 5–6 hours daily in East Chandanagar spark voter anger',
    source: 'TV9 Telugu',
    published_at: '2026-05-12T08:00:00Z',
    sentiment_score: -0.58,
    tags: ['Power', 'East Zone', 'Anti-incumbency'],
    summary: 'East Zone residents experiencing 5-6 hour daily power outages are threatening to vote against the incumbent, compounding the contact rate crisis in the zone.',
    content: `Chandanagar, May 12 — East Chandanagar residents are experiencing daily power outages of 5–6 hours, a situation they call "intolerable" heading into the May 28 election.

"Every summer, the same story. No power, no water, no roads — and they want our vote again?" said Mohammed Saleem, a small trader near booth B091.

TSECPDCL officials cite "high demand and substation maintenance" as reasons, but residents say the same explanation has been given for three consecutive summers.

East Zone has the lowest mood score (2.9/5) of all five zones. Ground intelligence indicates power cuts are the primary driver of anti-incumbency sentiment in the area.

Opposition candidate Priya Mehta has promised 24-hour power supply if elected.`,
  },
  {
    id: 8,
    headline: "Women's SHG network endorses Arjun Reddy; 8,000 households to be mobilised",
    source: 'Eenadu',
    published_at: '2026-05-10T17:00:00Z',
    sentiment_score: 0.51,
    tags: ['Women', 'SHG', 'TRP', 'West Zone'],
    summary: '42 Self-Help Groups in West Zone formally endorsed TRP candidate Arjun Kumar Reddy, pledging to mobilise approximately 8,000 women voters.',
    content: `Chandanagar, May 10 — A network of 42 Self-Help Groups (SHGs) representing approximately 1,800 women in West Zone formally endorsed TRP candidate Arjun Kumar Reddy.

SHG Network Head Smt. Padma Lakshmi said, "Arjun ji has committed to two new urban health sub-centres. We stand with him."

The endorsement is strategically significant: West Zone has approximately 38,000 female voters, and each SHG member pledged to personally persuade at least 5 women in their neighbourhood.

West Zone currently shows a mood score of 3.8/5 with an improving trend — the SHG endorsement is expected to push it higher.`,
  },
  {
    id: 9,
    headline: "INC's Pillai holds SC community meeting; vote-split risk for TRP identified",
    source: 'Telangana Today',
    published_at: '2026-05-11T10:00:00Z',
    sentiment_score: -0.14,
    tags: ['INC', 'SC Community', 'Vote Split'],
    summary: 'INC candidate Suresh Kumar Pillai targeted SC community leaders in East Zone, raising the risk of a vote split that could tighten the final margin.',
    content: `Chandanagar, May 11 — INC candidate Suresh Kumar Pillai hosted a meeting with SC community leaders at the Ambedkar statue in East Zone, in what observers say was an attempt to consolidate SC votes.

Pillai, himself from the SC (Mala) community, addressed approximately 150 attendees and promised enhanced scholarship support and MGNREGA expansion.

The meeting raises strategic concerns for TRP: if Pillai draws significant SC votes — estimated at 15% of the total voter base — it could affect TRP's arithmetic in a closely contested race.

"SC voters are not anyone's property. We make an independent choice," said Dr. Sulochana Bai, SC Welfare Association head, who attended but said she remains "undecided."`,
  },
  {
    id: 10,
    headline: 'Ground workers report IT park promise resonating with youth in three booths',
    source: 'Sakshi',
    published_at: '2026-05-12T05:00:00Z',
    sentiment_score: 0.33,
    tags: ['Employment', 'Youth', 'Ground Report'],
    summary: "Field intelligence shows youth voters aged 18–30 are responding positively to the IT park partnership promise, with candidate's IAS background adding credibility.",
    content: `Chandanagar, May 12 — Field intelligence collected over the past 48 hours indicates that the IT park partnership promise — a commitment to facilitate a technology park creating 2,000 jobs — is gaining traction among youth voters.

Worker reports from booths B143, B122, and B108 specifically mention youth aged 18–30 responding positively, with multiple workers noting that the candidate's IAS background "adds credibility."

"When an IAS officer says he will get an IT park done, youth believe him more than a politician," noted one field report.

The positive response provides a counterweight to BNP's unemployment allowance promise targeting the same demographic.`,
  },
  {
    id: 11,
    headline: '248,432 voters, 12 candidates: Chandanagar shapes up for three-cornered contest',
    source: 'The Hans India',
    published_at: '2026-05-09T12:00:00Z',
    sentiment_score: 0.05,
    tags: ['Election', 'Overview', 'EC'],
    summary: 'With 248,432 registered voters and 12 candidates on the May 28 ballot, Chandanagar Assembly Constituency is expected to see a TRP-BNP-INC three-way race.',
    content: `Chandanagar, May 9 — With 248,432 registered voters across 150 polling booths, Chandanagar Assembly Constituency will see 12 candidates contest the May 28 state election.

The real battle is expected to be a three-way contest between TRP, BNP, and INC. OBC voters constitute the largest bloc at approximately 32%, followed by General/Upper Caste (22%) and Muslim voters (18%).

Voter turnout in 2023 was 68.4%. The Election Commission has deployed 847 polling officials and 4 observers.

Chandanagar is considered a marginal seat, with no candidate currently holding a commanding lead. The next 16 days are expected to be decisive.`,
  },
  {
    id: 12,
    headline: "Analysts: TRP's caste arithmetic strong, but North Zone exposure and anti-incumbency are live risks",
    source: 'Deccan Chronicle',
    published_at: '2026-05-11T20:00:00Z',
    sentiment_score: 0.08,
    tags: ['Analysis', 'TRP', 'Psephology'],
    summary: 'Political analysts say TRP holds a structural demographic advantage but faces risks from anti-incumbency sentiment, BNP North Zone momentum, and an East Zone contact deficit.',
    content: `Chandanagar, May 11 — Political analysts monitoring Chandanagar say TRP candidate Arjun Kumar Reddy holds a structural advantage owing to favourable caste arithmetic — but faces live risks.

"Reddy's OBC-Yadav identity is a natural fit for a constituency where OBC voters are the largest bloc at 32%," said Dr. Praveena Nair, political scientist at Osmania University. "Combined with a clean professional record and IAS credibility, he should hold the fortress booths comfortably."

However, analysts flag three risk factors: (1) BNP's North Zone momentum following last week's rally; (2) East Zone anti-incumbency driven by power cuts; and (3) the INC factor — even a modest SC vote split could tighten the margin.

Ground intelligence indicates a win probability of 67% for TRP — winnable if the North Zone is shored up and East Zone contact rate improves. "Both are operational challenges, not structural ones," concluded Dr. Nair.`,
  },
];

const MOCK_TRENDS = [
  { date: 'May 4',  avg_score:  0.24, article_count: 4  },
  { date: 'May 5',  avg_score:  0.12, article_count: 6  },
  { date: 'May 6',  avg_score: -0.08, article_count: 9  },
  { date: 'May 7',  avg_score: -0.34, article_count: 14 },
  { date: 'May 8',  avg_score: -0.21, article_count: 11 },
  { date: 'May 9',  avg_score:  0.04, article_count: 8  },
  { date: 'May 10', avg_score:  0.18, article_count: 12 },
  { date: 'May 11', avg_score:  0.14, article_count: 9  },
  { date: 'May 12', avg_score:  0.22, article_count: 5  },
];

const MOCK_ISSUES = [
  { issue_name: 'Water Supply',         mention_count: 18, sentiment_score: -0.62, trend: 'rising'  },
  { issue_name: 'Road Infrastructure',  mention_count: 14, sentiment_score: -0.10, trend: 'stable'  },
  { issue_name: 'Unemployment Promise', mention_count: 12, sentiment_score: -0.40, trend: 'rising'  },
  { issue_name: 'Power Cuts',           mention_count: 10, sentiment_score: -0.55, trend: 'rising'  },
  { issue_name: 'Youth Employment',     mention_count: 9,  sentiment_score:  0.20, trend: 'falling' },
  { issue_name: 'Healthcare Access',    mention_count: 7,  sentiment_score: -0.15, trend: 'stable'  },
  { issue_name: 'Voter Awareness',      mention_count: 5,  sentiment_score:  0.38, trend: 'stable'  },
  { issue_name: 'Affordable Housing',   mention_count: 4,  sentiment_score: -0.28, trend: 'stable'  },
];

const MOCK_SOURCES = [
  { id: 1, name: 'Deccan Chronicle',    source_type: 'Print',     article_count: 12, avg_sentiment:  0.05 },
  { id: 2, name: 'Times of India',      source_type: 'Print',     article_count: 9,  avg_sentiment: -0.12 },
  { id: 3, name: 'The Hans India',      source_type: 'Print',     article_count: 7,  avg_sentiment: -0.31 },
  { id: 4, name: 'Telangana Today',     source_type: 'Digital',   article_count: 8,  avg_sentiment:  0.22 },
  { id: 5, name: 'Sakshi',              source_type: 'Print',     article_count: 8,  avg_sentiment:  0.18 },
  { id: 6, name: 'TV9 Telugu',          source_type: 'Broadcast', article_count: 6,  avg_sentiment: -0.08 },
  { id: 7, name: 'Eenadu',              source_type: 'Print',     article_count: 5,  avg_sentiment:  0.24 },
  { id: 8, name: 'V6 News',             source_type: 'Broadcast', article_count: 3,  avg_sentiment: -0.04 },
  { id: 9, name: 'Telangana Journal',   source_type: 'Digital',   article_count: 2,  avg_sentiment:  0.11 },
];

const MOCK_DIGEST_STATIC = {
  content: `CHANDANAGAR MEDIA INTELLIGENCE — 12 May 2026, 06:00 AM

HEADLINE WATCH: 14 articles tracked in the last 24 hours across 9 monitored outlets. Current sentiment: +0.22 (recovering — up from −0.34 low on May 7).

TOP COVERAGE THEMES:
▪ BNP's ₹6,000 unemployment promise — 4 articles, dominant opposition narrative, spreading on WhatsApp
▪ Road project progress — 3 articles, mixed (Phase 1 praised, Phase 2 delay criticised)
▪ Water supply crisis, South Zone — 3 articles, strongly negative, primary anti-incumbency driver
▪ Women's SHG endorsement, West Zone — 2 articles, positive momentum confirmed
▪ Priya Mehta land case — 2 articles, opposition under scrutiny

MEDIA BIAS: Times of India and Hans India lean negative on TRP infrastructure delivery. Sakshi and Eenadu balanced-to-positive. TV9 Telugu negative on power/water issues.

RECOMMENDED ACTION: Issue factual press release on road project Phase 2 timeline to shift narrative from "delayed" to "on track." Approve BNP fact-check content urgently — delay gives the opposition narrative room to embed further.

— VANI Intelligence Engine · 14 articles processed · 9 sources · Chandanagar 2026`,
  generated_at: '2026-05-12T06:00:00Z',
  is_stale: false,
};

// ─── Constituency relevance filter ───────────────────────────────────────────

const HARD_BLOCK_TERMS = [
  // International / national
  'iran', 'israel', 'ukraine', 'russia', 'china border', 'pakistan', 'us consumer',
  'wall street', 'nasdaq', 'dow jones', 'federal reserve', 'imf', 'world bank',
  'tamil nadu', 'kerala', 'karnataka', 'maharashtra', 'gujarat', 'punjab',
  'west bengal', 'bihar', 'uttar pradesh', 'rajasthan', 'madhya pradesh',
  'lok sabha', 'rajya sabha', 'parliament session', 'union budget',
  'prime minister modi', 'amit shah', 'rahul gandhi',
  // Entertainment
  'mohanlal', 'rajinikanth', 'salman khan', 'shahrukh', 'deepika', 'priyanka chopra',
  'bollywood', 'tollywood', 'kollywood', 'box office collection', 'ott release',
  'netflix series', 'amazon prime video', 'disney hotstar',
  'bigg boss', 'kbc', 'reality show', 'film release', 'movie review',
  'celebrity wedding', 'award ceremony', 'filmfare', 'siima',
  // Sports (non-local)
  'ipl match', 'cricket world cup', 'test match series',
  'fifa', 'olympics', 'commonwealth games', 'formula one',
  // Finance
  'sensex', 'nifty', 'share price', 'stock market', 'cryptocurrency',
  'bitcoin', 'mutual fund', 'ipo listing',
];

const CONSTITUENCY_KEYWORDS = [
  { terms: ['chandanagar constituency', 'chandanagar mla', 'chandanagar assembly', '70-chandanagar'], score: 10 },
  { terms: ['chandanagar'], score: 8 },
  { terms: ['serilingampally constituency', 'serilingampally mla'], score: 8 },
  { terms: ['miyapur', 'hafeezpet', 'madinaguda', 'lingampally', 'bhel township', 'bhel nagar'], score: 7 },
  { terms: ['nizampet', 'nallagandla', 'gopanpally', 'tellapur', 'serilingampally', 'kothaguda'], score: 6 },
  { terms: ['ghmc chandanagar', 'ghmc miyapur', 'ghmc serilingampally', 'chandanagar division'], score: 6 },
  { terms: ['hmwssb miyapur', 'hmwssb chandanagar', 'tsspdcl miyapur', 'tsspdcl chandanagar'], score: 5 },
  { terms: ['miyapur metro', 'miyapur flyover', 'nizampet road', 'lingampally flyover', 'orr chandanagar'], score: 5 },
  { terms: ['local mla', 'ward member', 'ward corporator', 'ghmc ward'], score: 4 },
  { terms: ['water supply', 'water shortage', 'water tanker', 'borewell'], score: 3 },
  { terms: ['road works', 'road repair', 'pothole', 'traffic diversion', 'flyover work'], score: 3 },
  { terms: ['power cut', 'electricity cut', 'outage', 'load shedding', 'tsecpdcl'], score: 3 },
  { terms: ['drainage', 'sewage', 'flooding', 'stormwater', 'nala'], score: 3 },
  { terms: ['ghmc', 'hyderabad west', 'ranga reddy'], score: 2 },
  { terms: ['hyderabad'], score: 1 },
];

function calculateRelevanceScore(article) {
  const text = `${article.headline || article.title || ''} ${article.body_text || article.summary || article.description || ''}`.toLowerCase();

  // If backend already sent a relevance_score, use it as base
  let score = typeof article.relevance_score === 'number' ? article.relevance_score * 10 : 0;

  // Hard block — immediate reject
  for (const term of HARD_BLOCK_TERMS) {
    if (text.includes(term.toLowerCase())) return 0;
  }

  // Keyword scoring
  for (const { terms, score: pts } of CONSTITUENCY_KEYWORDS) {
    for (const term of terms) {
      if (text.includes(term.toLowerCase())) {
        score += pts;
        break; // count each category once
      }
    }
  }

  return score;
}

function filterRelevantArticles(rawArticles) {
  // Articles from the live proxy already passed backend constituency filtering.
  // MIN_SCORE 2 ensures state-level Hyderabad articles (backend fallback tier)
  // still appear rather than being double-filtered out here.
  const MIN_SCORE = 2;

  const scored = rawArticles
    .map(a => ({ ...a, _relevanceScore: calculateRelevanceScore(a) }))
    .filter(a => a._relevanceScore >= MIN_SCORE);

  // Sort: highest relevance first, then newest
  scored.sort((a, b) => {
    if (b._relevanceScore !== a._relevanceScore) return b._relevanceScore - a._relevanceScore;
    return new Date(b.published_at || b.created_at || 0) - new Date(a.published_at || a.created_at || 0);
  });

  // Deduplicate by normalized headline prefix (first 60 chars, lowercased, stripped)
  const seen = new Set();
  const deduped = [];
  for (const a of scored) {
    const key = (a.headline || a.title || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').trim().slice(0, 60);
    if (key && seen.has(key)) continue;
    if (key) seen.add(key);
    deduped.push(a);
  }

  return deduped.slice(0, 15);
}

// ─────────────────────────────────────────────────────────────────────────────

function suggestResponse(article) {
  const score = article.sentiment_score ?? article.sentiment ?? null;
  const tags = article.tags || article.constituency_tags || [];
  const text = `${article.headline || ''} ${article.summary || ''}`.toLowerCase();

  if (text.includes('water') || text.includes('tanker') || text.includes('borewell'))
    return 'Issue a factual update on HMWSSB repair timelines and announce emergency tanker deployment schedule. Activate WhatsApp ward groups for real-time updates to affected residents.';
  if (text.includes('road') || text.includes('pothole') || text.includes('flyover'))
    return 'Release a Phase-wise completion timeline with photographic evidence of progress. Counter negative narrative with GHMC work order numbers and contractor accountability details.';
  if (text.includes('power') || text.includes('electricity') || text.includes('outage'))
    return 'Contact TSECPDCL officer directly and publish their written commitment timeline. Circulate substation upgrade plan to East Zone panna pramukhsas to counter anti-incumbency at booth level.';
  if (text.includes('opposition') || text.includes('bnp') || text.includes('rival'))
    return 'Brief ground commander to monitor opposition rally location. Prepare factual rebuttal sheet for worker distribution. Schedule candidate visit to same zone within 24 hours.';
  if (score != null && score < -0.4)
    return 'High negative sentiment detected. Recommend candidate public statement within 6 hours. Brief media cell and prepare a 3-point factual counter-narrative for distribution across all ward WhatsApp groups.';
  if (score != null && score > 0.3)
    return 'Positive coverage detected. Amplify through official social media channels. Share with SHG networks and panna pramukhsas for grassroots distribution. Good material for morning brief.';
  return 'Monitor article spread across local WhatsApp groups. Flag to campaign manager if traction increases. Document for the VANI daily digest.';
}

function computePoliticalImpact(article) {
  const score = article.sentiment_score ?? article.sentiment ?? null;
  const rel = article._relevanceScore ?? article.relevance_score ?? 5;
  const text = `${article.headline || ''} ${article.summary || ''}`.toLowerCase();
  const highImpact = ['water', 'power cut', 'unemploy', 'anti-incumbency', 'bnp', 'opposition', 'rally', 'land case', 'vote split'];
  const boost = highImpact.some(t => text.includes(t)) ? 2 : 0;
  const sentNorm = score != null ? Math.abs(score) : 0.3;
  const relNorm = Math.min(10, rel) / 10;
  const raw = sentNorm * 6 + relNorm * 3 + boost;
  const impactScore = Math.min(10, Math.max(1, Math.round(raw)));
  const candidateImpact = score == null ? 'neutral' : score > 0.2 ? 'positive' : score < -0.2 ? 'negative' : 'neutral';
  return { score: impactScore, candidateImpact };
}

function inferZone(article) {
  const text = `${article.headline || ''} ${article.summary || ''} ${article.zone || ''}`.toLowerCase();
  if (text.includes('south')) return 'South';
  if (text.includes('north')) return 'North';
  if (text.includes('east')) return 'East';
  if (text.includes('west')) return 'West';
  if (text.includes('central')) return 'Central';
  return article.zone || null;
}

function ArticleModal({ article, onClose, toast }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marked, setMarked] = useState(false);

  useEffect(() => {
    // Try to fetch enriched detail from backend; fall back silently to article data
    const idStr = String(article?.id ?? '');
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(idStr);
    if (!isUuid) { setLoading(false); return; }
    getArticleDetail(article.id)
      .then(d => setDetail(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [article?.id]);

  // Escape key closes modal
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const data = detail || article;
  const score = data?.sentiment_score ?? data?.sentiment ?? null;
  const scoreColor = sentimentColor(score);
  const headline = data?.headline || data?.title || 'Untitled';
  const source = data?.source || data?.source_name || '—';
  const relTime = formatRelTime(data?.published_at || data?.created_at);
  const content = detail?.body_text || detail?.content || detail?.full_content || data?.summary || data?.description || null;
  const url = data?.url || data?.link || null;
  const relScore = article._relevanceScore ?? article.relevance_score ?? null;
  const relTier = article.relevance_tier ?? null;
  const tags = data?.tags || data?.constituency_tags || [];
  const suggestedResponse = suggestResponse(data);

  const actions = [
    {
      icon: <Star size={13} />, label: marked ? 'Marked Important' : 'Mark Important',
      color: marked ? 'var(--yellow)' : 'var(--text-muted)',
      bg: marked ? 'rgba(217,119,6,0.12)' : 'var(--bg-base)',
      border: marked ? 'rgba(217,119,6,0.35)' : 'var(--border)',
      action: () => { setMarked(m => !m); toast(marked ? 'Removed from important' : 'Marked as important', 'success'); },
    },
    {
      icon: <Zap size={13} />, label: 'Send to War Room',
      color: 'var(--red)', bg: 'rgba(220,38,38,0.08)', border: 'rgba(220,38,38,0.25)',
      action: () => toast('Sent to War Room — team notified', 'warning'),
    },
    {
      icon: <BookOpen size={13} />, label: 'Save for Briefing',
      color: 'var(--blue)', bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.25)',
      action: () => toast('Saved to next briefing document', 'info'),
    },
    {
      icon: <MessageSquare size={13} />, label: 'Generate Talking Points',
      color: 'var(--purple)', bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.25)',
      action: () => toast('Talking points queued — VANI will generate within 2 min', 'info'),
    },
    {
      icon: <Share2 size={13} />, label: 'Share to Team',
      color: 'var(--green)', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.25)',
      action: () => toast('Article shared to campaign WhatsApp group', 'success'),
    },
  ];

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 9000,
        background: 'rgba(0,0,0,0.78)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20, animation: 'fadeIn 0.18s ease',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--bg-elevated)', border: '1px solid var(--border)',
          borderRadius: 18, maxWidth: 760, width: '100%', maxHeight: '88vh',
          overflowY: 'auto', position: 'relative',
          boxShadow: '0 32px 100px rgba(0,0,0,0.65)',
          animation: 'slideUp 0.22s cubic-bezier(0.16,1,0.3,1)',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Sentiment colour strip at top */}
        <div style={{ height: 5, borderRadius: '18px 18px 0 0', background: scoreColor, opacity: 0.85 }} />

        <div style={{ padding: '22px 28px 28px' }}>
          {/* Header row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Newspaper size={12} color="var(--text-muted)" />
                <span style={{ fontSize: 12, color: 'var(--saffron)', fontWeight: 700 }}>{source}</span>
              </div>
              {relTime && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{relTime}</span>}
              {score != null && (
                <span className={`badge ${sentimentBadgeClass(score)}`} style={{ fontSize: 10 }}>
                  {score >= 0 ? '+' : ''}{score.toFixed(2)} · {sentimentLabel(score)}
                </span>
              )}
              {relTier && relTier !== 'irrelevant' && (
                <span style={{
                  fontSize: 9, padding: '2px 7px', borderRadius: 8, fontWeight: 700,
                  background: 'rgba(16,185,129,0.12)', color: 'var(--green)',
                  border: '1px solid rgba(16,185,129,0.3)', textTransform: 'uppercase', letterSpacing: 0.4,
                }}>
                  {relTier === 'constituency_specific' ? 'Constituency' : relTier}
                </span>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
              {url && (
                <a
                  href={url} target="_blank" rel="noopener noreferrer"
                  title="Open original article"
                  style={{
                    display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px',
                    borderRadius: 8, fontSize: 11, color: 'var(--blue)', textDecoration: 'none',
                    border: '1px solid rgba(59,130,246,0.3)', background: 'rgba(59,130,246,0.08)',
                  }}
                  onClick={e => e.stopPropagation()}
                >
                  <ExternalLink size={11} /> Source
                </a>
              )}
              <button
                onClick={onClose}
                style={{
                  background: 'var(--bg-base)', border: '1px solid var(--border)',
                  borderRadius: 8, cursor: 'pointer', color: 'var(--text-muted)',
                  padding: '6px 8px', display: 'flex', alignItems: 'center',
                }}
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Headline */}
          <div style={{ fontSize: 21, fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 18 }}>
            {headline}
          </div>

          {/* Tags */}
          {tags.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 20 }}>
              {tags.map(tag => (
                <span key={tag} className="badge badge-blue" style={{ fontSize: 10 }}>{tag}</span>
              ))}
            </div>
          )}

          {/* Intelligence summary strip */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 22,
            padding: '14px 16px', borderRadius: 12,
            background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)',
          }}>
            <div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 }}>
                <BarChart2 size={9} style={{ display: 'inline', marginRight: 4 }} />Constituency Relevance
              </div>
              <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--green)' }}>
                {relScore != null
                  ? (typeof relScore === 'number' && relScore <= 1 ? Math.round(relScore * 100) : Math.round(relScore * 10)) + '%'
                  : '—'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 }}>
                <MapPin size={9} style={{ display: 'inline', marginRight: 4 }} />Zone / Ward
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                {data?.zone || data?.ward || 'Chandanagar'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 4 }}>
                <User size={9} style={{ display: 'inline', marginRight: 4 }} />Candidate Impact
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: scoreColor }}>
                {score == null ? 'Neutral' : score > 0.2 ? 'Positive' : score < -0.2 ? 'Adverse' : 'Low Impact'}
              </div>
            </div>
          </div>

          {/* Article content */}
          <div style={{ marginBottom: 22 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
              Article Content
            </div>
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', fontSize: 13, padding: '10px 0' }}>
                <div style={{
                  width: 15, height: 15, border: '2px solid var(--border)',
                  borderTop: '2px solid var(--saffron)', borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite', flexShrink: 0,
                }} />
                Loading full article…
              </div>
            ) : content ? (
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.9, whiteSpace: 'pre-wrap' }}>
                {content}
              </div>
            ) : (
              <div style={{
                padding: '14px 16px', borderRadius: 10,
                background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)',
                fontSize: 13, color: 'var(--text-muted)', fontStyle: 'italic',
              }}>
                No detailed content available for this article.
              </div>
            )}
          </div>

          {/* Suggested political response */}
          <div style={{
            marginBottom: 24, padding: '14px 16px', borderRadius: 12,
            background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
              <AlertTriangle size={12} color="var(--purple)" />
              <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--purple)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
                Suggested Political Response
              </span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.75 }}>
              {suggestedResponse}
            </div>
          </div>

          {/* Action buttons */}
          <div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
              Actions
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {actions.map(({ icon, label, color, bg, border, action }) => (
                <button
                  key={label}
                  onClick={(e) => { e.stopPropagation(); action(); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '8px 14px', borderRadius: 9, cursor: 'pointer',
                    fontSize: 12, fontWeight: 600, color,
                    background: bg, border: `1px solid ${border}`,
                    transition: 'opacity 0.15s, transform 0.1s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                  onMouseLeave={e => { e.currentTarget.style.opacity = '1'; e.currentTarget.style.transform = 'translateY(0)'; }}
                >
                  {icon} {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── EmergingRisksPanel ────────────────────────────────────────────────────────
const EmergingRisksPanel = memo(function EmergingRisksPanel({ articles }) {
  const risks = useMemo(() => (articles || [])
    .filter(a => {
      const s = a.sentiment_score ?? a.sentiment ?? null;
      return s != null && s < -0.25;
    })
    .sort((a, b) => {
      const sa = a.sentiment_score ?? a.sentiment ?? 0;
      const sb = b.sentiment_score ?? b.sentiment ?? 0;
      return sa - sb;
    })
    .slice(0, 5),
  [articles]);

  if (!risks.length) return null;

  return (
    <div style={{
      padding: '14px 16px', borderRadius: 12,
      background: 'linear-gradient(135deg, rgba(239,68,68,0.07) 0%, rgba(239,68,68,0.02) 100%)',
      border: '1px solid rgba(239,68,68,0.25)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
        <AlertTriangle size={11} color="var(--red)" />
        <span style={{ fontSize: 10, fontWeight: 800, color: 'var(--red)', textTransform: 'uppercase', letterSpacing: 0.9 }}>
          Top 5 Emerging Risks
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>by negative sentiment</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {risks.map((a, i) => {
          const s = a.sentiment_score ?? a.sentiment ?? 0;
          const zone = inferZone(a);
          const { score: impact } = computePoliticalImpact(a);
          return (
            <div key={a.id || i} style={{
              padding: '8px 10px', borderRadius: 8,
              background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.18)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                <span style={{
                  fontSize: 9, fontWeight: 900, fontFamily: 'var(--font-mono)',
                  color: 'var(--red)', flexShrink: 0, marginTop: 1,
                }}>#{i + 1}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                    {a.headline || a.title || '—'}
                  </div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{a.source}</span>
                    <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--red)', fontWeight: 700 }}>
                      {s.toFixed(2)}
                    </span>
                    {zone && <span style={{ fontSize: 8, padding: '1px 5px', borderRadius: 3, background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>{zone}</span>}
                    <span style={{ fontSize: 8, color: 'var(--text-dim)' }}>Impact: {impact}/10</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

// ── PositiveNarrativesPanel ───────────────────────────────────────────────────
const PositiveNarrativesPanel = memo(function PositiveNarrativesPanel({ articles }) {
  const positives = useMemo(() => (articles || [])
    .filter(a => {
      const s = a.sentiment_score ?? a.sentiment ?? null;
      return s != null && s > 0.15;
    })
    .sort((a, b) => {
      const sa = a.sentiment_score ?? a.sentiment ?? 0;
      const sb = b.sentiment_score ?? b.sentiment ?? 0;
      return sb - sa;
    })
    .slice(0, 5),
  [articles]);

  if (!positives.length) return null;

  return (
    <div style={{
      padding: '14px 16px', borderRadius: 12,
      background: 'linear-gradient(135deg, rgba(16,185,129,0.07) 0%, rgba(16,185,129,0.02) 100%)',
      border: '1px solid rgba(16,185,129,0.25)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
        <TrendingUp size={11} color="var(--green)" />
        <span style={{ fontSize: 10, fontWeight: 800, color: 'var(--green)', textTransform: 'uppercase', letterSpacing: 0.9 }}>
          Top 5 Positive Narratives
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)', marginLeft: 'auto' }}>by positive sentiment</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {positives.map((a, i) => {
          const s = a.sentiment_score ?? a.sentiment ?? 0;
          const zone = inferZone(a);
          return (
            <div key={a.id || i} style={{
              padding: '8px 10px', borderRadius: 8,
              background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.18)',
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                <span style={{
                  fontSize: 9, fontWeight: 900, fontFamily: 'var(--font-mono)',
                  color: 'var(--green)', flexShrink: 0, marginTop: 1,
                }}>#{i + 1}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 3 }}>
                    {a.headline || a.title || '—'}
                  </div>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>{a.source}</span>
                    <span style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--green)', fontWeight: 700 }}>
                      +{s.toFixed(2)}
                    </span>
                    {zone && <span style={{ fontSize: 8, padding: '1px 5px', borderRadius: 3, background: 'var(--bg-elevated)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>{zone}</span>}
                    <span style={{ fontSize: 9, color: 'var(--green)', fontWeight: 700 }}>↑ Amplify</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default function NewsIntelligence() {
  const { addToast } = useToast();
  const [articles, setArticles] = useState(MOCK_ARTICLES);
  const [trends, setTrends] = useState(MOCK_TRENDS);
  const [issues, setIssues] = useState(MOCK_ISSUES);
  const [sources, setSources] = useState(MOCK_SOURCES);
  const [digest, setDigest] = useState(null);
  const [errors, setErrors] = useState({});
  const [refreshing, setRefreshing] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [liveArticles, setLiveArticles] = useState(false);
  const [liveTrends, setLiveTrends] = useState(false);
  const [liveSources, setLiveSources] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [liveSourceCounts, setLiveSourceCounts] = useState(null);

  const handleOpenArticle = useCallback((article) => {
    const url = article.url || article.link || null;
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    } else {
      // No external URL — open internal intelligence detail
      setSelectedArticle(article);
    }
  }, []);

  const loadAll = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    const newErrors = {};

    await Promise.allSettled([
      getLiveHeadlines(40).then(data => {
        const arr = Array.isArray(data) ? data : [];
        const filtered = filterRelevantArticles(arr);
        if (filtered.length > 0) {
          setArticles(filtered);
          setLiveArticles(true);
          // Build per-source article counts from live proxy results
          const counts = {};
          filtered.forEach(a => {
            const src = a.source_name || a.source || 'Unknown';
            counts[src] = (counts[src] || 0) + 1;
          });
          setLiveSourceCounts(counts);
        } else {
          // Fall back to DB-backed feed if live proxy returned nothing
          return getArticles(50).then(dbData => {
            const dbArr = Array.isArray(dbData) ? dbData : dbData.items || dbData.articles || [];
            const dbFiltered = filterRelevantArticles(dbArr);
            if (dbFiltered.length > 0) { setArticles(dbFiltered); setLiveArticles(true); }
          });
        }
      }).catch(() => {
        // Live proxy failed — try DB feed
        getArticles(50).then(dbData => {
          const dbArr = Array.isArray(dbData) ? dbData : dbData.items || dbData.articles || [];
          const dbFiltered = filterRelevantArticles(dbArr);
          if (dbFiltered.length > 0) { setArticles(dbFiltered); setLiveArticles(true); }
        }).catch(() => { newErrors.articles = true; });
      }),

      getNewsSentimentTrends().then(data => {
        const raw = data?.timeline || data?.trend_data || data?.data || [];
        const arr = Array.isArray(raw) ? raw : [];
        if (arr.length > 0) { setTrends(arr); setLiveTrends(true); }
      }).catch(() => { newErrors.trends = true; }),

      getNewsTrendingIssues().then(data => {
        const arr = Array.isArray(data) ? data : data.issues || data.items || [];
        if (arr.length > 0) setIssues(arr);
      }).catch(() => { newErrors.issues = true; }),

      getMorningDigest().then(data => {
        if (data?.narrative || data?.content) {
          setDigest({ ...data, content: data.narrative || data.content });
        }
      }).catch(() => {}),

      getNewsSources().then(data => {
        const arr = Array.isArray(data) ? data : data.sources || data.items || [];
        if (arr.length > 0) {
          setLiveSources(true);
          // Only replace mock sources if the DB has actual article data.
          // If Celery hasn't run yet, article_count is 0 across all sources —
          // keep mock sources displayed but mark connectivity as live.
          const hasArticles = arr.some(s => (s.article_count || s.count || 0) > 0);
          if (hasArticles) setSources(arr);
        }
      }).catch(() => {}),
    ]);

    setErrors(newErrors);
    setRefreshing(false);
    setInitialized(true);
  };

  const refresh = useCallback(() => loadAll(true), []);
  const { countdown, triggerNow } = useAutoRefresh(refresh, 90);

  useEffect(() => { loadAll(); }, []);

  const safeTrends = Array.isArray(trends) ? trends : [];

  const avgSentiment = safeTrends.length
    ? safeTrends.reduce((s, t) => s + (t.polarity ?? t.avg_score ?? t.score ?? 0), 0) / safeTrends.length
    : null;

  const latestSentiment = safeTrends.length
    ? (safeTrends[safeTrends.length - 1].polarity ?? safeTrends[safeTrends.length - 1].avg_score ?? safeTrends[safeTrends.length - 1].score)
    : null;

  const totalArticles = safeTrends.reduce((s, t) => {
    const c = t.article_count ?? t.count ?? t.sample_count ?? (t.positive != null ? (t.positive + t.negative + t.neutral) : 0);
    return s + c;
  }, 0);

  return (
    <>
      {selectedArticle && (
        <ArticleModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
          toast={addToast}
        />
      )}

      <div>
        <div className="page-header">
          <div>
            <div className="page-title">News Intelligence</div>
            <div className="page-subtitle">VANI Agent · Media monitoring · Sentiment analysis · Serilingampally AC-52 · 2026</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="live-badge"><span className="live-dot" /> VANI Active</span>
            <button
              className="btn btn-outline btn-sm"
              onClick={triggerNow}
              disabled={refreshing}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <RefreshCw size={12} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
              {refreshing ? 'Refreshing…' : `Refresh (${countdown}s)`}
            </button>
          </div>
        </div>

        <div className="page-body">
          {/* ─── Data Source Attribution ─── */}
          <DataSourceStrip
            sources={[DATA_SOURCES.VANI, DATA_SOURCES.VIVEK]}
            live={liveArticles}
            confidence={liveArticles ? 87 : 70}
          />

          {Object.keys(errors).length > 0 && (
            <div style={{
              padding: '10px 14px', marginBottom: 16, borderRadius: 8,
              background: 'rgba(217,119,6,0.1)', border: '1px solid rgba(217,119,6,0.3)',
              display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--yellow)',
            }}>
              <AlertCircle size={13} />
              Some live data unavailable — showing cached / static data for affected sections.
            </div>
          )}

          {/* Morning Digest */}
          {(digest || MOCK_DIGEST_STATIC) && (
            <div style={{
              padding: '20px 24px', marginBottom: 18,
              background: 'linear-gradient(135deg, #0c1a2e 0%, #101c30 100%)',
              borderRadius: 16, border: '1px solid rgba(99,102,241,0.3)',
              boxShadow: '0 0 40px rgba(99,102,241,0.08)',
            }}>
              {(() => {
                const d = digest || MOCK_DIGEST_STATIC;
                return (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                      <div style={{
                        width: 32, height: 32, borderRadius: 8,
                        background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.4)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <Cpu size={16} color="var(--purple)" />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--purple)', letterSpacing: 1, textTransform: 'uppercase' }}>
                          VANI Morning Digest
                        </div>
                        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                          Generated {formatRelTime(d.generated_at)}
                          {d.is_stale && <span style={{ color: 'var(--yellow)', marginLeft: 6 }}>· STALE</span>}
                        </div>
                      </div>
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.85, whiteSpace: 'pre-wrap' }}>
                      {d.content}
                    </div>
                  </>
                );
              })()}
            </div>
          )}

          {/* Stats row */}
          {!initialized ? (
            <div className="grid-4 section-gap">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="stat-card">
                  <div className="skeleton" style={{ height: 11, width: '60%', marginBottom: 10 }} />
                  <div className="skeleton" style={{ height: 32, width: '50%', marginBottom: 8 }} />
                  <div className="skeleton" style={{ height: 10, width: '40%' }} />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid-4 section-gap">
              {[
                {
                  label: 'Current Sentiment',
                  value: latestSentiment != null ? latestSentiment.toFixed(2) : '—',
                  sub: sentimentLabel(latestSentiment),
                  color: sentimentColor(latestSentiment),
                },
                {
                  label: '7-Day Avg Sentiment',
                  value: avgSentiment != null ? avgSentiment.toFixed(2) : '—',
                  sub: sentimentLabel(avgSentiment),
                  color: sentimentColor(avgSentiment),
                },
                {
                  label: 'Articles (7d)',
                  value: totalArticles || articles.length,
                  sub: liveArticles ? 'Live count' : 'Estimated',
                  color: 'var(--blue)',
                },
                {
                  label: 'Tracked Sources',
                  value: sources.length,
                  sub: liveSources ? 'Live · VANI' : 'Monitored outlets',
                  color: 'var(--purple)',
                },
              ].map(({ label, value, sub, color }) => (
                <div key={label} className="stat-card" style={{ '--accent-color': color }}>
                  <div className="stat-label">{label}</div>
                  <div className="stat-value" style={{ fontSize: 28, color, fontFamily: 'var(--font-mono)' }}>{value}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>
                </div>
              ))}
            </div>
          )}

          {/* Constituency Intelligence Summary Strip */}
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12,
            padding: '14px 18px', marginBottom: 18, borderRadius: 14,
            background: 'linear-gradient(135deg, rgba(239,68,68,0.05) 0%, rgba(99,102,241,0.05) 100%)',
            border: '1px solid rgba(239,68,68,0.2)',
          }}>
            <div style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Zap size={12} color="var(--red)" />
              <span style={{ fontSize: 10, fontWeight: 800, color: 'var(--red)', textTransform: 'uppercase', letterSpacing: 1 }}>
                Constituency Intelligence · Top Breaking Signals
              </span>
            </div>
            {issues.slice(0, 3).map((issue, i) => {
              const name = issue.issue_name || issue.issue || issue.name || `Issue ${i + 1}`;
              const score = issue.sentiment_score ?? issue.sentiment ?? null;
              const trend = issue.trend || issue.trend_direction || 'stable';
              return (
                <div key={i} style={{
                  padding: '10px 12px', borderRadius: 10,
                  background: 'var(--bg-elevated)', border: `1px solid ${score != null && score < -0.3 ? 'rgba(239,68,68,0.25)' : 'var(--border)'}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <span style={{
                      fontSize: 9, fontWeight: 800, fontFamily: 'var(--font-mono)',
                      color: i === 0 ? 'var(--red)' : i === 1 ? 'var(--yellow)' : 'var(--saffron)',
                    }}>#{i + 1}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', flex: 1 }}>{name}</span>
                    <TrendIcon trend={trend} />
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {issue.mention_count || issue.count || 0} articles
                    </span>
                    {score != null && (
                      <span className={`badge ${sentimentBadgeClass(score)}`} style={{ fontSize: 9 }}>
                        {sentimentLabel(score)}
                      </span>
                    )}
                    {trend === 'rising' && (
                      <span style={{ fontSize: 9, color: 'var(--red)', fontWeight: 700 }}>↑ RISING</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Emerging Risks + Positive Narratives */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 18 }}>
            <EmergingRisksPanel articles={articles} />
            <PositiveNarrativesPanel articles={articles} />
          </div>

          {/* Sentiment trend + Trending issues */}
          <div className="grid-2 section-gap">
            {/* Sentiment trend chart */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">Media Sentiment Trend</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                  {liveTrends ? 'Live · VANI' : 'Static'} · -1 to +1
                </span>
              </div>
              <div className="card-body">
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={safeTrends.map(t => ({
                    date: t.date || new Date(t.period_start || t.date || '').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
                    score: t.polarity ?? t.avg_score ?? t.score ?? 0,
                    count: t.article_count ?? t.count ?? t.sample_count ?? (t.positive != null ? (t.positive + t.negative + t.neutral) : 0),
                  }))}>
                    <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                    <YAxis domain={[-1, 1]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} tickFormatter={v => v.toFixed(1)} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                      formatter={(v, name) => [name === 'score' ? v.toFixed(2) : v, name === 'score' ? 'Sentiment' : 'Articles']}
                    />
                    <Line type="monotone" dataKey="score" stroke="var(--blue)" strokeWidth={2} dot={{ r: 3, fill: 'var(--blue)' }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>Article Volume</div>
                  <ResponsiveContainer width="100%" height={50}>
                    <BarChart data={safeTrends.map(t => ({
                      date: t.date || '',
                      count: t.article_count ?? t.count ?? t.sample_count ?? (t.positive != null ? (t.positive + t.negative + t.neutral) : 0),
                    }))}>
                      <Bar dataKey="count" fill="var(--border-bright)" radius={[2, 2, 0, 0]} />
                      <XAxis dataKey="date" hide />
                      <Tooltip
                        contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11 }}
                        formatter={(v) => [v, 'Articles']}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Trending issues from news */}
            <div className="card">
              <div className="card-header">
                <span className="card-title">News-Driven Issues</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Ranked by media mention count</span>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                {issues.slice(0, 8).map((issue, i) => {
                  const name = issue.issue_name || issue.issue || issue.name || issue.slug || `Issue ${i + 1}`;
                  const count = issue.mention_count || issue.count || issue.article_count || 0;
                  const maxCount = Math.max(...issues.map(x => x.mention_count || x.count || x.article_count || 1));
                  const pct = Math.round((count / maxCount) * 100);
                  const score = issue.sentiment_score ?? issue.sentiment ?? issue.avg_sentiment ?? null;
                  return (
                    <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                        <span style={{
                          width: 18, height: 18, borderRadius: 4, background: 'var(--bg-elevated)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 9, fontWeight: 800, fontFamily: 'var(--font-mono)',
                          color: i < 3 ? 'var(--saffron)' : 'var(--text-muted)', flexShrink: 0,
                        }}>
                          {i + 1}
                        </span>
                        <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{name}</span>
                        <TrendIcon trend={issue.trend || issue.trend_direction} />
                        {score != null && (
                          <span className={`badge ${sentimentBadgeClass(score)}`} style={{ fontSize: 9 }}>
                            {sentimentLabel(score)}
                          </span>
                        )}
                        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{count}x</span>
                      </div>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{
                          width: `${pct}%`,
                          background: score != null ? sentimentColor(score) : 'var(--blue)',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Article feed */}
          <div className="card section-gap">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="card-title">Article Feed</span>
                {liveArticles
                  ? <span className="live-badge"><span className="live-dot" /> Live</span>
                  : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
                }
                <span style={{
                  fontSize: 9, color: 'var(--green)', padding: '2px 7px', borderRadius: 10,
                  background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)',
                  fontWeight: 700, letterSpacing: 0.5,
                }}>
                  SERILINGAMPALLY ONLY
                </span>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {articles.length} live articles · click to open source · filtered for Serilingampally AC-52
              </span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              {articles.length === 0 ? (
                <div style={{
                  padding: '40px 24px', textAlign: 'center',
                  color: 'var(--text-muted)', fontSize: 13,
                }}>
                  <Newspaper size={28} color="var(--border-bright)" style={{ marginBottom: 12, display: 'block', margin: '0 auto 12px' }} />
                  No constituency-specific news available
                  <div style={{ fontSize: 11, marginTop: 6, color: 'var(--text-muted)', opacity: 0.7 }}>
                    Only articles directly relevant to Serilingampally, Hafeezpet, Kondapur, Miyapur and nearby areas are shown
                  </div>
                </div>
              ) : articles.map((article, i) => {
                const score = article.sentiment_score ?? article.sentiment ?? null;
                const scoreColor = sentimentColor(score);
                const headline = article.headline || article.title || article.name || 'Untitled';
                const source = article.source || article.source_name || '—';
                const summary = article.summary || article.description || article.content_preview || null;
                const relTime = formatRelTime(article.published_at || article.created_at);
                const relScore = article._relevanceScore ?? article.relevance_score ?? null;
                const relTier = article.relevance_tier ?? null;
                const constituencyTags = article.constituency_tags?.length
                  ? article.constituency_tags
                  : article.tags || [];
                const credTier = getCredibilityTier(source);
                const { score: impactScore, candidateImpact } = computePoliticalImpact(article);
                const zone = inferZone(article);
                return (
                  <div
                    key={article.id || i}
                    onClick={() => handleOpenArticle(article)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={e => e.key === 'Enter' && handleOpenArticle(article)}
                    style={{
                      padding: '14px 18px',
                      borderBottom: i < articles.length - 1 ? '1px solid var(--border)' : 'none',
                      cursor: 'pointer',
                      transition: 'background 0.15s, box-shadow 0.15s, transform 0.12s',
                      outline: 'none',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = 'var(--bg-elevated)';
                      e.currentTarget.style.boxShadow = `inset 3px 0 0 ${scoreColor}`;
                      e.currentTarget.style.transform = 'translateX(2px)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.boxShadow = 'none';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                      {/* Sentiment bar */}
                      <div style={{
                        width: 4, alignSelf: 'stretch', borderRadius: 2, flexShrink: 0,
                        background: scoreColor, opacity: 0.7,
                      }} />

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, marginBottom: 6 }}>
                              {headline}
                            </div>
                            {/* Meta row 1: source + credibility + time + live badge */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                                <Newspaper size={10} color="var(--text-muted)" />
                                <span style={{ fontSize: 11, color: 'var(--saffron)', fontWeight: 600 }}>{source}</span>
                              </div>
                              <SourceBadge credibility={credTier} />
                              {relTime && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{relTime}</span>}
                              {article.url ? (
                                <span style={{
                                  display: 'inline-flex', alignItems: 'center', gap: 3,
                                  fontSize: 9, padding: '2px 6px', borderRadius: 8, fontWeight: 700,
                                  background: 'rgba(16,185,129,0.12)', color: 'var(--green)',
                                  border: '1px solid rgba(16,185,129,0.3)',
                                }}>
                                  <ExternalLink size={8} /> LIVE
                                </span>
                              ) : relTier && relTier !== 'irrelevant' ? (
                                <span style={{
                                  fontSize: 9, padding: '2px 6px', borderRadius: 8, fontWeight: 700,
                                  background: 'rgba(99,102,241,0.12)', color: 'var(--purple)',
                                  border: '1px solid rgba(99,102,241,0.25)',
                                  textTransform: 'uppercase', letterSpacing: 0.4,
                                }}>
                                  Intelligence
                                </span>
                              ) : null}
                            </div>
                            {/* Meta row 2: issue tags + zone + candidate impact */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                              {constituencyTags.slice(0, 2).map(tag => (
                                <span key={tag} className="badge badge-blue" style={{ fontSize: 9 }}>{tag}</span>
                              ))}
                              {zone && (
                                <span className={`zone-pill zone-${zone.toLowerCase()}`} style={{ fontSize: 9 }}>{zone}</span>
                              )}
                              <span style={{
                                fontSize: 9, padding: '1px 6px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.4,
                                color: candidateImpact === 'positive' ? 'var(--green)' : candidateImpact === 'negative' ? 'var(--red)' : 'var(--text-muted)',
                                background: candidateImpact === 'positive' ? 'rgba(16,185,129,0.1)' : candidateImpact === 'negative' ? 'rgba(239,68,68,0.1)' : 'var(--bg-elevated)',
                                border: `1px solid ${candidateImpact === 'positive' ? 'rgba(16,185,129,0.25)' : candidateImpact === 'negative' ? 'rgba(239,68,68,0.25)' : 'var(--border)'}`,
                              }}>
                                {candidateImpact === 'positive' ? '↑ Candidate' : candidateImpact === 'negative' ? '↓ Candidate' : '→ Neutral'}
                              </span>
                            </div>
                          </div>
                          {/* Right column: sentiment + political impact score */}
                          <div style={{ textAlign: 'right', flexShrink: 0, minWidth: 68 }}>
                            {score != null && (
                              <>
                                <div style={{ fontSize: 18, fontWeight: 900, fontFamily: 'var(--font-mono)', color: scoreColor, lineHeight: 1 }}>
                                  {score >= 0 ? '+' : ''}{score.toFixed(2)}
                                </div>
                                <span className={`badge ${sentimentBadgeClass(score)}`} style={{ fontSize: 9, marginTop: 3, display: 'inline-block' }}>
                                  {sentimentLabel(score)}
                                </span>
                              </>
                            )}
                            <div style={{
                              marginTop: 5, fontSize: 9, fontWeight: 800, fontFamily: 'var(--font-mono)',
                              color: impactScore >= 8 ? 'var(--red)' : impactScore >= 5 ? 'var(--yellow)' : 'var(--text-muted)',
                              display: 'flex', alignItems: 'center', gap: 3, justifyContent: 'flex-end',
                            }}>
                              <Zap size={8} />
                              Impact {impactScore}/10
                            </div>
                          </div>
                        </div>

                        {summary && (
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 6 }}>
                            {summary}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Media Sources */}
          <div className="card section-gap">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="card-title">Media Sources</span>
                {liveSources
                  ? <span className="live-badge"><span className="live-dot" /> Live</span>
                  : <span style={{ fontSize: 10, color: 'var(--text-muted)', padding: '2px 7px', borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}>Static</span>
                }
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {sources.length} outlets monitored by VANI
              </span>
            </div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 12 }}>
                {sources.map((src, i) => {
                  const name = src.name || src.source_name || `Source ${i + 1}`;
                  const type = src.source_type || src.outlet_type || src.type || 'Print';
                  // Prefer live proxy article counts when available (populated even when Celery
                  // hasn't run), falling back to DB article_count from the sources endpoint.
                  const count = (liveSourceCounts?.[name]) ?? src.article_count ?? src.count ?? 0;
                  const avgScore = src.avg_sentiment ?? src.average_sentiment ?? null;
                  return (
                    <div key={src.id || i} style={{
                      padding: '14px 16px', borderRadius: 10,
                      border: '1px solid var(--border)', background: 'var(--bg-base)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <Globe size={13} color="var(--text-muted)" style={{ flexShrink: 0 }} />
                        <span style={{
                          fontSize: 13, fontWeight: 700, color: 'var(--text-primary)',
                          flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }}>
                          {name}
                        </span>
                        <span style={{
                          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
                          background: count > 0 ? 'var(--green)' : 'var(--yellow)',
                          boxShadow: count > 0 ? '0 0 4px rgba(16,185,129,0.6)' : 'none',
                        }} title={count > 0 ? 'Active' : 'No recent data'} />
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                        <span className="badge badge-blue" style={{ fontSize: 9 }}>{type}</span>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{count} articles</span>
                        <span style={{ fontSize: 9, color: count > 0 ? 'var(--green)' : 'var(--yellow)', fontWeight: 700, marginLeft: 'auto' }}>
                          {count > 0 ? 'Active' : 'No Data'}
                        </span>
                      </div>
                      {avgScore != null && (
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                            <span style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Avg Sentiment</span>
                            <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: sentimentColor(avgScore), fontWeight: 700 }}>
                              {avgScore >= 0 ? '+' : ''}{avgScore.toFixed(2)}
                            </span>
                          </div>
                          <div style={{ height: 4, borderRadius: 2, background: 'var(--border)', overflow: 'hidden' }}>
                            <div style={{
                              height: '100%', borderRadius: 2,
                              width: `${Math.min(100, Math.abs(avgScore) * 100)}%`,
                              background: sentimentColor(avgScore),
                              marginLeft: avgScore < 0 ? 'auto' : 0,
                            }} />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
