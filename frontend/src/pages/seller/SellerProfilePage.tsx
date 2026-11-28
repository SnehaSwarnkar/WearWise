import React, { useEffect, useState } from 'react';
import SellerLayout from '../../components/seller/SellerLayout';
import { fetchSellerProfile, updateSellerProfile } from '../../api/seller';
import { useAuth } from '../../context/AuthContext';

export default function SellerProfilePage({ settingsMode = false }: { settingsMode?: boolean }) {
  const { refreshUser } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [form, setForm] = useState({
    name: '',
    store_name: '',
    business_email: '',
    brand_tagline: '',
    store_description: '',
  });
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSellerProfile()
      .then((p) => {
        setProfile(p);
        setForm({
          name: p.name || '',
          store_name: p.store_name || '',
          business_email: p.business_email || p.email || '',
          brand_tagline: p.brand_tagline || '',
          store_description: p.store_description || '',
        });
      })
      .catch((err) => setError(err.message || 'Failed to load seller profile'));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setNotice('');
    setError('');
    try {
      const updated = await updateSellerProfile(form);
      setProfile(updated);
      await refreshUser();
      setNotice('Store details updated cleanly.');
    } catch (err: any) {
      setError(err.message || 'Failed to save store profile');
    }
  };

  return (
    <SellerLayout
      title={settingsMode ? 'Seller Settings & Verification' : 'Store Profile'}
      subtitle="Manage your approved brand identity and store information shown on WearWise."
    >
      {error && <p className="auth-error">{error}</p>}
      {notice && (
        <div style={{ padding: '10px 14px', border: '2px solid #151515', background: '#d8ff3f', marginBottom: '16px', fontWeight: 700 }}>
          {notice}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        <form
          onSubmit={handleSave}
          style={{
            background: '#ffffff',
            border: '2.5px solid #151515',
            boxShadow: '6px 6px 0 #151515',
            padding: '22px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <label className="auth-field">
            <span>STORE DISPLAY NAME</span>
            <input value={form.store_name} onChange={(e) => setForm({ ...form, store_name: e.target.value })} required />
          </label>
          <label className="auth-field">
            <span>MERCHANT CONTACT NAME</span>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label className="auth-field">
            <span>BUSINESS EMAIL</span>
            <input type="email" value={form.business_email} onChange={(e) => setForm({ ...form, business_email: e.target.value })} />
          </label>
          <label className="auth-field">
            <span>BRAND TAGLINE</span>
            <input value={form.brand_tagline} onChange={(e) => setForm({ ...form, brand_tagline: e.target.value })} />
          </label>
          <label className="auth-field">
            <span>STORE DESCRIPTION</span>
            <textarea
              rows={3}
              value={form.store_description}
              onChange={(e) => setForm({ ...form, store_description: e.target.value })}
              style={{ padding: '10px', border: '2px solid #151515', fontFamily: 'inherit' }}
            />
          </label>
          <button type="submit" className="auth-submit">
            SAVE STORE PROFILE
          </button>
        </form>

        <section
          style={{
            background: '#ffffff',
            border: '2.5px solid #151515',
            boxShadow: '6px 6px 0 #8d6bff',
            padding: '22px',
            height: 'fit-content',
          }}
        >
          <h2 style={{ margin: '0 0 14px', fontSize: '18px', fontWeight: 900 }}>Account Verification &amp; Access</h2>
          <dl style={{ margin: 0, display: 'grid', rowGap: '10px', fontSize: '13px' }}>
            <div>
              <dt style={{ fontWeight: 800, color: '#707482' }}>ACCOUNT ROLE</dt>
              <dd style={{ margin: '2px 0 0', fontWeight: 800 }}>{profile?.role || 'seller'}</dd>
            </div>
            <div>
              <dt style={{ fontWeight: 800, color: '#707482' }}>APPROVAL STATUS</dt>
              <dd style={{ margin: '2px 0 0', fontWeight: 800 }}>
                {profile?.seller_approved ? 'Approved & Active' : 'Pending Approval'}
              </dd>
            </div>
            <div>
              <dt style={{ fontWeight: 800, color: '#707482' }}>STORE BRAND ID</dt>
              <dd style={{ margin: '2px 0 0', fontFamily: 'monospace' }}>{profile?.brand_id || '—'}</dd>
            </div>
            <div>
              <dt style={{ fontWeight: 800, color: '#707482' }}>AUTHENTICATION EMAIL</dt>
              <dd style={{ margin: '2px 0 0' }}>{profile?.email || '—'}</dd>
            </div>
          </dl>
        </section>
      </div>
    </SellerLayout>
  );
}
