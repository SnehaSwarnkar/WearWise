import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../App.css';
import { applyForSeller } from '../api/auth';

export default function SellerRegisterInfoPage() {
  const [form, setForm] = useState({
    name: '',
    email: '',
    store_name: '',
    store_description: '',
    password: '',
  });
  const [submittedMsg, setSubmittedMsg] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmittedMsg('');
    setLoading(true);
    try {
      const res = await applyForSeller(form);
      setSubmittedMsg(res.message);
    } catch (err: any) {
      setError(err.message || 'Could not submit application.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page" style={{ background: '#151515', padding: '36px 20px' }}>
      <div className="auth-shape auth-shape-purple" />
      <div className="auth-shape auth-shape-pink" />

      <div
        className="auth-card"
        data-testid="seller-register-info-card"
        style={{ width: 'min(560px, 100%)', background: '#fff8f1', boxShadow: '12px 12px 0 #d8ff3f' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <Link to="/auth" className="auth-logo" style={{ marginBottom: 0 }}>
            Wear<span>Wise</span>
          </Link>
          <span
            style={{
              background: '#ff3d9a',
              color: '#ffffff',
              border: '2px solid #151515',
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 900,
            }}
          >
            APPROVAL REQUIRED
          </span>
        </div>

        <h1 className="auth-title" style={{ fontSize: 'clamp(30px, 4vw, 44px)', letterSpacing: '-1.5px' }}>
          BECOME A <span style={{ color: '#8d6bff' }}>SELLER.</span>
        </h1>
        <p className="auth-subtitle" style={{ marginBottom: '18px' }}>
          Seller accounts are issued or approved by WearWise. Public sign-up does not grant immediate merchant publishing permissions.
        </p>

        {submittedMsg ? (
          <div
            data-testid="seller-apply-confirmation"
            style={{
              padding: '16px',
              border: '2px solid #151515',
              background: '#d8ff3f',
              color: '#151515',
              fontSize: '14px',
              lineHeight: 1.5,
              marginBottom: '16px',
            }}
          >
            <strong>Application Recorded (Pending Approval):</strong> {submittedMsg}
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label>CONTACT NAME</label>
              <input name="name" value={form.name} onChange={update} required placeholder="Founder or Studio Lead" />
            </div>
            <div className="auth-field">
              <label>STORE NAME</label>
              <input name="store_name" value={form.store_name} onChange={update} required placeholder="Studio / Brand Name" />
            </div>
            <div className="auth-field">
              <label>BUSINESS EMAIL</label>
              <input type="email" name="email" value={form.email} onChange={update} required placeholder="merchant@brand.com" />
            </div>
            <div className="auth-field">
              <label>APPLICATION PASSWORD</label>
              <input type="password" name="password" value={form.password} onChange={update} required placeholder="Min. 6 characters" />
            </div>
            <div className="auth-field">
              <label>BRAND DESCRIPTION</label>
              <textarea
                name="store_description"
                value={form.store_description}
                onChange={update}
                rows={3}
                placeholder="Categories, sizing standards, and try-on goals"
                style={{ padding: '10px', border: '2px solid #151515', background: '#ffffff', fontFamily: 'inherit' }}
              />
            </div>

            {error && <p className="auth-error">{error}</p>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? 'Submitting…' : 'REQUEST WEARWISE SELLER APPROVAL →'}
            </button>
          </form>
        )}

        <p className="auth-switch" style={{ marginTop: '16px' }}>
          Already approved? <Link to="/seller/login">Sign in to Seller Portal →</Link>
        </p>
      </div>
    </div>
  );
}
