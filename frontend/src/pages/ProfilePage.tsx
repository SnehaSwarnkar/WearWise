import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Header from './Header';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export default function ProfilePage() {
  const { user, updateProfile, logout } = useAuth();
  const themeCtx = useTheme() as any;
  const navigate = useNavigate();

  const [preferredSection, setPreferredSection] = useState(user?.gender || 'women');
  const [savedNotice, setSavedNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSavePrefs = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedNotice(null);
    try {
      await updateProfile({ gender: preferredSection });
      setSavedNotice('Your shopping preferences have been saved.');
    } catch (err: any) {
      setSavedNotice(err.message || 'Could not update settings right now.');
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/auth');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
      <Header />

      <div style={{ maxWidth: '920px', margin: '0 auto', padding: '32px 24px 64px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
        <div>
          <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '0.08em', color: '#ff3d9a' }}>
            ✦ ACCOUNT &amp; PREFERENCES
          </span>
          <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: '34px', margin: '4px 0 0' }}>
            CUSTOMER PROFILE
          </h1>
        </div>

        <section
          data-testid="customer-profile-card"
          style={{ background: '#ffffff', border: '2.5px solid #151515', boxShadow: '6px 6px 0 #151515', padding: '24px' }}
        >
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 12px' }}>Account Details</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', fontSize: '14px' }}>
            <div><strong>Name:</strong> {user?.name || 'Customer'}</div>
            <div><strong>Email:</strong> {user?.email}</div>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '18px' }}>
            <Link to="/avatar" className="main-btn" style={{ textDecoration: 'none' }}>
              Manage My Avatar →
            </Link>
            <Link to="/orders" className="outline-btn" style={{ textDecoration: 'none' }}>
              View My Orders
            </Link>
            <Link to="/wishlist" className="outline-btn" style={{ textDecoration: 'none' }}>
              My Wishlist
            </Link>
          </div>
        </section>

        <section style={{ background: '#ffffff', border: '2.5px solid #151515', padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 12px' }}>Shopping Preferences</h2>
          <form onSubmit={handleSavePrefs} style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '420px' }}>
            <label className="auth-field">
              <span>PREFERRED DEPARTMENT</span>
              <select
                value={preferredSection}
                onChange={(e) => setPreferredSection(e.target.value)}
                style={{ padding: '10px', border: '2px solid #151515', background: '#ffffff' }}
              >
                <option value="women">Women</option>
                <option value="men">Men</option>
                <option value="kids">Kids</option>
              </select>
            </label>

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button type="submit" disabled={saving} className="main-btn">
                {saving ? 'Saving…' : 'Save Preferences'}
              </button>
              <button
                type="button"
                onClick={() => themeCtx?.toggle?.()}
                className="outline-btn"
              >
                Theme: {themeCtx?.theme === 'negative' ? 'Dark Mode' : 'Light Mode'}
              </button>
            </div>
            {savedNotice && <p style={{ margin: 0, fontWeight: 700, fontSize: '13px', color: '#15803d' }}>{savedNotice}</p>}
          </form>
        </section>

        <div>
          <button
            type="button"
            onClick={handleSignOut}
            style={{
              border: '2px solid #151515',
              background: '#151515',
              color: '#ffffff',
              padding: '10px 20px',
              fontWeight: 900,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
