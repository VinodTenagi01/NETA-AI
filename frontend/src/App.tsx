import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './store/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';

const CommandCentre          = lazy(() => import('./pages/CommandCentre'));
const ConstituencyIntelligence = lazy(() => import('./pages/ConstituencyIntelligence'));
const GroundPulse            = lazy(() => import('./pages/GroundPulse'));
const BoothManagement        = lazy(() => import('./pages/BoothManagement'));
const OppositionIntelligence = lazy(() => import('./pages/OppositionIntelligence'));
const CandidateBrief         = lazy(() => import('./pages/CandidateBrief'));
const NewsIntelligence       = lazy(() => import('./pages/NewsIntelligence'));
const FieldReports           = lazy(() => import('./pages/FieldReports'));
const AdminDashboard         = lazy(() => import('./pages/AdminDashboard'));
const BoothIntelligence      = lazy(() => import('./pages/BoothIntelligence'));
const ConstituencyDemographics = lazy(() => import('./pages/ConstituencyDemographics'));
const DataSources            = lazy(() => import('./pages/DataSources'));
const VoterRollUpload        = lazy(() => import('./pages/VoterRollUpload'));

function NotFound() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: 12, color: 'var(--text-muted)',
    }}>
      <div style={{ fontSize: 48, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--border-bright)' }}>404</div>
      <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)' }}>Page not found</div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>The route you requested doesn't exist in NETA.AI.</div>
      <a href="/command-centre" style={{
        marginTop: 8, fontSize: 12, color: 'var(--saffron)', textDecoration: 'none',
        padding: '7px 16px', borderRadius: 7, border: '1px solid var(--saffron)',
        fontWeight: 700,
      }}>
        ← Back to Command Centre
      </a>
    </div>
  );
}

function PageLoader() {
  return (
    <div style={{
      flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexDirection: 'column', gap: 10, color: 'var(--text-muted)',
    }}>
      <div style={{
        width: 28, height: 28, border: '2px solid var(--border)',
        borderTop: '2px solid var(--saffron)', borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <div style={{ fontSize: 11, letterSpacing: 1 }}>LOADING</div>
    </div>
  );
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg-base)', flexDirection: 'column', gap: 12,
      }}>
        <div style={{ fontSize: 22, fontWeight: 900, color: 'var(--saffron)' }}>NETA.AI</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Initializing…</div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <Layout>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/"                              element={<Navigate to="/command-centre" replace />} />
                  <Route path="/command-centre"               element={<CommandCentre />} />
                  <Route path="/constituency-intelligence"    element={<ConstituencyIntelligence />} />
                  <Route path="/ground-pulse"                 element={<GroundPulse />} />
                  <Route path="/booth-management"             element={<BoothManagement />} />
                  <Route path="/opposition-intelligence"      element={<OppositionIntelligence />} />
                  <Route path="/candidate-brief"              element={<CandidateBrief />} />
                  <Route path="/news-intelligence"            element={<NewsIntelligence />} />
                  <Route path="/field-reports"                element={<FieldReports />} />
                  <Route path="/admin"                        element={<AdminDashboard />} />
                  <Route path="/booth-intelligence"           element={<BoothIntelligence />} />
                  <Route path="/constituency-demographics"    element={<ConstituencyDemographics />} />
                  <Route path="/data-sources"                 element={<DataSources />} />
                  <Route path="/voter-roll-upload"            element={<VoterRollUpload />} />
                  <Route path="*"                             element={<NotFound />} />
                </Routes>
              </Suspense>
            </Layout>
          </RequireAuth>
        }
      />
    </Routes>
  );
}
