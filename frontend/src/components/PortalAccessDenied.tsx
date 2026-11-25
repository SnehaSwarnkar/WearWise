import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css';

export default function PortalAccessDenied({
  requiredPortal,
  message,
  returnTo,
  returnLabel,
}: {
  requiredPortal: 'Seller Portal' | 'Shopper Portal';
  message: string;
  returnTo: string;
  returnLabel: string;
}) {
  return (
    <div className="auth-page" style={{ background: '#151515' }}>
      <div
        className="auth-card"
        data-testid={requiredPortal === 'Seller Portal' ? 'seller-access-denied' : 'shopper-access-denied'}
        style={{ background: '#fff8f1', boxShadow: '12px 12px 0 #ff3d9a' }}
      >
        <div className="auth-eyebrow" style={{ color: '#ff3d9a' }}>
          403 · ACCESS RESTRICTED
        </div>
        <h1 className="auth-title" style={{ fontSize: '36px', letterSpacing: '-1.5px' }}>
          PORTAL <span style={{ color: '#ff3d9a' }}>RESTRICTED.</span>
        </h1>
        <p className="auth-subtitle" style={{ color: '#151515' }}>
          {message}
        </p>
        <Link
          to={returnTo}
          className="auth-submit"
          style={{ display: 'block', textAlign: 'center', textDecoration: 'none' }}
        >
          {returnLabel}
        </Link>
      </div>
    </div>
  );
}
