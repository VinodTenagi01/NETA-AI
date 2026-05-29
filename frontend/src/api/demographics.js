import client from './client';

/**
 * Get aggregated demographic profile for a constituency.
 * Falls back to Chandanagar static data when no DB records found.
 * @param {string} constituencyId - UUID
 */
export async function getConstituencyDemographics(constituencyId) {
  const res = await client.get(`/demographics/constituency/${constituencyId}`);
  return res.data;
}

/**
 * Get per-booth demographic breakdown.
 * @param {string} constituencyId - UUID
 * @param {object} params - { page, page_size }
 */
export async function getBoothDemographics(constituencyId, { page = 1, page_size = 50 } = {}) {
  const res = await client.get(`/demographics/booths/${constituencyId}`, {
    params: { page, page_size },
  });
  return res.data;
}

/**
 * Get community influencers for a constituency.
 * @param {string} constituencyId - UUID
 * @param {object} params - { alignment, community }
 */
export async function getInfluencers(constituencyId, { alignment, community } = {}) {
  const params = {};
  if (alignment) params.alignment = alignment;
  if (community) params.community = community;
  const res = await client.get(`/demographics/influencers/${constituencyId}`, { params });
  return res.data;
}
