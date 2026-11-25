import React, { useEffect, useState } from 'react';
import SellerLayout from '../../components/seller/SellerLayout';
import { fetchSellerOrders, updateSellerOrderStatus } from '../../api/seller';

export default function SellerOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetchSellerOrders();
      setOrders(res.orders || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load store orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleStatusChange = async (orderId: string, status: string) => {
    setError('');
    try {
      await updateSellerOrderStatus(orderId, status);
      await loadOrders();
    } catch (err: any) {
      setError(err.message || 'Failed to update order status');
    }
  };

  return (
    <SellerLayout
      title="Store Orders"
      subtitle="Customer orders containing garments owned by your WearWise store."
    >
      {error && <p className="auth-error">{error}</p>}
      {loading ? (
        <p>Loading store orders…</p>
      ) : orders.length === 0 ? (
        <div
          data-testid="seller-orders-empty"
          style={{ padding: '24px', background: '#ffffff', border: '2px solid #151515' }}
        >
          No orders have been placed for your store items yet.
        </div>
      ) : (
        <div data-testid="seller-orders-list" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {orders.map((ord) => (
            <div
              key={ord.id}
              data-testid={`seller-order-${ord.id}`}
              style={{
                background: '#ffffff',
                border: '2px solid #151515',
                boxShadow: '4px 4px 0 #151515',
                padding: '18px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '10px' }}>
                <div>
                  <strong style={{ fontSize: '16px' }}>Order #{ord.id}</strong>
                  <div style={{ fontSize: '13px', color: '#454854' }}>
                    Customer: {ord.customer_name} · {ord.shipping_city}{ord.shipping_state ? `, ${ord.shipping_state}` : ''} · Payment: {String(ord.paymentMethod || '').toUpperCase()}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <strong>₹{ord.seller_subtotal}</strong>
                  <select
                    value={ord.status}
                    onChange={(e) => handleStatusChange(ord.id, e.target.value)}
                    style={{ padding: '6px 10px', border: '2px solid #151515', fontWeight: 800, background: '#d8ff3f' }}
                  >
                    {['Confirmed', 'Packed', 'Shipped', 'Delivered', 'Cancelled'].map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
              </div>
              <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#2b2d36' }}>
                {(ord.items || []).map((it: any, idx: number) => (
                  <li key={`${it.sku || it.id}-${idx}`}>
                    {it.name} ({it.sku || `ID ${it.id}`}) — Size {it.size || 'M'} × {it.quantity || 1} — ₹{it.price}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </SellerLayout>
  );
}
