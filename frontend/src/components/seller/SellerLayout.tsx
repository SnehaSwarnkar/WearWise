import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  PlusSquare,
  Boxes,
  ShoppingBag,
  Sparkles,
  Store,
  Settings,
  LogOut,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const SELLER_NAV = [
  { label: 'Dashboard', to: '/seller/dashboard', icon: LayoutDashboard },
  { label: 'Products', to: '/seller/products', icon: Package },
  { label: 'Add Product', to: '/seller/products/new', icon: PlusSquare },
  { label: 'Garment Studio', to: '/seller/studio', icon: Sparkles },
  { label: 'Inventory', to: '/seller/inventory', icon: Boxes },
  { label: 'Orders', to: '/seller/orders', icon: ShoppingBag },
  { label: 'Store Profile', to: '/seller/profile', icon: Store },
  { label: 'Settings', to: '/seller/settings', icon: Settings },
];

export default function SellerLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/seller/login');
  };

  return (
    <div
      data-testid="seller-portal-shell"
      style={{
        minHeight: '100vh',
        background: '#fff8f1',
        color: '#151515',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Top Seller Header */}
      <header
        style={{
          background: '#151515',
          color: '#fff8f1',
          borderBottom: '3px solid #151515',
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <Link
            to="/seller/dashboard"
            style={{
              fontFamily: '"Archivo Black", sans-serif',
              fontSize: '20px',
              color: '#fff8f1',
              textDecoration: 'none',
              letterSpacing: '-0.8px',
            }}
          >
            Wear<span style={{ color: '#ff3d9a' }}>Wise</span>
          </Link>
          <span
            style={{
              background: '#8d6bff',
              color: '#ffffff',
              padding: '3px 9px',
              fontSize: '11px',
              fontWeight: 900,
              letterSpacing: '0.08em',
              border: '1.5px solid #fff8f1',
            }}
          >
            SELLER PORTAL
          </span>
          {user?.store_name && (
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#d8ff3f' }}>
              {user.store_name}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <Link
            to="/explore"
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
            Public Marketplace <ExternalLink size={13} />
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            data-testid="seller-logout-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: '#ff3d9a',
              color: '#ffffff',
              border: '2px solid #fff8f1',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
            }}
          >
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </header>

      {/* Secondary Horizontal / Responsive Seller Navigation */}
      <nav
        aria-label="Seller navigation"
        data-testid="seller-portal-nav"
        style={{
          background: '#ffffff',
          borderBottom: '2px solid #151515',
          padding: '10px 24px',
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
        }}
      >
        {SELLER_NAV.map((item) => {
          const Icon = item.icon;
          const active = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 12px',
                fontSize: '13px',
                fontWeight: 800,
                textDecoration: 'none',
                color: '#151515',
                background: active ? '#d8ff3f' : '#fff8f1',
                border: '2px solid #151515',
                boxShadow: active ? '3px 3px 0 #151515' : 'none',
              }}
            >
              <Icon size={15} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, maxWidth: '1240px', width: '100%', margin: '0 auto', padding: '26px 20px 56px' }}>
        <div style={{ marginBottom: '22px' }}>
          <h1
            style={{
              fontFamily: '"Archivo Black", sans-serif',
              fontSize: 'clamp(24px, 3vw, 34px)',
              margin: '0 0 6px',
              letterSpacing: '-0.8px',
            }}
          >
            {title}
          </h1>
          {subtitle && (
            <p style={{ margin: 0, color: '#555866', fontSize: '14px' }}>{subtitle}</p>
          )}
        </div>
        {children}
      </main>
    </div>
  );
}
