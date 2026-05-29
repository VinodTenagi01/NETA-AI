import client from './client';

const CID = '11111111-0052-4000-8000-000000000001';

const cid_param = (cid = CID) => `constituency_id=${cid}`;

export const getCommandCentreOverview = (cid = CID) =>
  client.get(`/intelligence/command-centre/overview?${cid_param(cid)}`).then(r => r.data);

export const getGroundPulseLive = (cid = CID) =>
  client.get(`/intelligence/ground-pulse/live?${cid_param(cid)}`).then(r => r.data);

export const getAlertsLive = (cid = CID) =>
  client.get(`/intelligence/alerts/live?${cid_param(cid)}`).then(r => r.data);

export const markAlertDone = (alertId) =>
  client.patch(`/intelligence/alerts/${alertId}/done`);

export const getBoothHeatmap = (cid = CID) =>
  client.get(`/intelligence/booths/heatmap?${cid_param(cid)}`).then(r => r.data);

export const getSentimentTrends = (cid = CID, days = 14) =>
  client.get(`/intelligence/sentiment/trends?${cid_param(cid)}&period_days=${days}`).then(r => r.data);

export const getOppositionIntelligence = (cid = CID) =>
  client.get(`/intelligence/opposition-intelligence?${cid_param(cid)}`).then(r => r.data);

export const getCandidateBrief = (cid = CID) =>
  client.get(`/intelligence/candidate-brief?${cid_param(cid)}`).then(r => r.data);

export const generateBrief = (cid = CID, briefType = 'daily') =>
  client.post(`/intelligence/briefs/generate`, { constituency_id: cid, brief_type: briefType }).then(r => r.data);

export const getWinProbability = () =>
  client.get('/v1/predictions/win-probability?constituency_id=11111111-0052-4000-8000-000000000001').then(r => r.data);
