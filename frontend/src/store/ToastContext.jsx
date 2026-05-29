import { createContext, useContext, useState, useCallback, useRef } from 'react';
import { CheckCircle, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastCtx = createContext(null);

const TYPE = {
  success: { color: 'var(--green)',  bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.3)',  Icon: CheckCircle },
  error:   { color: 'var(--red)',    bg: 'rgba(220,38,38,0.12)',  border: 'rgba(220,38,38,0.3)',   Icon: AlertCircle },
  warning: { color: 'var(--yellow)', bg: 'rgba(217,119,6,0.12)',  border: 'rgba(217,119,6,0.3)',   Icon: AlertTriangle },
  info:    { color: 'var(--blue)',   bg: 'rgba(37,99,235,0.12)',  border: 'rgba(37,99,235,0.3)',   Icon: Info },
};

function ToastStack({ toasts, onRemove }) {
  return (
    <div style={{
      position: 'fixed', top: 24, right: 24, zIndex: 500,
      display: 'flex', flexDirection: 'column', gap: 8,
      maxWidth: 340, pointerEvents: 'none',
    }}>
      {toasts.map(({ id, message, type }) => {
        const { color, bg, border, Icon } = TYPE[type] || TYPE.info;
        return (
          <div key={id} style={{
            display: 'flex', alignItems: 'flex-start', gap: 10,
            padding: '10px 14px', borderRadius: 10,
            background: bg, border: `1px solid ${border}`,
            boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
            animation: 'toast-in 0.22s cubic-bezier(.21,1.02,.73,1) forwards',
            pointerEvents: 'all',
          }}>
            <Icon size={14} color={color} style={{ flexShrink: 0, marginTop: 1 }} />
            <span style={{ flex: 1, fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.5 }}>{message}</span>
            <button
              onClick={() => onRemove(id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', flexShrink: 0, padding: 0, marginLeft: 4 }}
            >
              <X size={11} />
            </button>
          </div>
        );
      })}
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const counter = useRef(0);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const safe = message == null ? '' : typeof message === 'string' ? message : typeof message === 'number' ? String(message) : message?.message || message?.title || '[notification]';
    const id = ++counter.current;
    setToasts(prev => [...prev, { id, message: safe, type }]);
    if (duration > 0) setTimeout(() => removeToast(id), duration);
    return id;
  }, [removeToast]);

  return (
    <ToastCtx.Provider value={{ addToast }}>
      {children}
      <ToastStack toasts={toasts} onRemove={removeToast} />
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);
