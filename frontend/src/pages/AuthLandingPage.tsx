import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css';

/**
 * Dual-Portal WearWise Authentication Entry Experience (`/auth`)
 * Clearly separates Shopper Portal vs Seller Portal entry points.
 */
export default function AuthLandingPage() {
  return (
    <div className="auth-page auth-portal-landing" style={{ padding: '40px 20px' }}>
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />
      <div className="auth-shape auth-shape-pink" />

      <div style={{ position: 'relative', zIndex: 1, width: 'min(980px, 100%)' }}>
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
            to="/explore"
            style={{
              color: '#fff8f1',
              fontSize: '13px',
              fontWeight: 700,
              textDecoration: 'underline',
              letterSpacing: '0.04em',
            }}
          >
            Browse Public Marketplace →
          </Link>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '24px',
          }}
        >
          {/* SHOPPER LOGIN PORTAL */}
          <section
            data-testid="portal-card-shopper"
            style={{
              background: '#fff8f1',
              border: '3px solid #151515',
              boxShadow: '10px 10px 0 #d8ff3f',
              padding: '38px 34px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '22px',
            }}
          >
            <div>
              <div className="auth-eyebrow" style={{ color: '#ff3d9a' }}>
                ✦ CUSTOMER EXPERIENCE
              </div>
              <h1
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 'clamp(30px, 4vw, 42px)',
                  lineHeight: 0.94,
                  letterSpacing: '-1.8px',
                  color: '#151515',
                  margin: '0 0 14px',
                }}
              >
                SHOPPER <span style={{ color: '#ff3d9a', fontFamily: '"Playfair Display", serif', fontStyle: 'italic' }}>LOGIN</span>
              </h1>
              <p style={{ fontSize: '15px', color: '#454854', lineHeight: 1.6, margin: 0 }}>
                Discover fashion, find your fit and shop with WearWise.
              </p>
              <ul style={{ margin: '18px 0 0', paddingLeft: '18px', color: '#2b2d36', fontSize: '13px', lineHeight: 1.7 }}>
                <li>Explore dual-mode Image &amp; 3D Try-On garments</li>
                <li>Save wardrobe items, looks, and personal body fit profiles</li>
                <li>Track bag items, checkout, and order history</li>
              </ul>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link
                to="/login"
                data-testid="enter-shopper-login"
                className="auth-submit"
                style={{ textAlign: 'center', textDecoration: 'none' }}
              >
                SIGN IN AS SHOPPER ✦
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
                CREATE SHOPPER ACCOUNT →
              </Link>
            </div>
          </section>

          {/* SELLER LOGIN PORTAL */}
          <section
            data-testid="portal-card-seller"
            style={{
              background: '#fff8f1',
              border: '3px solid #151515',
              boxShadow: '10px 10px 0 #8d6bff',
              padding: '38px 34px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '22px',
            }}
          >
            <div>
              <div className="auth-eyebrow" style={{ color: '#8d6bff' }}>
                ◆ MERCHANT CONSOLE
              </div>
              <h2
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 'clamp(30px, 4vw, 42px)',
                  lineHeight: 0.94,
                  letterSpacing: '-1.8px',
                  color: '#151515',
                  margin: '0 0 14px',
                }}
              >
                SELLER <span style={{ color: '#8d6bff', fontFamily: '"Playfair Display", serif', fontStyle: 'italic' }}>LOGIN</span>
              </h2>
              <p style={{ fontSize: '15px', color: '#454854', lineHeight: 1.6, margin: 0 }}>
                Manage your products, publish garments and grow your store.
              </p>
              <ul style={{ margin: '18px 0 0', paddingLeft: '18px', color: '#2b2d36', fontSize: '13px', lineHeight: 1.7 }}>
                <li>Create listings, upload photos, and manage inventory</li>
                <li>Configure Image Try-On &amp; 3D digital garment preparation</li>
                <li>View store orders and fulfill customer purchases</li>
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
                Request Seller Access (WearWise Approval Required) →
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
