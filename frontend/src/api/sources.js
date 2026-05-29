import client from './client';

/**
 * List all registered news sources.
 * @param {object} params - { is_active }
 */
export async function getNewsSources({ is_active } = {}) {
  const params = {};
  if (is_active !== undefined) params.is_active = is_active;
  const res = await client.get('/v1/news/sources', { params });
  return res.data;
}

export async function addNewsSource(payload) {
  const res = await client.post('/v1/news/sources', payload);
  return res.data;
}

export async function updateNewsSource(sourceId, patch) {
  const res = await client.patch(`/v1/news/sources/${sourceId}`, patch);
  return res.data;
}

export async function pollSource(sourceId) {
  const res = await client.post(`/v1/news/ingest`, { feed_sources: [sourceId] });
  return res.data;
}

export async function deleteNewsSource(sourceId) {
  await client.delete(`/v1/news/sources/${sourceId}`);
}

export async function getIngestionStatus() {
  const res = await client.get('/v1/news/ingestion/logs', { params: { page_size: 5 } });
  return res.data;
}
