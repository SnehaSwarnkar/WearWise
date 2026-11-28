import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../Header';
import { apiClient } from '../../api/client';
import { getWishlist } from '../../api/saved';
import { fetchProducts } from '../../api/products';
import { getMyOrders } from '../../api/orders';
import { BodyProfile } from '../../types/api';
import { ConsumerAvatarViewport } from '../../components/avatar/ConsumerAvatarViewport';

export default function AvatarDashboardPage() {
  const [profile, setProfile] = useState<BodyProfile | null>(null);
  const [wishlist, setWishlist] = useState<any[]>([]);
  const [tryOnCatalog, setTryOnCatalog] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    Promise.all([
      apiClient.listProfiles().catch(() => []),
      getWishlist().catch(() => []),
      fetchProducts(null, false, {}).catch(() => []),
      getMyOrders().catch(() => []),
    ]).then(([profiles, wish, prods, ords]) => {
      if (!alive) return;
      setProfile(Array.isArray(profiles) && profiles.length > 0 ? profiles[0] : null);
      setWishlist(Array.isArray(wish) ? wish : []);
      const ready = (Array.isArray(prods) ? prods : []).filter(
        (p) => p.sku && p.tryOnCapabilities?.threeDTryOnEnabled
      );
      setTryOnCatalog(ready.slice(0, 6));
      setOrders(Array.isArray(ords) ? ords : []);
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, []);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
        <Header />
        <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '48px 24px', textAlign: 'center', fontWeight: 700, fontSize: '15px', color: '#454854' }}>
          Loading your avatar studio…
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
        <Header />
        <div style={{ maxWidth: '720px', margin: '48px auto', padding: '32px', background: '#ffffff', border: '3px solid #151515', boxShadow: '8px 8px 0 #d8ff3f' }}>
          <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: '30px', margin: '0 0 10px' }}>NO SAVED AVATAR YET</h1>
          <p style={{ fontSize: '15px', color: '#454854', margin: '0 0 20px' }}>
            You can create your body profile to see how clothing sizes and fit may suit your body.
          </p>
          <Link to="/avatar/create" className="main-btn" style={{ textDecoration: 'none' }}>
            Create My Avatar →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
      <Header />

      <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '30px 24px 64px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '24px' }}>
          <div>
            <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '0.08em', color: '#ff3d9a' }}>
              ✦ AVATAR STUDIO &amp; VIRTUAL WARDROBE
            </span>
            <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: 'clamp(28px, 4vw, 42px)', margin: '4px 0 0' }}>
              {profile?.avatar_name || 'MY AVATAR STUDIO'}
            </h1>
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <Link
              to="/avatar/create?edit=1"
              style={{ border: '2px solid #151515', background: '#d8ff3f', color: '#151515', padding: '10px 16px', fontWeight: 900, fontSize: '13px', textDecoration: 'none' }}
            >
              Edit Body &amp; Proportions
            </Link>
            <Link
              to="/try-on"
              className="main-btn"
              style={{ textDecoration: 'none' }}
            >
              Open Virtual Try-On →
            </Link>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '28px', alignItems: 'start' }}>
          <ConsumerAvatarViewport assetUrl={profile?.latest_asset_url} height={500} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Personal Summary */}
            <section style={{ background: '#ffffff', border: '2.5px solid #151515', padding: '20px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 900, margin: '0 0 12px' }}>Your Fit Summary</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', fontSize: '13px' }}>
                <div><strong>Shape Preset:</strong> {profile?.body_shape || 'Balanced'}</div>
                <div><strong>Height:</strong> {profile ? `${Math.round(profile.stature_cm)} cm` : '—'}</div>
                <div>
                  <strong>Chest:</strong>{' '}
                  {profile?.active_measurements?.chest_circumference
                    ? `${Math.round(profile.active_measurements.chest_circumference.value_cm)} cm`
                    : '—'}
                </div>
                <div>
                  <strong>Waist:</strong>{' '}
                  {profile?.active_measurements?.waist_planar_circumference
                    ? `${Math.round(profile.active_measurements.waist_planar_circumference.value_cm)} cm`
                    : '—'}
                </div>
                <div>
                  <strong>Hips:</strong>{' '}
                  {profile?.active_measurements?.hip_circumference
                    ? `${Math.round(profile.active_measurements.hip_circumference.value_cm)} cm`
                    : '—'}
                </div>
                <div>
                  <strong>Shoulders:</strong>{' '}
                  {profile?.active_measurements?.shoulder_biacromial_breadth
                    ? `${Math.round(profile.active_measurements.shoulder_biacromial_breadth.value_cm)} cm`
                    : '—'}
                </div>
              </div>
            </section>

            {/* 3D Try-On Ready Clothing */}
            <section style={{ background: '#ffffff', border: '2.5px solid #151515', padding: '20px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 900, margin: '0 0 10px' }}>Try On in 3D</h2>
              {tryOnCatalog.length === 0 ? (
                <p style={{ fontSize: '13px', color: '#454854', margin: 0 }}>
                  Visit our shop to find garments ready for your virtual fitting room.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {tryOnCatalog.map((item) => (
                    <div
                      key={item.sku}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 12px',
                        border: '1.5px solid #151515',
                        background: '#fff8f1',
                      }}
                    >
                      <div>
                        <strong style={{ fontSize: '14px' }}>{item.name}</strong>
                        <div style={{ fontSize: '12px', color: '#454854' }}>
                          {item.seller_name || item.brand} · ₹{Number(item.price || 0).toLocaleString()}
                        </div>
                      </div>
                      <Link
                        to={`/try-on?sku=${encodeURIComponent(item.sku)}`}
                        style={{
                          padding: '7px 12px',
                          background: '#151515',
                          color: '#d8ff3f',
                          fontWeight: 900,
                          fontSize: '12px',
                          textDecoration: 'none',
                        }}
                      >
                        Try On →
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Wishlist & Orders shortcuts */}
            <section style={{ background: '#ffffff', border: '2.5px solid #151515', padding: '20px' }}>
              <h2 style={{ fontSize: '16px', fontWeight: 900, margin: '0 0 8px' }}>Your Wardrobe &amp; Saved Picks</h2>
              <p style={{ fontSize: '13px', color: '#454854', margin: '0 0 12px' }}>
                You have {wishlist.length} saved wishlist item{wishlist.length === 1 ? '' : 's'} and {orders.length} past order{orders.length === 1 ? '' : 's'}.
              </p>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <Link to="/wishlist" style={{ border: '2px solid #151515', padding: '8px 14px', fontWeight: 800, fontSize: '12px', textDecoration: 'none', color: '#151515' }}>
                  View Wishlist →
                </Link>
                <Link to="/orders" style={{ border: '2px solid #151515', padding: '8px 14px', fontWeight: 800, fontSize: '12px', textDecoration: 'none', color: '#151515' }}>
                  View Orders →
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
