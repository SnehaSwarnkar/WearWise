import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  User,
  ShoppingBag,
  Box,
  Sliders,
  Sparkles,
  Server,
  Layers,
  ChevronDown,
  Key,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const {
    role,
    currentPrincipalId,
    token,
    switchRole,
    setCustomToken,
    activeProfile,
    allProfiles,
    setActiveProfile,
    backendStatus,
    checkBackendHealth,
    refreshProfiles,
  } = useAuth();

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [customUuidInput, setCustomUuidInput] = useState('');
  const [customJwtInput, setCustomJwtInput] = useState(token || '');
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const navigate = useNavigate();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: Layers },
    { label: 'Body Profile', path: '/profile', icon: User },
    { label: '3D Avatar Studio', path: '/avatar', icon: Box },
    { label: 'Garment Studio', path: '/garments', icon: ShoppingBag },
    { label: 'Honest Fit', path: '/fit', icon: Sparkles },
  ];

  return (
    <>
      <header
        style={{
          height: '70px',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
          position: 'sticky',
          top: 0,
          zIndex: 50,
        }}
      >
        {/* Brand identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <div
            onClick={() => navigate('/')}
            style={{
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              lineHeight: 1.1,
            }}
          >
            <span
              style={{
                fontSize: '18px',
                fontWeight: 800,
                letterSpacing: '0.18em',
                color: '#ffffff',
                textTransform: 'uppercase',
              }}
            >
              WearWise
            </span>
            <span
              style={{
                fontSize: '10px',
                letterSpacing: '0.1em',
                color: 'var(--accent-cyan)',
                fontWeight: 500,
                textTransform: 'uppercase',
              }}
            >
              Avatar Engine &bull; Honest Fit
            </span>
          </div>

          {/* Navigation links */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  style={({ isActive }) => ({
                    display: 'flex',
                    alignItems: 'center',
                    gap: '7px',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    fontWeight: isActive ? 600 : 500,
                    color: isActive ? '#ffffff' : 'var(--text-muted)',
                    background: isActive ? 'var(--bg-surface-raised)' : 'transparent',
                    border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                    transition: 'all 0.15s ease',
                  })}
                >
                  <Icon size={15} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Right side controls: Profile Chip + Role Switcher + Backend Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Active Profile Pill (for shopper mode) */}
          {role === 'user' && (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 12px',
                  background: 'var(--bg-surface-raised)',
                  border: '1px solid var(--border-medium)',
                  borderRadius: '20px',
                  fontSize: '12px',
                  color: 'var(--text-main)',
                }}
              >
                <div
                  style={{
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    background: activeProfile ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                  }}
                />
                <span style={{ fontWeight: 600 }}>
                  {activeProfile
                    ? `${activeProfile.presentation_gender} • ${activeProfile.stature_cm}cm`
                    : 'No Profile Selected'}
                </span>
                <ChevronDown size={14} color="var(--text-muted)" />
              </button>

              {/* Profile selector dropdown */}
              {profileDropdownOpen && (
                <div
                  style={{
                    position: 'absolute',
                    top: '38px',
                    right: 0,
                    width: '260px',
                    background: 'var(--bg-surface-raised)',
                    border: '1px solid var(--border-highlight)',
                    borderRadius: '8px',
                    padding: '8px',
                    boxShadow: 'var(--shadow-lg)',
                    zIndex: 60,
                  }}
                >
                  <div
                    style={{
                      fontSize: '11px',
                      color: 'var(--text-dim)',
                      fontWeight: 600,
                      padding: '4px 8px 8px',
                      textTransform: 'uppercase',
                      borderBottom: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span>User Profiles ({allProfiles.length})</span>
                    <button
                      onClick={() => refreshProfiles()}
                      style={{ color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <RefreshCw size={11} /> Refresh
                    </button>
                  </div>

                  <div style={{ maxHeight: '180px', overflowY: 'auto', margin: '6px 0' }}>
                    {allProfiles.map((p) => (
                      <div
                        key={p.profile_id}
                        onClick={() => {
                          setActiveProfile(p);
                          setProfileDropdownOpen(false);
                        }}
                        style={{
                          padding: '8px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          cursor: 'pointer',
                          background: activeProfile?.profile_id === p.profile_id ? 'var(--bg-surface-hover)' : 'transparent',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '2px',
                        }}
                      >
                        <span style={{ fontWeight: 600, color: '#ffffff' }}>
                          {p.presentation_gender.toUpperCase()} • {p.stature_cm} cm (Rev {p.current_revision})
                        </span>
                        <span style={{ fontSize: '10px', color: 'var(--text-dim)' }} className="mono">
                          ID: {p.profile_id.substring(0, 8)}...
                        </span>
                      </div>
                    ))}

                    {allProfiles.length === 0 && (
                      <div style={{ padding: '12px 8px', fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center' }}>
                        No profiles created yet.
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      navigate('/profile');
                    }}
                    className="btn-primary"
                    style={{ width: '100%', fontSize: '12px', padding: '6px 0' }}
                  >
                    + Create New Profile
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Role Pill */}
          <button
            onClick={() => setShowAuthModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: 600,
              background: role === 'user' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(168, 85, 247, 0.12)',
              border: `1px solid ${role === 'user' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(168, 85, 247, 0.3)'}`,
              color: role === 'user' ? 'var(--accent-cyan)' : '#c084fc',
            }}
          >
            <ShieldCheck size={14} />
            <span>{role === 'user' ? 'Shopper Mode' : 'Merchant Brand'}</span>
          </button>

          {/* Backend Health Indicator */}
          <div
            onClick={() => checkBackendHealth()}
            title="FastAPI Backend Health"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '11px',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <Server size={12} />
            <div
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background:
                  backendStatus === 'online'
                    ? 'var(--accent-emerald)'
                    : backendStatus === 'checking'
                    ? 'var(--accent-amber)'
                    : 'var(--accent-rose)',
              }}
            />
            <span className="mono">{backendStatus === 'online' ? '8000' : backendStatus}</span>
          </div>
        </div>
      </header>

      {/* Dev Auth / Identity Modal */}
      {showAuthModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setShowAuthModal(false)}
        >
          <div
            className="card-raised"
            style={{ width: '480px', maxWidth: '90vw' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Key size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Development Identity & Authentication</h3>
              </div>
              <button
                onClick={() => setShowAuthModal(false)}
                style={{ color: 'var(--text-dim)', fontSize: '18px' }}
              >
                &times;
              </button>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '18px', lineHeight: 1.5 }}>
              WearWise isolates User Shopper identities from Merchant Brand principals. Select a role below to simulate
              multi-tenant API requests via the replaceable authentication adapter.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
              <button
                onClick={() => switchRole('user')}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: `2px solid ${role === 'user' ? 'var(--accent-cyan)' : 'var(--border-medium)'}`,
                  background: role === 'user' ? 'rgba(56, 189, 248, 0.08)' : 'var(--bg-surface)',
                  color: '#ffffff',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>Shopper User</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Generates avatars, manages measurements, evaluates fit.
                </div>
              </button>

              <button
                onClick={() => switchRole('brand')}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: `2px solid ${role === 'brand' ? '#a855f7' : 'var(--border-medium)'}`,
                  background: role === 'brand' ? 'rgba(168, 85, 247, 0.08)' : 'var(--bg-surface)',
                  color: '#ffffff',
                  textAlign: 'left',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>Merchant Brand</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Registers garments, fabric specs, and size dimensions.
                </div>
              </button>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>
                Active Principal UUID ({role})
              </label>
              <input
                type="text"
                className="input-field mono"
                style={{ fontSize: '12px' }}
                value={customUuidInput || currentPrincipalId}
                onChange={(e) => setCustomUuidInput(e.target.value)}
                placeholder="00000000-0000-0000-0000-000000000000"
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px', color: 'var(--text-muted)' }}>
                Optional Production JWT Bearer Token
              </label>
              <textarea
                className="input-field mono"
                rows={2}
                style={{ fontSize: '11px', resize: 'vertical' }}
                value={customJwtInput}
                onChange={(e) => setCustomJwtInput(e.target.value)}
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="btn-secondary"
                onClick={() => {
                  setCustomToken(null);
                  setCustomJwtInput('');
                  setShowAuthModal(false);
                }}
              >
                Reset to Dev Defaults
              </button>
              <button
                className="btn-primary"
                onClick={() => {
                  if (customUuidInput) {
                    switchRole(role, customUuidInput);
                  }
                  if (customJwtInput) {
                    setCustomToken(customJwtInput.trim());
                  }
                  setShowAuthModal(false);
                }}
              >
                Save Identity
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
