import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../Header';
import { apiClient } from '../../api/client';
import { getMyOrders } from '../../api/orders';
import { BodyProfile } from '../../types/api';
import { ConsumerAvatarViewport } from '../../components/avatar/ConsumerAvatarViewport';

function formatInches(cm: number): string {
  const totalIn = Math.round(cm / 2.54);
  const ft = Math.floor(totalIn / 12);
  const rem = totalIn % 12;
  return `${ft}'${rem}"`;
}

function formatGenderLabel(g?: string): string {
  if (g === 'masculine') return 'Masculine Build';
  if (g === 'feminine') return 'Feminine Build';
  return 'Neutral Build';
}

export default function AvatarLandingPage() {
  const [profile, setProfile] = useState<BodyProfile | null>(null);
  const [hasOrders, setHasOrders] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([
      apiClient.listProfiles().catch(() => []),
      getMyOrders().catch(() => []),
    ]).then(([profiles, orders]) => {
      if (!alive) return;
      const list = Array.isArray(profiles) ? profiles : [];
      setProfile(list[0] || null);
      setHasOrders(Array.isArray(orders) && orders.length > 0);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  const chest = profile?.active_measurements?.chest_circumference?.value_cm;
  const waist = profile?.active_measurements?.waist_planar_circumference?.value_cm;
  const hips = profile?.active_measurements?.hip_circumference?.value_cm;

  return (
    <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
      <Header />

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px 64px' }}>
        {loading ? (
          <div style={{ padding: '40px', background: '#ffffff', border: '2.5px solid #151515' }}>
            Loading your personal avatar profile…
          </div>
        ) : !profile ? (
          /* Onboarding state when customer has no saved avatar yet */
          <section
            data-testid="avatar-onboarding"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '28px',
              alignItems: 'center',
            }}
          >
            <div
              style={{
                background: '#ffffff',
                border: '3px solid #151515',
                boxShadow: '10px 10px 0 #d8ff3f',
                padding: '34px 30px',
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  background: '#d8ff3f',
                  border: '1.5px solid #151515',
                  padding: '4px 10px',
                  fontSize: '11px',
                  fontWeight: 900,
                  letterSpacing: '0.06em',
                  marginBottom: '14px',
                }}
              >
                YOUR PERSONAL FIT GUIDE
              </span>
              <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: 'clamp(30px, 4vw, 44px)', lineHeight: 0.98, margin: '0 0 14px' }}>
                CREATE YOUR PERSONAL AVATAR
              </h1>
              <p style={{ fontSize: '16px', lineHeight: 1.6, color: '#3b3e49', margin: '0 0 18px' }}>
                You can create your body profile to see how clothing sizes and fit may suit your body.
              </p>

              <ul style={{ margin: '0 0 24px', paddingLeft: '18px', fontSize: '14px', lineHeight: 1.8, color: '#2b2d36' }}>
                <li>Start with your height and an everyday body shape preset</li>
                <li>Fine-tune shoulders, chest, waist, and hips with simple sliders</li>
                <li>Try tops and shirts virtually on your saved avatar before ordering</li>
              </ul>

              <Link
                to="/avatar/create"
                data-testid="create-my-avatar-btn"
                className="main-btn"
                style={{ display: 'inline-block', textDecoration: 'none' }}
              >
                Create My Avatar →
              </Link>
            </div>

            <ConsumerAvatarViewport
              height={460}
              emptyTitle="Your 3D Avatar Preview"
              emptySubtitle="Once you enter a few simple proportions, your personal avatar appears here for virtual try-on."
            />
          </section>
        ) : (
          /* Personal Fashion / Body Profile Summary */
          <section
            data-testid="avatar-saved-summary"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '28px',
              alignItems: 'start',
            }}
          >
            <ConsumerAvatarViewport assetUrl={profile.latest_asset_url} height={500} autoRotate />

            <div
              style={{
                background: '#ffffff',
                border: '3px solid #151515',
                boxShadow: '10px 10px 0 #151515',
                padding: '28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '18px',
              }}
            >
              <div>
                <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '0.08em', color: '#ff3d9a' }}>
                  ✦ SAVED BODY PROFILE
                </span>
                <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: '30px', margin: '4px 0 4px' }}>
                  {profile.avatar_name || 'My Personal Avatar'}
                </h1>
                <div style={{ fontSize: '13px', color: '#454854' }}>
                  Last updated {new Date(profile.updated_at).toLocaleDateString()}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                <div style={{ padding: '12px', background: '#fff8f1', border: '1.5px solid #151515' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#6b7280' }}>BASE PROFILE</div>
                  <strong style={{ fontSize: '14px' }}>{formatGenderLabel(profile.presentation_gender)}</strong>
                </div>
                <div style={{ padding: '12px', background: '#fff8f1', border: '1.5px solid #151515' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#6b7280' }}>BODY SHAPE</div>
                  <strong style={{ fontSize: '14px' }}>{profile.body_shape || 'Balanced'}</strong>
                </div>
                <div style={{ padding: '12px', background: '#fff8f1', border: '1.5px solid #151515' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#6b7280' }}>HEIGHT</div>
                  <strong style={{ fontSize: '14px' }}>
                    {Math.round(profile.stature_cm)} cm ({formatInches(profile.stature_cm)})
                  </strong>
                </div>
                <div style={{ padding: '12px', background: '#fff8f1', border: '1.5px solid #151515' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#6b7280' }}>CHEST / WAIST / HIPS</div>
                  <strong style={{ fontSize: '14px' }}>
                    {chest ? `${Math.round(chest)}` : '—'} / {waist ? `${Math.round(waist)}` : '—'} / {hips ? `${Math.round(hips)}` : '—'} cm
                  </strong>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
                <Link
                  to="/avatar/dashboard"
                  data-testid="open-avatar-studio-btn"
                  className="main-btn"
                  style={{ textAlign: 'center', textDecoration: 'none' }}
                >
                  Open Avatar Studio →
                </Link>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
                  <Link
                    to="/avatar/create?edit=1"
                    data-testid="edit-avatar-btn"
                    style={{
                      textAlign: 'center',
                      textDecoration: 'none',
                      padding: '11px 14px',
                      border: '2px solid #151515',
                      background: '#d8ff3f',
                      color: '#151515',
                      fontWeight: 900,
                      fontSize: '13px',
                    }}
                  >
                    Edit Avatar
                  </Link>
                  <Link
                    to="/wishlist"
                    style={{
                      textAlign: 'center',
                      textDecoration: 'none',
                      padding: '11px 14px',
                      border: '2px solid #151515',
                      background: '#ffffff',
                      color: '#151515',
                      fontWeight: 800,
                      fontSize: '13px',
                    }}
                  >
                    Try My Wishlist
                  </Link>
                  {hasOrders && (
                    <Link
                      to="/orders"
                      style={{
                        textAlign: 'center',
                        textDecoration: 'none',
                        padding: '11px 14px',
                        border: '2px solid #151515',
                        background: '#ffffff',
                        color: '#151515',
                        fontWeight: 800,
                        fontSize: '13px',
                      }}
                    >
                      Try Purchased Clothes
                    </Link>
                  )}
                  <Link
                    to="/shop"
                    style={{
                      textAlign: 'center',
                      textDecoration: 'none',
                      padding: '11px 14px',
                      border: '2px solid #151515',
                      background: '#ffffff',
                      color: '#151515',
                      fontWeight: 800,
                      fontSize: '13px',
                    }}
                  >
                    Explore Clothes
                  </Link>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
