import { X, Command } from 'lucide-react';

const NAV_SHORTCUTS = [
  { keys: ['G', 'C'], label: 'Command Centre' },
  { keys: ['G', 'B'], label: 'Candidate Brief' },
  { keys: ['G', 'I'], label: 'Constituency Intelligence' },
  { keys: ['G', 'G'], label: 'Ground Pulse' },
  { keys: ['G', 'O'], label: 'Opposition Intelligence' },
  { keys: ['G', 'N'], label: 'News Intelligence' },
  { keys: ['G', 'M'], label: 'Booth Management' },
  { keys: ['G', 'D'], label: 'Booth Intel Data' },
  { keys: ['G', 'R'], label: 'Field Reports' },
  { keys: ['G', 'A'], label: 'Admin Dashboard' },
  { keys: ['G', 'X'], label: 'Demographics' },
  { keys: ['G', 'S'], label: 'Data Sources' },
  { keys: ['G', 'V'], label: 'Voter Roll Upload' },
];

const GLOBAL_SHORTCUTS = [
  { keys: ['⌘', 'K'], label: 'Open Command Palette' },
  { keys: ['?'], label: 'Show Keyboard Shortcuts' },
  { keys: ['Esc'], label: 'Close Overlay / Palette' },
];

function Kbd({ children }) {
  return (
    <kbd style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 22, padding: '2px 6px', borderRadius: 5,
      background: 'var(--bg-base)', border: '1px solid var(--border-bright)',
      fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 700,
      color: 'var(--text-secondary)',
      boxShadow: '0 1px 0 rgba(0,0,0,0.4)',
    }}>
      {children}
    </kbd>
  );
}

export default function ShortcutsOverlay({ onClose }) {
  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 400,
        background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'palette-in 0.12s ease',
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 520,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 14,
          boxShadow: '0 32px 100px rgba(0,0,0,0.65)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '13px 18px', borderBottom: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Command size={14} color="var(--saffron)" />
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>Keyboard Shortcuts</span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={15} />
          </button>
        </div>

        <div style={{ padding: '16px 18px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {/* Navigation */}
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              Navigation
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {NAV_SHORTCUTS.map(({ keys, label }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    {keys.map((k, i) => (
                      <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                        <Kbd>{k}</Kbd>
                        {i < keys.length - 1 && (
                          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>then</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Global */}
          <div>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}>
              Global
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {GLOBAL_SHORTCUTS.map(({ keys, label }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                    {keys.map((k, i) => (
                      <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                        <Kbd>{k}</Kbd>
                        {i < keys.length - 1 && (
                          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>+</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 20, padding: '10px 12px', background: 'var(--bg-base)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                <span style={{ color: 'var(--saffron)', fontWeight: 700 }}>G-key navigation:</span><br />
                Press <Kbd>G</Kbd> then a letter within 1 second to jump to any page instantly.
              </div>
            </div>
          </div>
        </div>

        <div style={{
          padding: '8px 18px', borderTop: '1px solid var(--border)',
          background: 'var(--bg-base)', fontSize: 10, color: 'var(--text-muted)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>NETA.AI Keyboard Reference</span>
          <span>Press <Kbd>Esc</Kbd> or <Kbd>?</Kbd> to close</span>
        </div>
      </div>
    </div>
  );
}
