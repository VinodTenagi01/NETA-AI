import client from './client';

// DB-backed articles feed (NLP-processed, constituency-scoped)
export const getArticles = (limit = 15) =>
  client.get(`/v1/news/articles?limit=${limit}`).then(r => r.data);

// Live headlines — alias to articles feed (no separate headlines endpoint)
export const getLiveHeadlines = (limit = 30) =>
  client.get(`/v1/news/articles?limit=${limit}`).then(r => r.data);

// News sources health
export const getNewsSources = () =>
  client.get('/v1/news/sources/health').then(r => r.data);

// Sentiment trend over time
export const getNewsSentimentTrends = () =>
  client.get('/v1/news/trends/sentiment').then(r => r.data);

// Active narrative clusters (replaces trending issues)
export const getNewsTrendingIssues = () =>
  client.get('/v1/news/narratives/active').then(r => r.data);

// Morning digest — no dedicated endpoint; return articles feed
export const getMorningDigest = () =>
  client.get('/v1/news/articles?limit=5').then(r => r.data);

// Article detail
export const getArticleDetail = (articleId) =>
  client.get(`/v1/news/articles/${articleId}`).then(r => r.data);

// Feeds health (alias to sources/health)
export const getFeedsHealth = () =>
  client.get('/v1/news/sources/health').then(r => r.data);
