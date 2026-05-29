import { Component } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[NETA.AI] Render error caught:', error.message,
      info.componentStack?.split('\n')[1]?.trim() || '');
  }

  reset() {
    this.setState({ hasError: false, error: null });
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    const { label = 'Component unavailable', compact, fallback } = this.props;

    // Custom fallback passed by parent
    if (fallback) return fallback;

    // Compact inline variant — for widgets, charts, panels
    if (compact) {
      return (
        <div style={{
          padding: '8px 12px', borderRadius: 7,
          background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.18)',
          display: 'flex', alignItems: 'center', gap: 7,
          fontSize: 11, color: 'var(--text-muted)',
        }}>
          <AlertCircle size={11} color="var(--red)" style={{ flexShrink: 0 }} />
          <span style={{ flex: 1 }}>{label}</span>
          <button
            onClick={() => this.reset()}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-muted)', padding: '1px 4px',
              display: 'flex', alignItems: 'center', gap: 3, fontSize: 9,
            }}
          >
            <RefreshCw size={8} /> Retry
          </button>
        </div>
      );
    }

    // Full-page fallback — for top-level app wrapper
    return (
      <div style={{
        height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-base)', flexDirection: 'column', gap: 16, padding: 40, textAlign: 'center',
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: 'var(--red)', textTransform: 'uppercase', marginBottom: 4 }}>
          NETA-CORE · Runtime Error
        </div>
        <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--text-primary)' }}>Something went wrong</div>
        <div style={{
          fontSize: 12, color: 'var(--text-muted)', maxWidth: 420, lineHeight: 1.7,
          padding: '10px 16px', background: 'var(--bg-elevated)', borderRadius: 8,
          border: '1px solid var(--border)', fontFamily: 'var(--font-mono)',
        }}>
          {this.state.error?.message || 'An unexpected error occurred.'}
        </div>
        <button
          className="btn btn-primary"
          onClick={() => { this.reset(); window.location.reload(); }}
          style={{ marginTop: 8 }}
        >
          Reload Application
        </button>
      </div>
    );
  }
}
