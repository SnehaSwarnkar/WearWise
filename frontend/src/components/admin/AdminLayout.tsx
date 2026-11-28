import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UserCheck,
  PackageSearch,
  ShoppingCart,
  Users,
  Activity,
  History,
  LogOut,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export type AdminTabKey =
  | 'overview'
  | 'sellers'
  | 'products'
  | 'orders'
  | 'customers'
  | 'health'
  | 'audit';

const ADMIN_TABS: { id: AdminTabKey; label: string; icon: React.ComponentType<{ size?: number }> }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'sellers', label: 'Sellers & Approvals', icon: UserCheck },
  { id: 'products', label: 'Product Moderation', icon: PackageSearch },
  { id: 'orders', label: 'Orders', icon: ShoppingCart },
  { id: 'customers', label: 'Customers', icon: Users },
  { id: 'health', label: 'Platform Health', icon: Activity },
  { id: 'audit', label: 'Audit Trail', icon: History },
];

export default function AdminLayout({
  activeTab,
  onSelectTab,
  pendingCount = 0,
  children,
}: {
  activeTab: AdminTabKey;
  onSelectTab: (tab: AdminTabKey) => void;
  pendingCount?: number;
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  return (
    <div
      data-testid="admin-portal-shell"
      style={{
        minHeight: '100vh',
        background: '#f7f4ee',
        color: '#151515',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <header
        style={{
          background: '#151515',
          color: '#fff8f1',
          borderBottom: '3px solid #151515',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '14px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <Link
            to="/admin"
            style={{
              fontFamily: '"Archivo Black", sans-serif',
              fontSize: '20px',
              color: '#fff8f1',
              textDecoration: 'none',
            }}
          >
            Wear<span style={{ color: '#ff3d9a' }}>Wise</span>
          </Link>
          <span
            style={{
              background: '#ff3d9a',
              color: '#ffffff',
              padding: '3px 10px',
              fontSize: '11px',
              fontWeight: 900,
              letterSpacing: '0.08em',
              border: '1.5px solid #fff8f1',
            }}
          >
            ADMIN PORTAL
          </span>
          <span style={{ fontSize: '12px', opacity: 0.8 }}>{user?.email}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <Link
            to="/admin/diagnostics"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: '#d8ff3f',
              fontSize: '12px',
              fontWeight: 800,
              textDecoration: 'none',
              border: '1.5px solid #d8ff3f',
              padding: '6px 11px',
            }}
          >
            Internal Diagnostics <ExternalLink size={13} />
          </Link>
          <Link
            to="/shop"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: '#fff8f1',
              fontSize: '12px',
              fontWeight: 700,
              textDecoration: 'none',
              border: '1.5px solid rgba(255,248,241,0.35)',
              padding: '6px 11px',
            }}
          >
            Storefront <ExternalLink size={13} />
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            data-testid="admin-logout-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: '#ffffff',
              color: '#151515',
              border: '2px solid #151515',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
            }}
          >
            <LogOut size={13} /> Sign Out
          </button>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, flexWrap: 'wrap' }}>
        <aside
          data-testid="admin-portal-nav"
          style={{
            width: '240px',
            flex: '0 0 240px',
            background: '#ffffff',
            borderRight: '2.5px solid #151515',
            padding: '18px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          {ADMIN_TABS.map((t) => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                data-testid={`admin-nav-${t.id}`}
                onClick={() => onSelectTab(t.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '10px',
                  width: '100%',
                  textAlign: 'left',
                  padding: '10px 12px',
                  border: active ? '2px solid #151515' : '2px solid transparent',
                  background: active ? '#d8ff3f' : 'transparent',
                  color: '#151515',
                  fontWeight: active ? 900 : 700,
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '9px' }}>
                  <Icon size={16} />
                  {t.label}
                </span>
                {t.id === 'sellers' && pendingCount > 0 && (
                  <span
                    style={{
                      background: '#ff3d9a',
                      color: '#ffffff',
                      fontSize: '11px',
                      fontWeight: 900,
                      padding: '1px 7px',
                      borderRadius: '999px',
                    }}
                  >
                    {pendingCount}
                  </span>
                )}
              </button>
            );
          })}
        </aside>

        <main style={{ flex: 1, minWidth: '300px', padding: '24px 28px', maxWidth: '1280px' }}>
          {children}
        </main>
      </div>
    </div>
  );
}
