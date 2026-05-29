import { useState } from 'react';
import { ChevronRight, CheckCircle } from 'lucide-react';
import { alerts } from '../data/mockData';

const typeLabel = {
  critical: { label: 'CRITICAL', color: 'var(--red)' },
  warning:  { label: 'WARNING',  color: 'var(--yellow)' },
  info:     { label: 'INFO',     color: 'var(--blue)' },
  success:  { label: 'OK',       color: 'var(--green)' },
};

export default function AlertFeed({ maxItems }) {
  const [dismissed, setDismissed] = useState(new Set());
  const visible = (maxItems ? alerts.slice(0, maxItems) : alerts)
    .filter(a => !dismissed.has(a.id));

  return (
    <div>
      {visible.map((alert) => (
        <div key={alert.id} className={`alert-item ${alert.type}`}>
          <div className="alert-header">
            <span
              style={{
                fontSize: 9, fontWeight: 800, letterSpacing: 1,
                color: typeLabel[alert.type]?.color,
              }}
            >
              {typeLabel[alert.type]?.label}
            </span>
            <span className="alert-agent">{alert.agent}</span>
            <span className="alert-time">{alert.time}</span>
          </div>
          <div className="alert-text">{alert.message}</div>
          {alert.action && !alert.actionDone && (
            <div
              className="alert-action"
              onClick={() => setDismissed(new Set([...dismissed, alert.id]))}
            >
              <ChevronRight size={10} />
              {alert.action}
            </div>
          )}
          {alert.actionDone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 6, fontSize: 10, color: 'var(--green)' }}>
              <CheckCircle size={10} />
              Resolved
            </div>
          )}
        </div>
      ))}
      {visible.length === 0 && (
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
          No active alerts
        </div>
      )}
    </div>
  );
}
