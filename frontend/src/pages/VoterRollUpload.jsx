import { useCallback, useEffect, useRef, useState } from 'react';
import { Upload, CheckCircle, AlertTriangle, FileText, RefreshCw, X, Download, ChevronDown, ChevronUp } from 'lucide-react';
import { uploadVoterRoll, getIngestionLogs, getIngestionLog, retryIngestion, pollIngestionStatus } from '../api/ingestion';
import { useToast } from '../store/ToastContext';

const ACCEPTED = '.pdf,.csv,.xlsx,.xls';

const STATUS_COLORS = {
  completed: 'var(--green)',
  partial: 'var(--yellow)',
  failed: 'var(--red)',
  pending: 'var(--saffron)',
  running: 'var(--blue)',
  dry_run: 'var(--purple)',
};

const STATUS_LABELS = {
  completed: 'Completed', partial: 'Partial', failed: 'Failed',
  pending: 'Queued', running: 'Running', dry_run: 'Dry Run',
};

function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || 'var(--text-muted)';
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
      background: `${color}20`, border: `1px solid ${color}50`,
      color, textTransform: 'uppercase', letterSpacing: 0.5,
    }}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function ProgressBar({ pct }) {
  const color = pct >= 100 ? 'var(--green)' : 'var(--saffron)';
  return (
    <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden', marginTop: 8 }}>
      <div style={{
        height: '100%', borderRadius: 3,
        width: `${Math.min(100, pct)}%`,
        background: `linear-gradient(90deg, ${color}cc, ${color})`,
        transition: 'width 0.4s ease',
      }} />
    </div>
  );
}

function LogRow({ log, onRetry, onExpand, expanded }) {
  const hasErrors = log.has_errors || log.records_failed > 0;
  return (
    <>
      <tr style={{ borderLeft: `3px solid ${STATUS_COLORS[log.status] || 'var(--border)'}` }}>
        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
          {new Date(log.created_at).toLocaleString('en-IN', {
            day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true,
          })}
        </td>
        <td style={{ maxWidth: 220 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileText size={12} color="var(--text-muted)" />
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {log.file_name || '—'}
            </span>
          </div>
        </td>
        <td><StatusBadge status={log.status} /></td>
        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--green)' }}>
          {(log.records_processed || 0).toLocaleString()}
        </td>
        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: log.records_failed > 0 ? 'var(--red)' : 'var(--text-muted)' }}>
          {(log.records_failed || 0).toLocaleString()}
        </td>
        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
          {(log.records_skipped || 0).toLocaleString()}
        </td>
        <td>
          <div style={{ display: 'flex', gap: 6 }}>
            {hasErrors && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => onExpand(log.id)}
                style={{ padding: '2px 8px', fontSize: 10, display: 'flex', alignItems: 'center', gap: 4 }}
              >
                {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />} Errors
              </button>
            )}
            {['failed', 'partial'].includes(log.status) && (
              <button
                className="btn btn-outline btn-sm"
                onClick={() => onRetry(log.id)}
                style={{ padding: '2px 8px', fontSize: 10, display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <RefreshCw size={10} /> Retry
              </button>
            )}
          </div>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={7} style={{ padding: '8px 16px', background: 'var(--bg-elevated)' }}>
            <div style={{ fontSize: 11, color: 'var(--red)', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', maxHeight: 120, overflow: 'auto' }}>
              {log.error_detail
                ? (Array.isArray(log.error_detail) ? log.error_detail.join('\n') : JSON.stringify(log.error_detail, null, 2))
                : 'No error detail available.'
              }
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function VoterRollUpload() {
  const { showToast } = useToast();

  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [dryRun, setDryRun] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadPct, setUploadPct] = useState(0);
  const [currentJob, setCurrentJob] = useState(null);
  const stopPollRef = useRef(null);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fileInputRef = useRef(null);

  const loadHistory = useCallback(async (p = 1) => {
    setHistoryLoading(true);
    try {
      const data = await getIngestionLogs({ source_type: 'voter_roll', page: p });
      setHistory(data.items || []);
      setTotalPages(data.pages || 1);
    } catch { /* Backend unavailable */ }
    finally { setHistoryLoading(false); }
  }, []);

  useEffect(() => { loadHistory(page); }, [page, loadHistory]);

  const handleDrop = useCallback(e => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadPct(0);
    setCurrentJob(null);
    stopPollRef.current?.();

    const constituencyId = localStorage.getItem('neta_constituency_id') || '11111111-0052-4000-8000-000000000001';

    try {
      const result = await uploadVoterRoll(file, constituencyId, dryRun, pct => setUploadPct(pct));
      setCurrentJob({ ...result, status: 'pending' });
      showToast({ type: 'success', message: `Upload received: ${result.file_name}` });

      stopPollRef.current = pollIngestionStatus(
        result.log_id,
        updated => {
          setCurrentJob(prev => ({ ...prev, ...updated }));
          if (['completed', 'failed', 'partial', 'dry_run'].includes(updated.status)) {
            loadHistory(1);
            showToast({
              type: updated.status === 'completed' ? 'success' : 'error',
              message: updated.status === 'completed'
                ? `Ingestion complete: ${updated.records_processed} records loaded.`
                : 'Ingestion failed. Check error log.',
            });
          }
        },
        3000,
      );
    } catch (err) {
      const detail = err.response?.data?.detail || 'Upload failed. Check the backend is running.';
      showToast({ type: 'error', message: detail });
      setCurrentJob({ status: 'failed', error: detail, file_name: file.name });
    } finally {
      setUploading(false);
    }
  };

  const handleRetry = async logId => {
    try {
      await retryIngestion(logId);
      showToast({ type: 'success', message: 'Retry queued.' });
      loadHistory(page);
    } catch (err) {
      showToast({ type: 'error', message: err.response?.data?.detail || 'Retry failed.' });
    }
  };

  const handleExpand = async logId => {
    if (expandedLogId === logId) { setExpandedLogId(null); return; }
    setExpandedLogId(logId);
    try {
      const detail = await getIngestionLog(logId);
      setHistory(prev => prev.map(l => l.id === logId ? { ...l, error_detail: detail.error_detail } : l));
    } catch { /* ignore */ }
  };

  const downloadReport = () => {
    if (!history.length) return;
    const rows = [
      ['Date', 'File', 'Status', 'Processed', 'Failed', 'Skipped'],
      ...history.map(l => [l.created_at, l.file_name || '', l.status, l.records_processed, l.records_failed, l.records_skipped]),
    ];
    const blob = new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'ingestion_history.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const isDone = ['completed', 'failed', 'partial', 'dry_run'].includes(currentJob?.status);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Voter Roll Upload</div>
          <div className="page-subtitle">EC Electoral Roll Ingestion · PDF, CSV, XLSX supported</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-outline btn-sm" onClick={() => loadHistory(1)} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <RefreshCw size={12} /> Refresh
          </button>
          <button className="btn btn-outline btn-sm" onClick={downloadReport} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Download size={12} /> Export CSV
          </button>
        </div>
      </div>

      <div className="page-body">

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 18, alignItems: 'start', marginBottom: 18 }}>

          {/* Upload zone */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Upload Voter Roll File</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Max 100 MB · PDF / CSV / XLSX</span>
            </div>
            <div className="card-body">
              <div
                onDrop={handleDrop}
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onClick={() => !file && fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${dragging ? 'var(--saffron)' : file ? 'var(--green)' : 'var(--border)'}`,
                  borderRadius: 12, padding: '32px 24px', textAlign: 'center',
                  cursor: file ? 'default' : 'pointer',
                  background: dragging ? 'rgba(249,115,22,0.04)' : file ? 'rgba(16,185,129,0.04)' : 'transparent',
                  transition: 'all 0.2s', marginBottom: 16,
                }}
              >
                <input ref={fileInputRef} type="file" accept={ACCEPTED} style={{ display: 'none' }}
                  onChange={e => setFile(e.target.files?.[0] || null)} />
                {file ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 6 }}>
                      <FileText size={20} color="var(--green)" />
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{file.name}</span>
                      <button onClick={e => { e.stopPropagation(); setFile(null); setCurrentJob(null); }}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
                        <X size={14} />
                      </button>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {(file.size / 1024).toFixed(1)} KB · {file.type || 'unknown format'}
                    </div>
                  </div>
                ) : (
                  <div>
                    <Upload size={28} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>
                      Drop file here or click to browse
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      EC-format PDF · CSV with voter columns · Excel XLSX
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <input type="checkbox" id="dryRun" checked={dryRun}
                  onChange={e => setDryRun(e.target.checked)}
                  style={{ width: 14, height: 14, accentColor: 'var(--saffron)' }} />
                <label htmlFor="dryRun" style={{ fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                  Dry run — validate without writing to database
                </label>
              </div>

              <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}
                style={{ width: '100%', justifyContent: 'center', padding: '12px 0', fontSize: 13 }}>
                {uploading ? (
                  <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> Uploading… {uploadPct}%</>
                ) : (
                  <><Upload size={14} /> Start Ingestion</>
                )}
              </button>

              {uploading && <ProgressBar pct={uploadPct} />}
            </div>
          </div>

          {/* Sidebar: current job + format guide */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

            {currentJob && (
              <div className="card" style={{ border: `1px solid ${STATUS_COLORS[currentJob.status] || 'var(--border)'}50` }}>
                <div className="card-header">
                  <span className="card-title">Current Job</span>
                  <StatusBadge status={currentJob.status} />
                </div>
                <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {currentJob.file_name}
                  </div>
                  {!isDone && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--saffron)' }}>
                      <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} />
                      Processing — polling for updates…
                    </div>
                  )}
                  {isDone && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {[
                        { label: 'Inserted', val: currentJob.records_processed, color: 'var(--green)' },
                        { label: 'Failed', val: currentJob.records_failed, color: currentJob.records_failed > 0 ? 'var(--red)' : 'var(--text-muted)' },
                        { label: 'Skipped', val: currentJob.records_skipped, color: 'var(--text-muted)' },
                      ].map(({ label, val, color }) => (
                        <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</span>
                          <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)', color }}>{(val ?? 0).toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {currentJob.status === 'failed' && currentJob.error && (
                    <div style={{ fontSize: 10, color: 'var(--red)', background: 'var(--red-dim)', borderRadius: 6, padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>
                      {currentJob.error}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="card">
              <div className="card-header"><span className="card-title">Supported Formats</span></div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { ext: 'PDF', desc: 'EC electoral roll PDF (text or scanned)', color: 'var(--red)' },
                  { ext: 'CSV', desc: 'ec_id, name, age, gender, booth columns', color: 'var(--green)' },
                  { ext: 'XLSX', desc: 'Excel format — same column schema', color: 'var(--blue)' },
                ].map(({ ext, desc, color }) => (
                  <div key={ext} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: `${color}20`, color, border: `1px solid ${color}40`, flexShrink: 0 }}>{ext}</span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{desc}</span>
                  </div>
                ))}
                <div style={{ marginTop: 2, padding: '8px 10px', background: 'var(--bg-elevated)', borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                    Required columns: <code style={{ color: 'var(--saffron)', fontFamily: 'var(--font-mono)' }}>ec_voter_id, voter_name, age, gender, booth_number</code>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* History table */}
        <div className="card section-gap">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="card-title">Ingestion History</span>
              {historyLoading && <RefreshCw size={12} color="var(--text-muted)" style={{ animation: 'spin 1s linear infinite' }} />}
            </div>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Voter roll import audit trail</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th><th>File</th><th>Status</th><th>Inserted</th><th>Failed</th><th>Skipped</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {!historyLoading && history.length === 0 && (
                  <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px', fontSize: 12 }}>
                    No ingestion history. Upload a voter roll to begin.
                  </td></tr>
                )}
                {history.map(log => (
                  <LogRow key={log.id} log={log} onRetry={handleRetry}
                    onExpand={handleExpand} expanded={expandedLogId === log.id} />
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
              <button className="btn btn-outline btn-sm" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 8px' }}>Page {page} of {totalPages}</span>
              <button className="btn btn-outline btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
            </div>
          )}
        </div>

        <div style={{ padding: '12px 16px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border)', fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.7 }}>
          <strong style={{ color: 'var(--text-secondary)' }}>Data Governance:</strong> All uploads are logged for audit. Duplicate voter IDs are automatically skipped. Files retained for 90 days. Requires Campaign Manager role.
        </div>

      </div>
    </div>
  );
}
