import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SellerLayout from '../../components/seller/SellerLayout';
import { fetchSellerDashboard } from '../../api/seller';

export default function SellerDashboardPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSellerDashboard()
      .then(setData)
      .catch((err) => setError(err.message || 'Failed to load seller dashboard'))
      .finally(() => setLoading(false));
  }, []);

  const metrics = data?.metrics || {
    total_products: 0,
    published_products: 0,
    draft_products: 0,
    needs_attention: 0,
    orders_count: 0,
  };

  return (
    <SellerLayout
      title={data?.seller?.store_name ? `${data.seller.store_name} Dashboard` : 'Seller Dashboard'}
      subtitle="Live overview of your listings, garment preparation status, and incoming orders."
    >
      {loading && <p>Loading store dashboard…</p>}
      {error && <p className="auth-error">{error}</p>}

      {!loading && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div
            data-testid="seller-dashboard-metrics"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '16px',
            }}
          >
            {[
              { label: 'Total Products', value: metrics.total_products, accent: '#d8ff3f' },
              { label: 'Published', value: metrics.published_products, accent: '#ff3d9a', darkText: false },
              { label: 'Drafts', value: metrics.draft_products, accent: '#ffffff' },
              { label: 'Needs Attention', value: metrics.needs_attention, accent: '#ffad7d' },
              { label: 'Store Orders', value: metrics.orders_count, accent: '#8d6bff', darkText: false },
            ].map((card) => (
              <div
                key={card.label}
                style={{
                  background: card.accent,
                  color: card.darkText === false ? '#ffffff' : '#151515',
                  border: '2.5px solid #151515',
                  boxShadow: '5px 5px 0 #151515',
                  padding: '18px',
                }}
              >
                <div style={{ fontSize: '12px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {card.label}
                </div>
                <div style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: '34px', marginTop: '6px' }}>
                  {card.value}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '20px',
            }}
          >
            <section
              style={{
                background: '#ffffff',
                border: '2.5px solid #151515',
                boxShadow: '6px 6px 0 #151515',
                padding: '20px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 900 }}>Products Requiring Attention</h2>
                <Link to="/seller/products" style={{ fontSize: '12px', fontWeight: 800, color: '#8d6bff' }}>
                  Manage All →
                </Link>
              </div>
              {data?.attention_products?.length ? (
                <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {data.attention_products.map((p: any) => (
                    <li
                      key={p.id}
                      style={{
                        padding: '10px 12px',
                        border: '1.5px solid #151515',
                        background: '#fff8f1',
                        display: 'flex',
                        justifyContent: 'space-between',
                        gap: '10px',
                      }}
                    >
                      <div>
                        <strong>{p.name}</strong>{' '}
                        <span style={{ fontSize: '12px', color: '#555866' }}>({p.sku})</span>
                        <div style={{ fontSize: '12px', color: '#555866' }}>
                          Status: {p.status} · Stock: {p.inventory_count}
                        </div>
                      </div>
                      <Link to="/seller/studio" style={{ fontSize: '12px', fontWeight: 800, color: '#ff3d9a', alignSelf: 'center' }}>
                        Prepare →
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ margin: 0, color: '#555866', fontSize: '14px' }}>All store products are published and in stock.</p>
              )}
            </section>

            <section
              style={{
                background: '#ffffff',
                border: '2.5px solid #151515',
                boxShadow: '6px 6px 0 #151515',
                padding: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 12px', fontSize: '18px', fontWeight: 900 }}>Recent Store Activity</h2>
              {data?.recent_activity?.length ? (
                <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {data.recent_activity.map((ev: any, idx: number) => (
                    <li
                      key={`${ev.title}-${idx}`}
                      style={{
                        padding: '10px 12px',
                        borderBottom: '1px dashed #d5cfc7',
                        display: 'flex',
                        justifyContent: 'space-between',
                        gap: '10px',
                        fontSize: '13px',
                      }}
                    >
                      <span>
                        <strong>{ev.type.toUpperCase()}:</strong> {ev.title}
                      </span>
                      <span style={{ fontWeight: 800 }}>{ev.status}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ margin: 0, color: '#555866', fontSize: '14px' }}>No activity recorded yet.</p>
              )}
            </section>
          </div>
        </div>
      )}
    </SellerLayout>
  );
}
