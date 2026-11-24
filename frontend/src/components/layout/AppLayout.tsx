import React, { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { useAuth } from '../../context/AuthContext';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

interface AppLayoutProps {
  children: ReactNode;
  banner?: {
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
  };
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children, banner }) => {
  const { backendStatus } = useAuth();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      <Navbar />

      {/* Backend offline warning banner if unreachable */}
      {backendStatus === 'offline' && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            padding: '10px 24px',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <AlertCircle size={16} />
          <span>
            FastAPI backend is unreachable at <strong>http://127.0.0.1:8000</strong>. Please start the backend server with{' '}
            <code className="mono">uvicorn app.api.app:app --port 8000</code>.
          </span>
        </div>
      )}

      {/* Optional page banner */}
      {banner && (
        <div
          style={{
            background:
              banner.type === 'success'
                ? 'rgba(16, 185, 129, 0.15)'
                : banner.type === 'error'
                ? 'rgba(244, 63, 94, 0.15)'
                : 'rgba(56, 189, 248, 0.15)',
            borderBottom: `1px solid ${
              banner.type === 'success'
                ? 'rgba(16, 185, 129, 0.3)'
                : banner.type === 'error'
                ? 'rgba(244, 63, 94, 0.3)'
                : 'rgba(56, 189, 248, 0.3)'
            }`,
            color:
              banner.type === 'success'
                ? 'var(--accent-emerald)'
                : banner.type === 'error'
                ? 'var(--accent-rose)'
                : 'var(--accent-cyan)',
            padding: '10px 24px',
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          {banner.type === 'success' && <CheckCircle size={16} />}
          {banner.type === 'error' && <AlertCircle size={16} />}
          {banner.type === 'info' && <Info size={16} />}
          <span>{banner.message}</span>
        </div>
      )}

      {/* Main page container */}
      <main style={{ flex: 1, padding: '28px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {children}
      </main>

      {/* Minimal footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '20px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '12px',
          color: 'var(--text-dim)',
        }}
      >
        <div>
          WearWise &copy; 2026 &bull; Architecture: Modular Monolith &bull; NAVER Anny v0.6.2 &bull; Honest Fit Rev 1.2.1
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>MVP Release Baseline</span>
          <span>FastAPI 0.115+</span>
          <span>Three.js / React 19</span>
        </div>
      </footer>
    </div>
  );
};
