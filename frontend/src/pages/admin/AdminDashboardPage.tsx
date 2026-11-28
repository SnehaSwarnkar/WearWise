import React, { useCallback, useEffect, useState } from 'react';
import AdminLayout, { AdminTabKey } from '../../components/admin/AdminLayout';
import {
  AdminAuditLog,
  AdminOverview,
  AdminProductRecord,
  AdminSellerRecord,
  fetchAdminAuditLogs,
  fetchAdminCustomers,
  fetchAdminHealth,
  fetchAdminOrders,
  fetchAdminOverview,
  fetchAdminProducts,
  fetchAdminSellers,
  moderateAdminProduct,
  updateAdminCustomerStatus,
  updateAdminSellerStatus,
} from '../../api/admin';

const CARD_STYLE: React.CSSProperties = {
  background: '#ffffff',
  border: '2.5px solid #151515',
  padding: '18px 20px',
  boxShadow: '4px 4px 0 #151515',
};

const BADGE_COLORS: Record<string, { bg: string; fg: string }> = {
  active: { bg: '#d8ff3f', fg: '#151515' },
  pending: { bg: '#fef08a', fg: '#713f12' },
  rejected: { bg: '#fee2e2', fg: '#991b1b' },
  suspended: { bg: '#151515', fg: '#ffffff' },
  disabled: { bg: '#fee2e2', fg: '#991b1b' },
  removed: { bg: '#e5e7eb', fg: '#374151' },
};

function StatusChip({ status }: { status?: string }) {
  const key = (status || 'active').toLowerCase();
  const c = BADGE_COLORS[key] || { bg: '#e5e7eb', fg: '#151515' };
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '3px 9px',
        fontSize: '11px',
        fontWeight: 900,
        textTransform: 'uppercase',
        border: '1.5px solid #151515',
        background: c.bg,
        color: c.fg,
      }}
    >
      {key}
    </span>
  );
}

export default function AdminDashboardPage() {
  const [tab, setTab] = useState<AdminTabKey>('overview');
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [sellers, setSellers] = useState<AdminSellerRecord[]>([]);
  const [sellerFilter, setSellerFilter] = useState<string>('');
  const [products, setProducts] = useState<AdminProductRecord[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [rejectingSellerId, setRejectingSellerId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, sl, pr, ords, cust, hl, au] = await Promise.all([
        fetchAdminOverview(),
        fetchAdminSellers(sellerFilter || undefined),
        fetchAdminProducts(),
        fetchAdminOrders(),
        fetchAdminCustomers(),
        fetchAdminHealth(),
        fetchAdminAuditLogs(),
      ]);
      setOverview(ov);
      setSellers(sl);
      setProducts(pr);
      setOrders(ords);
      setCustomers(cust);
      setHealth(hl);
      setAuditLogs(au);
    } catch (err: any) {
      setError(err.message || 'Unable to load admin metrics.');
    } finally {
      setLoading(false);
    }
  }, [sellerFilter]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const handleSellerAction = async (
    sellerId: string,
    status: 'active' | 'rejected' | 'suspended' | 'pending',
    reason?: string
  ) => {
    setFeedback(null);
    setError(null);
    try {
      await updateAdminSellerStatus(sellerId, { status, reason });
      setRejectingSellerId(null);
      setRejectReason('');
      setFeedback(`Seller status updated to "${status}".`);
      await refreshAll();
    } catch (err: any) {
      setError(err.message || 'Failed to update seller status.');
    }
  };

  const handleProductAction = async (productId: string | number, status: 'active' | 'disabled' | 'removed') => {
    setFeedback(null);
    setError(null);
    try {
      await moderateAdminProduct(productId, { moderation_status: status });
      setFeedback(`Product status updated to "${status}".`);
      await refreshAll();
    } catch (err: any) {
      setError(err.message || 'Failed to update product status.');
    }
  };

  const handleCustomerToggle = async (customerId: string, nextActive: boolean) => {
    setFeedback(null);
    setError(null);
    try {
      await updateAdminCustomerStatus(customerId, nextActive);
      setFeedback(nextActive ? 'Customer account reactivated.' : 'Customer account suspended.');
      await refreshAll();
    } catch (err: any) {
      setError(err.message || 'Failed to update customer account.');
    }
  };

  const metrics = overview?.metrics;

  return (
    <AdminLayout
      activeTab={tab}
      onSelectTab={setTab}
      pendingCount={metrics?.pending_seller_applications || 0}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: '28px', margin: 0, letterSpacing: '-0.8px' }}>
            WEARWISE PLATFORM ADMINISTRATION
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#454854' }}>
            Manage merchant onboarding, catalog moderation, orders, and system governance.
          </p>
        </div>
        <button
          type="button"
          onClick={refreshAll}
          style={{
            border: '2px solid #151515',
            background: '#ffffff',
            padding: '8px 14px',
            fontWeight: 800,
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          {loading ? 'Refreshing…' : 'Refresh Data'}
        </button>
      </div>

      {feedback && (
        <div
          data-testid="admin-feedback-banner"
          style={{
            marginBottom: '16px',
            padding: '10px 14px',
            background: '#d8ff3f',
            border: '2px solid #151515',
            fontWeight: 800,
            fontSize: '13px',
          }}
        >
          {feedback}
        </div>
      )}
      {error && (
        <div
          style={{
            marginBottom: '16px',
            padding: '10px 14px',
            background: '#fee2e2',
            border: '2px solid #991b1b',
            color: '#991b1b',
            fontWeight: 800,
            fontSize: '13px',
          }}
        >
          {error}
        </div>
      )}

      {tab === 'overview' && metrics && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '14px' }}>
            {[
              { label: 'Total Customers', value: metrics.total_customers, sub: `${metrics.active_customers} active` },
              { label: 'Approved Sellers', value: metrics.approved_sellers, sub: `${metrics.suspended_sellers} suspended` },
              { label: 'Pending Seller Apps', value: metrics.pending_seller_applications, sub: 'Awaiting review', highlight: metrics.pending_seller_applications > 0 },
              { label: 'Active Products', value: metrics.active_products, sub: `Out of ${metrics.total_products} total` },
              { label: 'Total Orders', value: metrics.total_orders, sub: `Simulated volume ₹${metrics.simulated_order_volume.toLocaleString()}` },
              { label: 'Captured Revenue', value: `₹${metrics.actual_captured_revenue.toLocaleString()}`, sub: metrics.is_demo_payments_only ? 'Simulated staging checkout only' : 'Live payment capture' },
            ].map((kpi) => (
              <div
                key={kpi.label}
                style={{
                  ...CARD_STYLE,
                  background: kpi.highlight ? '#fef08a' : '#ffffff',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', color: '#454854' }}>
                  {kpi.label}
                </div>
                <div style={{ fontSize: '28px', fontWeight: 900, margin: '6px 0 4px' }}>{kpi.value}</div>
                <div style={{ fontSize: '12px', color: '#454854' }}>{kpi.sub}</div>
              </div>
            ))}
          </div>

          <div style={CARD_STYLE}>
            <h2 style={{ fontSize: '16px', fontWeight: 900, margin: '0 0 8px' }}>Pending Seller Applications</h2>
            {sellers.filter((s) => s.status === 'pending').length === 0 ? (
              <p style={{ margin: 0, fontSize: '13px', color: '#454854' }}>
                No seller applications are currently waiting for review.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {sellers
                  .filter((s) => s.status === 'pending')
                  .map((s) => (
                    <div
                      key={s.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '12px',
                        padding: '12px',
                        border: '1.5px solid #151515',
                        background: '#fff8f1',
                      }}
                    >
                      <div>
                        <strong>{s.store_name || s.name}</strong> ({s.email})
                        <div style={{ fontSize: '12px', color: '#454854' }}>
                          Owner: {s.owner_name || s.name} · Type: {s.business_type || 'Apparel Brand'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          type="button"
                          onClick={() => handleSellerAction(s.id, 'active')}
                          style={{
                            border: '2px solid #151515',
                            background: '#d8ff3f',
                            padding: '6px 12px',
                            fontWeight: 900,
                            fontSize: '12px',
                            cursor: 'pointer',
                          }}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setTab('sellers');
                            setRejectingSellerId(s.id);
                          }}
                          style={{
                            border: '2px solid #991b1b',
                            background: '#fee2e2',
                            color: '#991b1b',
                            padding: '6px 12px',
                            fontWeight: 900,
                            fontSize: '12px',
                            cursor: 'pointer',
                          }}
                        >
                          Reject…
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'sellers' && (
        <div style={CARD_STYLE}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 900, margin: 0 }}>Seller Applications &amp; Store Management</h2>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['', 'pending', 'active', 'rejected', 'suspended'].map((f) => (
                <button
                  key={f || 'all'}
                  type="button"
                  onClick={() => setSellerFilter(f)}
                  style={{
                    border: '2px solid #151515',
                    background: sellerFilter === f ? '#151515' : '#ffffff',
                    color: sellerFilter === f ? '#d8ff3f' : '#151515',
                    padding: '5px 11px',
                    fontSize: '12px',
                    fontWeight: 800,
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                  }}
                >
                  {f || 'All'}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {sellers.map((s) => (
              <div
                key={s.id}
                data-testid={`admin-seller-row-${s.email}`}
                style={{
                  border: '2px solid #151515',
                  padding: '14px 16px',
                  background: '#fffdf9',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                      <strong style={{ fontSize: '16px' }}>{s.store_name || s.name}</strong>
                      <StatusChip status={s.status} />
                    </div>
                    <div style={{ fontSize: '13px', color: '#454854', marginTop: '4px' }}>
                      Owner: <strong>{s.owner_name || s.name}</strong> · Email: {s.email}
                      {s.phone ? ` · Phone: ${s.phone}` : ''}
                    </div>
                    <div style={{ fontSize: '12px', color: '#454854', marginTop: '2px' }}>
                      Category: {s.business_type || 'Apparel Brand'}
                      {s.business_address ? ` · Address: ${s.business_address}` : ''}
                    </div>
                    {s.store_description && (
                      <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#2b2d36' }}>{s.store_description}</p>
                    )}
                    {s.rejection_reason && (
                      <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#991b1b', fontWeight: 700 }}>
                        Rejection Reason: {s.rejection_reason}
                      </p>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {s.status !== 'active' && (
                      <button
                        type="button"
                        data-testid={`approve-seller-${s.id}`}
                        onClick={() => handleSellerAction(s.id, 'active')}
                        style={{
                          border: '2px solid #151515',
                          background: '#d8ff3f',
                          padding: '7px 12px',
                          fontWeight: 900,
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        {s.status === 'suspended' ? 'Reactivate' : 'Approve'}
                      </button>
                    )}
                    {s.status === 'pending' && (
                      <button
                        type="button"
                        data-testid={`reject-seller-${s.id}`}
                        onClick={() => {
                          setRejectingSellerId(s.id);
                          setRejectReason('');
                        }}
                        style={{
                          border: '2px solid #991b1b',
                          background: '#fee2e2',
                          color: '#991b1b',
                          padding: '7px 12px',
                          fontWeight: 900,
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        Reject
                      </button>
                    )}
                    {s.status === 'active' && (
                      <button
                        type="button"
                        data-testid={`suspend-seller-${s.id}`}
                        onClick={() => handleSellerAction(s.id, 'suspended')}
                        style={{
                          border: '2px solid #151515',
                          background: '#151515',
                          color: '#ffffff',
                          padding: '7px 12px',
                          fontWeight: 800,
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        Suspend
                      </button>
                    )}
                  </div>
                </div>

                {rejectingSellerId === s.id && (
                  <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1.5px dashed #151515', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <input
                      type="text"
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      placeholder="Reason for rejection (shared with applicant)"
                      style={{ flex: 1, minWidth: '220px', padding: '7px 10px', border: '2px solid #151515' }}
                    />
                    <button
                      type="button"
                      onClick={() => handleSellerAction(s.id, 'rejected', rejectReason || 'Application criteria not met.')}
                      style={{
                        border: '2px solid #991b1b',
                        background: '#991b1b',
                        color: '#ffffff',
                        padding: '7px 14px',
                        fontWeight: 900,
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      Confirm Reject
                    </button>
                    <button
                      type="button"
                      onClick={() => setRejectingSellerId(null)}
                      style={{ border: '2px solid #151515', background: '#ffffff', padding: '7px 12px', fontSize: '12px', fontWeight: 700 }}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'products' && (
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 14px' }}>Marketplace Product Moderation</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #151515', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>Product</th>
                  <th style={{ padding: '8px' }}>Seller</th>
                  <th style={{ padding: '8px' }}>Section</th>
                  <th style={{ padding: '8px' }}>Price</th>
                  <th style={{ padding: '8px' }}>Status</th>
                  <th style={{ padding: '8px' }}>Moderation</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={String(p.id)} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '8px' }}>
                      <strong>{p.name}</strong>
                      {p.sku && <div style={{ fontSize: '11px', color: '#6b7280' }}>{p.sku}</div>}
                    </td>
                    <td style={{ padding: '8px' }}>{p.seller_name || 'Platform Catalog'}</td>
                    <td style={{ padding: '8px', textTransform: 'capitalize' }}>
                      {p.gender || 'unisex'} · {p.category}
                    </td>
                    <td style={{ padding: '8px' }}>₹{Number(p.price || 0).toLocaleString()}</td>
                    <td style={{ padding: '8px' }}>
                      <StatusChip status={p.moderation_status || p.status} />
                    </td>
                    <td style={{ padding: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {p.moderation_status !== 'disabled' ? (
                        <button
                          type="button"
                          onClick={() => handleProductAction(p.sku || p.id, 'disabled')}
                          style={{ border: '1.5px solid #991b1b', background: '#fee2e2', color: '#991b1b', padding: '4px 9px', fontSize: '11px', fontWeight: 800, cursor: 'pointer' }}
                        >
                          Disable
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleProductAction(p.sku || p.id, 'active')}
                          style={{ border: '1.5px solid #151515', background: '#d8ff3f', padding: '4px 9px', fontSize: '11px', fontWeight: 800, cursor: 'pointer' }}
                        >
                          Restore
                        </button>
                      )}
                      {p.moderation_status !== 'removed' && (
                        <button
                          type="button"
                          onClick={() => handleProductAction(p.sku || p.id, 'removed')}
                          style={{ border: '1.5px solid #151515', background: '#ffffff', padding: '4px 9px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                        >
                          Remove
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'orders' && (
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 6px' }}>Platform Orders (Simulated Staging Checkout)</h2>
          <p style={{ margin: '0 0 14px', fontSize: '12px', color: '#454854' }}>
            Orders below reflect storefront staging checkouts; no live payment gateway capture is active in staging.
          </p>
          {orders.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#454854' }}>No orders placed yet.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #151515', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Order ID</th>
                    <th style={{ padding: '8px' }}>Items</th>
                    <th style={{ padding: '8px' }}>Total</th>
                    <th style={{ padding: '8px' }}>Status</th>
                    <th style={{ padding: '8px' }}>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '8px', fontWeight: 800 }}>{o.id}</td>
                      <td style={{ padding: '8px' }}>{(o.items || []).map((i: any) => `${i.name} (${i.size || 'M'})`).join(', ')}</td>
                      <td style={{ padding: '8px' }}>₹{Number(o.total || 0).toLocaleString()}</td>
                      <td style={{ padding: '8px' }}><StatusChip status={o.status || 'placed'} /></td>
                      <td style={{ padding: '8px', fontSize: '12px' }}>{o.createdAt ? new Date(o.createdAt).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'customers' && (
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 14px' }}>Registered Customer Accounts</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #151515', textAlign: 'left' }}>
                  <th style={{ padding: '8px' }}>Name</th>
                  <th style={{ padding: '8px' }}>Email</th>
                  <th style={{ padding: '8px' }}>Status</th>
                  <th style={{ padding: '8px' }}>Orders</th>
                  <th style={{ padding: '8px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => {
                  const active = c.is_active !== false && c.status !== 'suspended';
                  return (
                    <tr key={c.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '8px', fontWeight: 700 }}>{c.name}</td>
                      <td style={{ padding: '8px' }}>{c.email}</td>
                      <td style={{ padding: '8px' }}><StatusChip status={active ? 'active' : 'suspended'} /></td>
                      <td style={{ padding: '8px' }}>{c.order_count ?? 0}</td>
                      <td style={{ padding: '8px' }}>
                        <button
                          type="button"
                          onClick={() => handleCustomerToggle(c.id, !active)}
                          style={{
                            border: '1.5px solid #151515',
                            background: active ? '#151515' : '#d8ff3f',
                            color: active ? '#ffffff' : '#151515',
                            padding: '5px 10px',
                            fontSize: '11px',
                            fontWeight: 800,
                            cursor: 'pointer',
                          }}
                        >
                          {active ? 'Suspend' : 'Reactivate'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'health' && (
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 10px' }}>Admin-Only Platform Health &amp; Service Diagnostics</h2>
          <p style={{ fontSize: '13px', color: '#454854', margin: '0 0 14px' }}>
            These system diagnostics are visible strictly to authenticated Administrators and never exposed on customer pages.
          </p>
          <pre
            style={{
              background: '#151515',
              color: '#d8ff3f',
              padding: '16px',
              overflowX: 'auto',
              fontSize: '12px',
              lineHeight: 1.5,
              border: '2px solid #151515',
            }}
          >
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}

      {tab === 'audit' && (
        <div style={CARD_STYLE}>
          <h2 style={{ fontSize: '18px', fontWeight: 900, margin: '0 0 14px' }}>Administrative Action Audit Log</h2>
          {auditLogs.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#454854' }}>No admin actions recorded yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {auditLogs.map((a) => (
                <div key={a.id} style={{ padding: '10px 12px', border: '1.5px solid #151515', fontSize: '12px' }}>
                  <strong>{a.action}</strong> on {a.target_type} <code>{a.target_id}</code> by <strong>{a.admin_email}</strong> ·{' '}
                  {new Date(a.timestamp).toLocaleString()}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </AdminLayout>
  );
}
