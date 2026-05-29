import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, MapPin, Activity, Map, FileText, ShieldAlert,
  Newspaper, ClipboardList, Settings, Search, ArrowRight, Command, Table2,
  Users, Database, Upload,
} from 'lucide-react';

const COMMANDS = [
  { id: 'command-centre',            label: 'Command Centre',           icon: LayoutDashboard, path: '/command-centre',            hint: 'G C', tags: 'overview dashboard alerts live' },
  { id: 'candidate-brief',           label: 'Candidate Brief',          icon: FileText,        path: '/candidate-brief',            hint: 'G B', tags: 'brief ai candidate generate' },
  { id: 'constituency-intelligence', label: 'Constituency Intelligence', icon: MapPin,          path: '/constituency-intelligence',  hint: 'G I', tags: 'demographics issues analysis constituency' },
  { id: 'ground-pulse',              label: 'Ground Pulse',             icon: Activity,        path: '/ground-pulse',               hint: 'G G', tags: 'mood field reports workers vayu zone' },
  { id: 'opposition-intelligence',   label: 'Opposition Intelligence',  icon: ShieldAlert,     path: '/opposition-intelligence',    hint: 'G O', tags: 'vivek candidates rumours threat sightings' },
  { id: 'news-intelligence',         label: 'News Intelligence',        icon: Newspaper,       path: '/news-intelligence',          hint: 'G N', tags: 'vani media articles sentiment digest' },
  { id: 'booth-management',          label: 'Booth Management',         icon: Map,             path: '/booth-management',           hint: 'G M', tags: 'booths heatmap coverage pulse reports' },
  { id: 'field-reports',             label: 'Field Reports',            icon: ClipboardList,   path: '/field-reports',              hint: 'G R', tags: 'reports submit escalation panna pramukh' },
  { id: 'admin',                     label: 'Admin Dashboard',          icon: Settings,        path: '/admin',                      hint: 'G A', tags: 'system admin queues scores ingestion' },
  { id: 'booth-intelligence',        label: 'Booth Raw Data',           icon: Table2,          path: '/booth-intelligence',         hint: 'G D', tags: 'booth raw data voters mood table intelligence export' },
  { id: 'constituency-demographics', label: 'Constituency Demographics', icon: Users,           path: '/constituency-demographics',  hint: 'G X', tags: 'demographics census population age community zone literacy' },
  { id: 'data-sources',              label: 'Data Sources',             icon: Database,        path: '/data-sources',               hint: 'G S', tags: 'sources vani vayu vivek vichar ec census ingestion pipeline registry' },
  { id: 'voter-roll-upload',         label: 'Voter Roll Upload',        icon: Upload,          path: '/voter-roll-upload',          hint: 'G V', tags: 'upload voter roll ec xml csv delta booth parsing' },
];

function Highlight({ text, query }) {
  if (!query) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark style={{ background: 'rgba(249,115,22,0.28)', color: 'var(--saffron)', borderRadius: 2, padding: '0 1px' }}>
        {text.slice(idx, idx + query.length)}
      </mark>
      {text.slice(idx + query.length)}
    </>
  );
}

export default function CommandPalette({ open, onClose }) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef(null);
  const listRef = useRef(null);
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    if (!query.trim()) return COMMANDS;
    const q = query.toLowerCase();
    return COMMANDS.filter(cmd =>
      cmd.label.toLowerCase().includes(q) || cmd.tags.includes(q)
    );
  }, [query]);

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  useEffect(() => { setSelected(0); }, [query]);

  const goTo = (cmd) => {
    navigate(cmd.path);
    onClose();
  };

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelected(s => {
          const next = Math.min(s + 1, filtered.length - 1);
          listRef.current?.children[next]?.scrollIntoView({ block: 'nearest' });
          return next;
        });
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelected(s => {
          const next = Math.max(s - 1, 0);
          listRef.current?.children[next]?.scrollIntoView({ block: 'nearest' });
          return next;
        });
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selected]) goTo(filtered[selected]);
      }
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, selected, filtered]);

  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(0,0,0,0.68)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        paddingTop: '16vh',
        animation: 'palette-in 0.12s ease',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%', maxWidth: 560,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: 14,
          boxShadow: '0 32px 100px rgba(0,0,0,0.65), 0 0 0 1px rgba(249,115,22,0.06)',
          overflow: 'hidden',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Input */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '13px 16px',
          borderBottom: '1px solid var(--border)',
        }}>
          <Search size={15} color="var(--text-muted)" style={{ flexShrink: 0 }} />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search pages, features, agents…"
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              fontSize: 14, color: 'var(--text-primary)', fontFamily: 'inherit',
            }}
          />
          <kbd style={{
            fontSize: 9, color: 'var(--text-muted)', padding: '2px 6px',
            borderRadius: 5, border: '1px solid var(--border)', background: 'var(--bg-base)',
            fontFamily: 'var(--font-mono)', flexShrink: 0,
          }}>ESC</kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: 368, overflowY: 'auto' }} ref={listRef}>
          {filtered.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              No results for "{query}"
            </div>
          ) : (
            <>
              <div style={{ padding: '10px 16px 4px', fontSize: 9, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                {query ? 'Matching pages' : 'All pages'}
              </div>
              {filtered.map((cmd, i) => {
                const Icon = cmd.icon;
                const active = i === selected;
                return (
                  <div
                    key={cmd.id}
                    onClick={() => goTo(cmd)}
                    onMouseEnter={() => setSelected(i)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      padding: '9px 16px', cursor: 'pointer',
                      background: active ? 'rgba(249,115,22,0.06)' : 'transparent',
                      borderLeft: `2px solid ${active ? 'var(--saffron)' : 'transparent'}`,
                      transition: 'background 0.07s',
                    }}
                  >
                    <div style={{
                      width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                      background: active ? 'rgba(249,115,22,0.14)' : 'var(--bg-base)',
                      border: `1px solid ${active ? 'rgba(249,115,22,0.3)' : 'var(--border)'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'all 0.07s',
                    }}>
                      <Icon size={14} color={active ? 'var(--saffron)' : 'var(--text-muted)'} />
                    </div>

                    <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      <Highlight text={cmd.label} query={query} />
                    </span>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                      <kbd style={{
                        fontSize: 9, color: active ? 'var(--saffron)' : 'var(--text-dim)',
                        padding: '1px 5px', borderRadius: 4,
                        border: `1px solid ${active ? 'rgba(249,115,22,0.3)' : 'var(--border)'}`,
                        background: 'var(--bg-base)', fontFamily: 'var(--font-mono)',
                      }}>
                        {cmd.hint}
                      </kbd>
                      {active && <ArrowRight size={13} color="var(--saffron)" />}
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '8px 16px', borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 14,
          fontSize: 10, color: 'var(--text-muted)',
          background: 'var(--bg-base)',
        }}>
          {[['↑↓', 'navigate'], ['↵', 'open'], ['esc', 'close']].map(([key, label]) => (
            <span key={key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <kbd style={{ fontFamily: 'var(--font-mono)', fontSize: 9, padding: '1px 4px', borderRadius: 4, border: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
                {key}
              </kbd>
              {label}
            </span>
          ))}
          <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 3, opacity: 0.6 }}>
            <Command size={9} /> K  ·  G + letter
          </span>
        </div>
      </div>
    </div>
  );
}
