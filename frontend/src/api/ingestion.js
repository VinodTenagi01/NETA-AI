import client from './client';

/**
 * Upload a voter roll file (PDF/CSV/XLSX) to the backend for ingestion.
 * @param {File} file - The file object from an <input type="file">
 * @param {string} constituencyId - UUID of the target constituency
 * @param {boolean} dryRun - If true, validate without writing to DB
 * @param {function} onProgress - Optional upload progress callback (0–100)
 * @returns {Promise<{log_id, file_name, file_size_bytes, dispatched_async, message}>}
 */
export async function uploadVoterRoll(file, constituencyId, dryRun = false, onProgress) {
  const form = new FormData();
  form.append('file', file);
  form.append('constituency_id', constituencyId);
  form.append('dry_run', String(dryRun));

  const res = await client.post('/admin/ingestion/voter-roll/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? e => {
          const pct = e.total ? Math.round((e.loaded / e.total) * 100) : 0;
          onProgress(pct);
        }
      : undefined,
  });
  return res.data;
}

/**
 * Get paginated ingestion history.
 * @param {object} params - { page, page_size, source_type, status }
 */
export async function getIngestionLogs({ page = 1, page_size = 20, source_type, status } = {}) {
  const params = { page, page_size };
  if (source_type) params.source_type = source_type;
  if (status) params.status = status;
  const res = await client.get('/v1/news/ingestion/logs', { params });
  return res.data;
}

export async function getIngestionLog(logId) {
  const res = await client.get(`/v1/news/ingestion/logs/${logId}`);
  return res.data;
}

export async function retryIngestion(logId) {
  const res = await client.post(`/admin/ingestion/voter-roll/retry/${logId}`);
  return res.data;
}

/**
 * Poll for ingestion log status until completed/failed or timeout.
 * @param {string} logId - UUID to poll
 * @param {function} onUpdate - Called with log data on each poll
 * @param {number} intervalMs - Poll interval in ms (default 3000)
 * @param {number} maxAttempts - Max polls before giving up (default 100 = ~5 min)
 * @returns {function} stopPolling - Call to cancel polling
 */
export function pollIngestionStatus(logId, onUpdate, intervalMs = 3000, maxAttempts = 100) {
  let active = true;
  let attempts = 0;

  const DONE = ['completed', 'failed', 'partial', 'dry_run'];

  const poll = async () => {
    while (active) {
      try {
        const log = await getIngestionLog(logId);
        onUpdate(log);
        if (DONE.includes(log.status)) {
          active = false;
          break;
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
      attempts += 1;
      if (attempts >= maxAttempts) {
        onUpdate({
          status: 'failed',
          records_processed: 0,
          records_failed: 0,
          records_skipped: 0,
          error: 'Polling timed out after 5 minutes — check server logs.',
        });
        active = false;
        break;
      }
      await new Promise(r => setTimeout(r, intervalMs));
    }
  };

  poll();
  return () => { active = false; };
}
