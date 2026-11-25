import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../App.css';
import { useAuth } from '../context/AuthContext';

export default function SellerLoginPage() {
  const navigate = useNavigate();
  const { sellerLogin } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await sellerLogin(form.email, form.password);
      navigate('/seller/dashboard');
    } catch (err: any) {
      setError(err.message || 'Seller sign-in failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page" style={{ background: '#151515' }}>
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-lime" />

      <div
        className="auth-card"
        data-testid="seller-login-card"
        style={{ boxShadow: '12px 12px 0 #8d6bff', background: '#fff8f1' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '22px' }}>
          <Link to="/" className="auth-logo" style={{ marginBottom: 0 }}>
            Wear<span>Wise</span>
          </Link>
          <span
            style={{
              background: '#8d6bff',
              color: '#ffffff',
              border: '2px solid #151515',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 900,
              letterSpacing: '0.08em',
            }}
          >
            SELLER PORTAL
          </span>
        </div>

        <div className="auth-eyebrow" style={{ color: '#8d6bff' }}>◆ MERCHANT ACCESS</div>

        <h1 className="auth-title" style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}>
          SELLER
          <br />
          <span style={{ color: '#8d6bff' }}>STUDIO.</span>
        </h1>

        <p className="auth-subtitle">
          Manage your products, publish garments and grow your store.
        </p>

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label>SELLER EMAIL</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={update}
              placeholder="seller@yourbrand.studio"
              required
              autoComplete="email"
            />
          </div>

          <div className="auth-field">
            <label>PASSWORD</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={update}
              placeholder="Seller password"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="auth-error" data-testid="seller-login-error">
              {error}
            </p>
          )}

          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
            data-testid="seller-login-submit"
            style={{ background: '#151515', color: '#d8ff3f', border: '2px solid #151515' }}
          >
            {loading ? 'Verifying seller account…' : 'ENTER SELLER PORTAL ◆'}
          </button>
        </form>

        <div
          style={{
            marginTop: '18px',
            padding: '12px 14px',
            border: '2px dashed #151515',
            background: '#ffffff',
            fontSize: '12px',
            lineHeight: 1.5,
            color: '#2b2d36',
          }}
        >
          <strong>Merchant Onboarding Policy:</strong> Seller accounts are issued or approved by WearWise.{' '}
          <Link to="/seller/register" style={{ color: '#8d6bff', fontWeight: 700 }}>
            Submit a seller onboarding request →
          </Link>
        </div>

        <p className="auth-switch" style={{ marginTop: '14px', fontSize: '12px' }}>
          Shopping with WearWise?{' '}
          <Link to="/login">Use Shopper Login →</Link>
        </p>
      </div>
    </div>
  );
}
