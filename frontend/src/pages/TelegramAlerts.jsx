import { useEffect, useState, useCallback } from 'react';
import { Send, CheckCircle, XCircle, AlertCircle, RefreshCw, MessageSquare } from 'lucide-react';
import client from '../api/client';
import { useToast } from '../store/ToastContext';

function StatCard({ label, value, sub, ok }) {
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '16px 20px', minWidth: 160,
    }}>
      <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {ok === true && <CheckCircle size={14} color="var(--green)" />}
        {ok === false && <XCircle size={14} color="var(--red)" />}
        <span style={{ fontSize: 16, fontWeight: 800, color: ok === false ? 'var(--red)' : ok === true ? 'var(--green)' : 'var(--text-primary)' }}>
          {value ?? '—'}
        </span>
      </div>
      {sub && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

const SEV_COLOR = {
  CRITICAL: 'var(--red)',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: 'var(--green)',
  INFO: 'var(--text-secondary)',
};

export default function TelegramAlerts() {
  const { showToast } = useToast();
  const [health, setHealth] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await client.get('/telegram/health');
      setHealth(res.data);
    } catch {
      setHealth(null);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await client.get('/intelligence/alerts/live', { params: { limit: 15 } });
      const data = res.data;
      const list = data.alerts ?? data.items ?? (Array.isArray(data) ? data : []);
      setAlerts(list.slice(0, 15));
    } catch {
      setAlerts([]);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchHealth(), fetchAlerts()]).finally(() => setLoading(false));
  }, [fetchHealth, fetchAlerts]);

  const handleTest = async () => {
    setTesting(true);
    try {
      await client.get('/telegram/test');
      showToast('Test message sent to Telegram', 'success');
      await fetchHealth();
    } catch (e) {
      const detail = e.response?.data?.detail ?? 'Test message failed';
      showToast(detail, 'error');
    } finally {
      setTesting(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    Promise.all([fetchHealth(), fetchAlerts()]).finally(() => setLoading(false));
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 26, height: 26, border: '2px solid var(--border)', borderTop: '2px solid var(--saffron)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      </div>
    );
  }

  const configured = health?.configured ?? false;
  const enabled = health?.enabled ?? false;
  const botUsername = health?.bot_username;
  const chatIdSet = health?.chat_id_set ?? false;

  return (
    <div style={{ padding: '24px 28px', maxWidth: 900, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <MessageSquare size={20} color="var(--saffron)" />
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>Telegram Alerts</h1>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Bot notification status and recent activity</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={handleRefresh}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 7, background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
          >
            <RefreshCw size={12} />
            Refresh
          </button>
          <button
            onClick={handleTest}
            disabled={!configured || testing}
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 7, background: configured ? 'var(--saffron)' : 'var(--bg-elevated)', border: '1px solid var(--border)', color: configured ? '#000' : 'var(--text-muted)', fontSize: 12, fontWeight: 700, cursor: configured ? 'pointer' : 'not-allowed', opacity: testing ? 0.6 : 1 }}
          >
            <Send size={12} />
            {testing ? 'Sending…' : 'Send Test'}
          </button>
        </div>
      </div>

      {/* Status cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Integration" value={enabled && configured ? 'Active' : configured ? 'Configured' : 'Not Configured'} ok={enabled && configured} />
        <StatCard label="Bot Username" value={botUsername ? `@${botUsername}` : 'Unknown'} ok={!!botUsername} sub="Telegram identity" />
        <StatCard label="Chat ID" value={chatIdSet ? 'Configured' : 'Missing'} ok={chatIdSet} sub="Destination channel" />
        <StatCard label="API Status" value={health?.status ?? 'Unknown'} ok={health?.status === 'healthy'} sub="Health check" />
      </div>

      {/* Config warning */}
      {!configured && (
        <div style={{
          padding: '12px 16px', borderRadius: 8, marginBottom: 20,
          background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)',
          display: 'flex', alignItems: 'flex-start', gap: 10,
        }}>
          <AlertCircle size={14} color="#eab308" style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#eab308' }}>Telegram not configured</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your Render environment variables to enable notifications.
            </div>
          </div>
        </div>
      )}

      {/* Recent alerts */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 10 }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>Recent Alerts</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Last 15 system alerts</span>
        </div>

        {alerts.length === 0 ? (
          <div style={{ padding: '32px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
            No alerts in the system yet
          </div>
        ) : (
          <div>
            {alerts.map((a, i) => {
              const sev = a.severity ?? 'INFO';
              const color = SEV_COLOR[sev] ?? 'var(--text-secondary)';
              const ts = a.created_at ?? a.timestamp ?? null;
              return (
                <div key={a.id ?? i} style={{
                  padding: '12px 20px',
                  borderBottom: i < alerts.length - 1 ? '1px solid var(--border)' : 'none',
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: color, flexShrink: 0, marginTop: 5 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {a.title ?? a.alert_type ?? 'Alert'}
                      </span>
                      <span style={{ fontSize: 9, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: 0.5, flexShrink: 0 }}>{sev}</span>
                    </div>
                    {a.description && (
                      <div style={{ fontSize: 10, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {a.description}
                      </div>
                    )}
                  </div>
                  {ts && (
                    <div style={{ fontSize: 9, color: 'var(--text-dim)', flexShrink: 0, fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                      {new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
