import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import QuickMoodWidget from './QuickMoodWidget';
import CommandPalette from './CommandPalette';
import ShortcutsOverlay from './ShortcutsOverlay';
import { Menu } from 'lucide-react';

const GO_MAP = {
  c: '/command-centre',
  b: '/candidate-brief',
  i: '/constituency-intelligence',
  g: '/ground-pulse',
  o: '/opposition-intelligence',
  n: '/news-intelligence',
  m: '/booth-management',
  d: '/booth-intelligence',
  r: '/field-reports',
  a: '/admin',
  x: '/constituency-demographics',
  s: '/data-sources',
  v: '/voter-roll-upload',
};

export default function Layout({ children }) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Close mobile sidebar on route change
  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  useEffect(() => {
    let gPressed = false;
    let gTimer = null;

    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setPaletteOpen(prev => !prev);
        return;
      }

      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      if (e.key === '?') {
        setShortcutsOpen(prev => !prev);
        return;
      }

      if (e.key === 'Escape') {
        setShortcutsOpen(false);
        setPaletteOpen(false);
        return;
      }

      if (e.key === 'g' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        gPressed = true;
        clearTimeout(gTimer);
        gTimer = setTimeout(() => { gPressed = false; }, 1000);
        return;
      }

      if (gPressed) {
        gPressed = false;
        clearTimeout(gTimer);
        if (GO_MAP[e.key]) navigate(GO_MAP[e.key]);
      }
    };

    window.addEventListener('keydown', handler);
    return () => {
      window.removeEventListener('keydown', handler);
      clearTimeout(gTimer);
    };
  }, [navigate]);

  return (
    <>
      <div className="app-shell">
        {/* Mobile overlay backdrop */}
        {sidebarOpen && (
          <div
            className="sidebar-overlay"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <Sidebar
          onOpenPalette={() => setPaletteOpen(true)}
          mobileOpen={sidebarOpen}
          onMobileClose={() => setSidebarOpen(false)}
        />

        <div className="main-wrapper">
          {/* Mobile top bar */}
          <div className="mobile-topbar">
            <button
              className="mobile-menu-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>
            <span className="mobile-logo">NETA.AI</span>
          </div>

          <main className="main-content">{children}</main>
        </div>

        <QuickMoodWidget />
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      {shortcutsOpen && <ShortcutsOverlay onClose={() => setShortcutsOpen(false)} />}
    </>
  );
}
