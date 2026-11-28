import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import App from '../App';

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Phase 13 Customer, Avatar & Admin Experience', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('shows clean customer navigation without merchant or telemetry labels on /home', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/me')) {
        return Promise.resolve({ ok: false, status: 401, json: async () => ({}) });
      }
      if (url.includes('/api/products/recommendations')) {
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      }
      if (url.includes('/api/products')) {
        return Promise.resolve({ ok: true, json: async () => [] });
      }
      if (url.includes('/api/cart')) {
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    }) as any;

    renderAt('/home');

    const header = await screen.findByTestId('customer-header');
    for (const label of ['Home', 'Explore', 'Shop', 'Avatar', 'Wishlist', 'Orders', 'Cart', 'Profile']) {
      expect(header.textContent).toContain(label);
    }
    expect(document.body.textContent).not.toMatch(/Vertex Count|Triangle Count|Manifold Status|Boundary Edges|BICE|ISO 7250/i);
  });

  it('shows consumer onboarding text on /avatar when customer has no saved avatar yet', async () => {
    const shopper = { id: 'cust-1', name: 'Riya', email: 'shopper@wearwise.test', role: 'shopper', status: 'active' };
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/me')) {
        return Promise.resolve({ ok: true, json: async () => shopper });
      }
      if (url.includes('/api/v1/profiles')) {
        return Promise.resolve({ ok: true, json: async () => [] });
      }
      if (url.includes('/api/orders')) {
        return Promise.resolve({ ok: true, json: async () => [] });
      }
      if (url.includes('/api/cart')) {
        return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
      }
      return Promise.resolve({ ok: true, json: async () => ({ status: 'healthy' }) });
    }) as any;

    renderAt('/avatar');
    await waitFor(() => {
      expect(screen.getByTestId('avatar-onboarding')).toBeTruthy();
    });
    expect(screen.getByText(/You can create your body profile to see how clothing sizes and fit may suit your body\./i)).toBeTruthy();
    expect(screen.getByTestId('create-my-avatar-btn').getAttribute('href')).toBe('/avatar/create');
  });

  it('blocks non-admin shoppers from /admin and renders Admin Console for authenticated admins', async () => {
    const shopper = { id: 'cust-1', name: 'Riya', email: 'shopper@wearwise.test', role: 'shopper', status: 'active' };
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/me')) {
        return Promise.resolve({ ok: true, json: async () => shopper });
      }
      return Promise.resolve({ ok: true, json: async () => ({ status: 'healthy' }) });
    }) as any;

    const { unmount } = renderAt('/admin');
    await waitFor(() => {
      expect(screen.getByTestId('admin-access-denied')).toBeTruthy();
    });
    unmount();

    const admin = { id: 'adm-dev-002', name: 'WearWise Platform Admin', email: 'admin@wearwise.com', role: 'admin', status: 'active' };
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/auth/me')) return Promise.resolve({ ok: true, json: async () => admin });
      if (url.includes('/api/admin/overview')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            admin,
            metrics: {
              total_customers: 4,
              active_customers: 4,
              total_sellers: 3,
              pending_seller_applications: 1,
              approved_sellers: 2,
              suspended_sellers: 0,
              rejected_sellers: 0,
              total_products: 17,
              active_products: 17,
              total_orders: 0,
              simulated_order_volume: 0,
              actual_captured_revenue: 0,
              is_demo_payments_only: true,
            },
          }),
        });
      }
      if (url.includes('/api/admin/sellers')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            sellers: [
              { id: 'slr-pending', name: 'Pending Owner', owner_name: 'Pending Owner', email: 'pending.seller@wearwise.studio', store_name: 'Pending Atelier', status: 'pending', seller_approved: false, is_active: false },
            ],
            total: 1,
          }),
        });
      }
      if (url.includes('/api/admin/')) {
        return Promise.resolve({ ok: true, json: async () => [] });
      }
      return Promise.resolve({ ok: true, json: async () => ({ status: 'healthy' }) });
    }) as any;

    renderAt('/admin');
    await waitFor(() => {
      expect(screen.getByTestId('admin-portal-shell')).toBeTruthy();
      expect(screen.getByText('Pending Atelier')).toBeTruthy();
    });
    fireEvent.click(screen.getByTestId('admin-nav-sellers'));
    expect(screen.getByTestId('admin-seller-row-pending.seller@wearwise.studio')).toBeTruthy();
  });
});
