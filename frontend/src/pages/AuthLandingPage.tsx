import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css';

/**
 * Role-Separated WearWise Authentication Entry Experience (`/auth`)
 * Clearly separates Customer, Seller, and Admin portals.
 */
export default function AuthLandingPage() {
  return (
    <div className="auth-page auth-portal-landing" style={{ padding: '40px 20px' }}>
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-pink" />

      <div style={{ position: 'relative', zIndex: 1, width: 'min(1100px, 100%)' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '28px',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <Link to="/" className="auth-logo" style={{ marginBottom: 0, color: '#fff8f1', fontSize: '26px' }}>
            Wear<span>Wise</span>
          </Link>
          <Link
            to="/shop"
            style={{
              color: '#fff8f1',
              fontSize: '13px',
              fontWeight: 700,
              textDecoration: 'underline',
              letterSpacing: '0.04em',
            }}
          >
            Browse Storefront →
          </Link>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '22px',
          }}
        >
          {/* CUSTOMER PORTAL */}
          <section
            data-testid="portal-card-shopper"
            style={{
              background: '#fff8f1',
              border: '3px solid #151515',
              boxShadow: '10px 10px 0 #d8ff3f',
              padding: '34px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '20px',
            }}
          >
            <div>
              <div className="auth-eyebrow" style={{ color: '#ff3d9a' }}>
                ✦ CUSTOMER EXPERIENCE
              </div>
              <h1
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 'clamp(28px, 3.5vw, 38px)',
                  lineHeight: 0.96,
                  letterSpacing: '-1.5px',
                  color: '#151515',
                  margin: '0 0 12px',
                }}
              >
                CUSTOMER{' '}
                <span style={{ color: '#ff3d9a', fontFamily: '"Playfair Display", serif', fontStyle: 'italic' }}>
                  LOGIN
                </span>
              </h1>
              <p style={{ fontSize: '15px', color: '#454854', lineHeight: 1.6, margin: 0 }}>
                Discover fashion, find your fit and shop with WearWise.
              </p>
              <ul style={{ margin: '16px 0 0', paddingLeft: '18px', color: '#2b2d36', fontSize: '13px', lineHeight: 1.7 }}>
                <li>Create your personal 3D avatar from simple body details</li>
                <li>Preview how garments fit &amp; check size guidance before ordering</li>
                <li>Save wishlist items, track orders, and manage your bag</li>
              </ul>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link
                to="/login"
                data-testid="enter-shopper-login"
                className="auth-submit"
                style={{ textAlign: 'center', textDecoration: 'none' }}
              >
                SIGN IN AS CUSTOMER ✦
              </Link>
              <Link
                to="/register"
                data-testid="enter-shopper-register"
                style={{
                  textAlign: 'center',
                  textDecoration: 'none',
                  padding: '12px 16px',
                  border: '2px solid #151515',
                  background: '#ffffff',
                  color: '#151515',
                  fontWeight: 800,
                  fontSize: '13px',
                  letterSpacing: '0.05em',
                }}
              >
                CREATE CUSTOMER ACCOUNT →
              </Link>
            </div>
          </section>

          {/* SELLER PORTAL */}
          <section
            data-testid="portal-card-seller"
            style={{
              background: '#fff8f1',
              border: '3px solid #151515',
              boxShadow: '10px 10px 0 #8d6bff',
              padding: '34px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '20px',
            }}
          >
            <div>
              <div className="auth-eyebrow" style={{ color: '#8d6bff' }}>
                ◆ MERCHANT CONSOLE
              </div>
              <h2
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 'clamp(28px, 3.5vw, 38px)',
                  lineHeight: 0.96,
                  letterSpacing: '-1.5px',
                  color: '#151515',
                  margin: '0 0 12px',
                }}
              >
                SELLER{' '}
                <span style={{ color: '#8d6bff', fontFamily: '"Playfair Display", serif', fontStyle: 'italic' }}>
                  LOGIN
                </span>
              </h2>
              <p style={{ fontSize: '15px', color: '#454854', lineHeight: 1.6, margin: 0 }}>
                Manage your products, publish garments and grow your store.
              </p>
              <ul style={{ margin: '16px 0 0', paddingLeft: '18px', color: '#2b2d36', fontSize: '13px', lineHeight: 1.7 }}>
                <li>Create listings, upload product photography, and manage stock</li>
                <li>Configure garment sizing &amp; virtual try-on readiness</li>
                <li>Process customer orders and track shipments</li>
              </ul>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link
                to="/seller/login"
                data-testid="enter-seller-login"
                className="auth-submit"
                style={{
                  textAlign: 'center',
                  textDecoration: 'none',
                  background: '#151515',
                  color: '#d8ff3f',
                  border: '2px solid #151515',
                }}
              >
                SIGN IN TO SELLER PORTAL ◆
              </Link>
              <Link
                to="/seller/register"
                data-testid="enter-seller-register"
                style={{
                  textAlign: 'center',
                  textDecoration: 'none',
                  padding: '12px 16px',
                  border: '2px dashed #151515',
                  background: '#ffffff',
                  color: '#151515',
                  fontWeight: 700,
                  fontSize: '13px',
                }}
              >
                Apply as a Seller (Admin Approval Required) →
              </Link>
            </div>
          </section>

          {/* ADMIN PORTAL */}
          <section
            data-testid="portal-card-admin"
            style={{
              background: '#fff8f1',
              border: '3px solid #151515',
              boxShadow: '10px 10px 0 #ff3d9a',
              padding: '34px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '20px',
            }}
          >
            <div>
              <div className="auth-eyebrow" style={{ color: '#ff3d9a' }}>
                ■ PLATFORM GOVERNANCE
              </div>
              <h2
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 'clamp(28px, 3.5vw, 38px)',
                  lineHeight: 0.96,
                  letterSpacing: '-1.5px',
                  color: '#151515',
                  margin: '0 0 12px',
                }}
              >
                ADMIN{' '}
                <span style={{ color: '#ff3d9a', fontFamily: '"Playfair Display", serif', fontStyle: 'italic' }}>
                  CONSOLE
                </span>
              </h2>
              <p style={{ fontSize: '15px', color: '#454854', lineHeight: 1.6, margin: 0 }}>
                Review seller applications, moderate marketplace listings, and monitor platform operations.
              </p>
              <ul style={{ margin: '16px 0 0', paddingLeft: '18px', color: '#2b2d36', fontSize: '13px', lineHeight: 1.7 }}>
                <li>Approve, reject, or suspend merchant seller accounts</li>
                <li>Moderate catalog products &amp; view full audit history</li>
                <li>Access internal diagnostics &amp; service health</li>
              </ul>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link
                to="/admin/login"
                data-testid="enter-admin-login"
                className="auth-submit"
                style={{
                  textAlign: 'center',
                  textDecoration: 'none',
                  background: '#ff3d9a',
                  color: '#ffffff',
                  border: '2px solid #151515',
                }}
              >
                SIGN IN AS ADMIN ■
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
