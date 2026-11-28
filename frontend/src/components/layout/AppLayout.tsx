import React, { ReactNode } from 'react';
import Header from '../../pages/Header';
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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary, var(--bg, #fff8f1))' }}>
      {/* Unified WearWise Application Shell Header */}
      <Header />

      {/* Backend offline warning banner if unreachable */}
      {backendStatus === 'offline' && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#b91c1c',
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
            Body Engine backend is unreachable at <strong>http://127.0.0.1:8000</strong>. Start it with{' '}
            <code style={{ fontFamily: 'var(--font-mono)', padding: '2px 6px', background: 'rgba(0,0,0,0.06)', borderRadius: '4px' }}>
              python -m uvicorn app.api.app:app --port 8000
            </code>.
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

      {/* Shared WearWise editorial footer */}
      <footer
        style={{
          borderTop: '2px solid var(--border)',
          background: 'var(--bg-invert, #151515)',
          color: 'var(--text-invert, #ffffff)',
          padding: '24px 28px',
          fontSize: '13px',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <span style={{ fontFamily: 'var(--font-sans)', fontWeight: 800, letterSpacing: '0.12em' }}>WEARWISE</span> &bull; AI Fashion Assistant & Honest Fit Platform
          </div>
          <div style={{ fontSize: '12px', opacity: 0.85 }}>
            NAVER Anny v0.6.2 &bull; Honest Fit Rev 1.2.1 &bull; Core Engine (Port 8000) & Store (Port 8001)
          </div>
        </div>
      </footer>
    </div>
  );
};
