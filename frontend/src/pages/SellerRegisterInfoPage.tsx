import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../App.css';
import { applyForSeller } from '../api/auth';

export default function SellerRegisterInfoPage() {
  const [form, setForm] = useState({
    owner_name: '',
    store_name: '',
    email: '',
    phone: '',
    business_type: 'Apparel Brand',
    business_address: '',
    store_description: '',
    password: '',
  });
  const [submittedMsg, setSubmittedMsg] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmittedMsg('');
    setLoading(true);
    try {
      const res = await applyForSeller({
        ...form,
        name: form.owner_name,
      });
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
        style={{ width: 'min(620px, 100%)', background: '#fff8f1', boxShadow: '12px 12px 0 #d8ff3f' }}
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
            ADMIN APPROVAL REQUIRED
          </span>
        </div>

        <h1 className="auth-title" style={{ fontSize: 'clamp(30px, 4vw, 44px)', letterSpacing: '-1.5px' }}>
          SELLER <span style={{ color: '#8d6bff' }}>APPLICATION.</span>
        </h1>
        <p className="auth-subtitle" style={{ marginBottom: '18px' }}>
          Submit your store details for review by WearWise Administrators. Access to Seller Portal opens once approved.
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
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <div className="auth-field">
                <label>OWNER / CONTACT NAME *</label>
                <input name="owner_name" value={form.owner_name} onChange={update} required placeholder="Founder or Studio Lead" />
              </div>
              <div className="auth-field">
                <label>STORE / BRAND NAME *</label>
                <input name="store_name" value={form.store_name} onChange={update} required placeholder="Studio / Brand Name" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <div className="auth-field">
                <label>BUSINESS EMAIL *</label>
                <input type="email" name="email" value={form.email} onChange={update} required placeholder="merchant@brand.com" />
              </div>
              <div className="auth-field">
                <label>PHONE NUMBER</label>
                <input type="tel" name="phone" value={form.phone} onChange={update} placeholder="+91 98XXXXXXXX" />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <div className="auth-field">
                <label>BUSINESS TYPE</label>
                <select
                  name="business_type"
                  value={form.business_type}
                  onChange={update}
                  style={{ padding: '11px 12px', border: '2px solid #151515', background: '#ffffff', fontWeight: 600 }}
                >
                  <option value="Apparel Brand">Apparel Brand</option>
                  <option value="Boutique Studio">Boutique Studio</option>
                  <option value="Streetwear Label">Streetwear Label</option>
                  <option value="Ethnic & Occasionwear">Ethnic &amp; Occasionwear</option>
                  <option value="Kidswear Brand">Kidswear Brand</option>
                  <option value="Marketplace Retailer">Marketplace Retailer</option>
                </select>
              </div>
              <div className="auth-field">
                <label>APPLICATION PASSWORD *</label>
                <input type="password" name="password" value={form.password} onChange={update} required minLength={6} placeholder="Min. 6 characters" />
              </div>
            </div>

            <div className="auth-field">
              <label>BUSINESS ADDRESS</label>
              <input name="business_address" value={form.business_address} onChange={update} placeholder="Studio city, state, country" />
            </div>

            <div className="auth-field">
              <label>BRAND DESCRIPTION &amp; CATALOG NOTES</label>
              <textarea
                name="store_description"
                value={form.store_description}
                onChange={update}
                rows={3}
                placeholder="Categories, typical sizing range, and what you plan to sell on WearWise"
                style={{ padding: '10px', border: '2px solid #151515', background: '#ffffff', fontFamily: 'inherit' }}
              />
            </div>

            {error && <p className="auth-error">{error}</p>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? 'Submitting Application…' : 'SUBMIT SELLER APPLICATION →'}
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
