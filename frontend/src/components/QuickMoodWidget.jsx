import { useState } from 'react';
import { SmilePlus, X, Send } from 'lucide-react';
import { submitMood } from '../api/vayu';
import { useToast } from '../store/ToastContext';

const CID = '10000000-0000-0000-0000-000000000001';

const MOOD_LABELS = ['', 'Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive'];
const MOOD_EMOJIS = ['', '😡', '😟', '😐', '😊', '😄'];

function moodColor(v) {
  if (v >= 4.5) return 'var(--green)';
  if (v >= 3.5) return 'var(--green)';
  if (v >= 2.5) return 'var(--yellow)';
  if (v >= 1.5) return 'var(--red)';
  return 'var(--red)';
}

export default function QuickMoodWidget() {
  const [open, setOpen] = useState(false);
  const [mood, setMood] = useState(3);
  const [zone, setZone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { addToast } = useToast();

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await submitMood({
        constituency_id: CID,
        mood_score: Number(mood),
        ...(zone ? { zone } : {}),
      });
      addToast(`Mood ${Number(mood).toFixed(1)}/5 submitted${zone ? ` for ${zone} Zone` : ''}.`, 'success');
      setOpen(false);
      setMood(3);
      setZone('');
    } catch (e) {
      const detail = e.response?.data?.detail;
      addToast(detail || 'Mood submission failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const moodVal = Math.round(mood);

  return (
    <div style={{ position: 'fixed', bottom: 28, right: 28, zIndex: 300 }}>
      {/* Expanded panel */}
      {open && (
        <div style={{
          position: 'absolute', bottom: 60, right: 0, width: 240,
          background: 'var(--bg-surface)', border: '1px solid var(--border)',
          borderRadius: 14, boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
          animation: 'toast-in 0.2s ease',
        }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>Quick Mood Check-in</span>
            <button onClick={() => setOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
              <X size={13} />
            </button>
          </div>

          <div style={{ padding: '14px' }}>
            {/* Mood display */}
            <div style={{ textAlign: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 28, lineHeight: 1 }}>{MOOD_EMOJIS[moodVal]}</div>
              <div style={{ fontSize: 22, fontWeight: 900, fontFamily: 'var(--font-mono)', color: moodColor(mood), lineHeight: 1.2 }}>
                {Number(mood).toFixed(1)}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {MOOD_LABELS[moodVal]}
              </div>
            </div>

            {/* Slider */}
            <input
              type="range" min={1} max={5} step={0.5}
              value={mood}
              onChange={e => setMood(e.target.value)}
              style={{ width: '100%', accentColor: moodColor(mood), marginBottom: 12 }}
            />

            {/* Zone */}
            <select
              className="select-input"
              style={{ width: '100%', marginBottom: 12, fontSize: 12 }}
              value={zone}
              onChange={e => setZone(e.target.value)}
            >
              <option value="">All zones (no filter)</option>
              {['Central', 'North', 'South', 'East', 'West'].map(z => (
                <option key={z} value={z}>{z} Zone</option>
              ))}
            </select>

            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', gap: 6 }}
              onClick={handleSubmit}
              disabled={submitting}
            >
              <Send size={12} />
              {submitting ? 'Submitting…' : 'Submit Mood'}
            </button>

            <div style={{ fontSize: 9, color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
              VAYU · Rate 20× per hour max
            </div>
          </div>
        </div>
      )}

      {/* Float button */}
      <button
        onClick={() => setOpen(v => !v)}
        title="Quick Mood Check-in"
        style={{
          width: 46, height: 46, borderRadius: '50%', border: 'none', cursor: 'pointer',
          background: open ? 'var(--bg-elevated)' : 'var(--saffron)',
          color: open ? 'var(--text-secondary)' : '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 16px rgba(249,115,22,0.5)',
          transition: 'all 0.2s',
        }}
      >
        {open ? <X size={18} /> : <SmilePlus size={20} />}
      </button>
    </div>
  );
}
