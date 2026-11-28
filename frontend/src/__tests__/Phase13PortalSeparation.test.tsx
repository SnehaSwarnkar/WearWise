import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import App from '../App';

function mockSessionFetch(activeUser: any = null, extraHandlers: (url: string, opts?: RequestInit) => any = () => null) {
  globalThis.fetch = vi.fn().mockImplementation((url: string, opts?: RequestInit) => {
    const custom = extraHandlers(url, opts);
    if (custom) return custom;
    if (url.includes('/api/auth/me')) {
      return activeUser
        ? Promise.resolve({ ok: true, json: async () => activeUser })
        : Promise.resolve({ ok: false, status: 401, json: async () => ({ detail: 'Authentication required' }) });
    }
    if (url.includes('/api/products')) {
      return Promise.resolve({ ok: true, json: async () => [] });
    }
    if (url.includes('/api/cart')) {
      return Promise.resolve({ ok: true, json: async () => ({ items: [], subtotal: 0, shipping: 0, total: 0 }) });
    }
    if (url.includes('/api/seller/dashboard')) {
      return Promise.resolve({
        ok: true,
        json: async () => ({
          seller: activeUser,
          metrics: { total_products: 3, published_products: 2, draft_products: 1, needs_attention: 1, orders_count: 4 },
          attention_products: [],
          recent_activity: [],
        }),
      });
    }
    if (url.includes('/health')) {
      return Promise.resolve({ ok: true, json: async () => ({ status: 'healthy' }) });
    }
    return Promise.resolve({ ok: true, json: async () => [] });
  }) as any;
}

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

describe('Phase 13 Shopper & Seller Portal Separation', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders /auth dual portal landing with exact descriptions', async () => {
    mockSessionFetch(null);
    renderAt('/auth');

    expect(await screen.findByText(/Discover fashion, find your fit and shop with WearWise\./i)).toBeTruthy();
    expect(screen.getByText(/Manage your products, publish garments and grow your store\./i)).toBeTruthy();
    expect(screen.getByTestId('enter-shopper-login')).toBeTruthy();
    expect(screen.getByTestId('enter-seller-login')).toBeTruthy();
  });

  it('shows portal mismatch error messages on Shopper Login and Seller Login', async () => {
    mockSessionFetch(null, (url) => {
      if (url.includes('/api/auth/seller/login')) {
        return Promise.resolve({
          ok: false,
          status: 403,
          json: async () => ({
            detail: 'This account is registered as a shopper. Please use Shopper Login or contact WearWise about seller access.',
          }),
        });
      }
      if (url.includes('/api/auth/login')) {
        return Promise.resolve({
          ok: false,
          status: 403,
          json: async () => ({ detail: 'This is a seller account. Please use Seller Login.' }),
        });
      }
      return null;
    });

    const { unmount } = renderAt('/login');
    fireEvent.change(await screen.findByPlaceholderText('shopper@example.com'), { target: { value: 'seller@wearwise.studio' } });
    fireEvent.change(screen.getByPlaceholderText('Your password'), { target: { value: 'Pass#123' } });
    fireEvent.click(screen.getByTestId('shopper-login-submit'));
    await waitFor(() => {
      expect(screen.getByTestId('shopper-login-error').textContent).toContain('This is a seller account. Please use Seller Login.');
    });
    unmount();

    renderAt('/seller/login');
    fireEvent.change(await screen.findByPlaceholderText('seller@yourbrand.studio'), { target: { value: 'shopper@wearwise.test' } });
    fireEvent.change(screen.getByPlaceholderText('Seller password'), { target: { value: 'Pass#123' } });
    fireEvent.click(screen.getByTestId('seller-login-submit'));
    await waitFor(() => {
      expect(screen.getByTestId('seller-login-error').textContent).toContain('This account is registered as a shopper');
    });
  });

  it('blocks unauthenticated users from protected portals and hides merchant UI from shopper header', async () => {
    mockSessionFetch(null);
    const { unmount } = renderAt('/seller/dashboard');
    await waitFor(() => {
      expect(screen.getByTestId('seller-login-card')).toBeTruthy();
    });
    unmount();

    renderAt('/explore');
    await waitFor(() => {
      expect(screen.getByTestId('header-signin-cta')).toBeTruthy();
    });
    expect(screen.queryByText('MERCHANT')).toBeNull();
    expect(screen.queryByText('Digital Garment Studio')).toBeNull();
  });

  it('denies shopper access to seller pages and denies seller access to shopper-only pages', async () => {
    const shopper = { id: 'u1', name: 'Riya Shopper', email: 'shopper@wearwise.test', role: 'shopper', status: 'active' };
    mockSessionFetch(shopper);
    const { unmount } = renderAt('/seller/dashboard');
    await waitFor(() => {
      expect(screen.getByTestId('seller-access-denied')).toBeTruthy();
    });
    unmount();

    const seller = {
      id: 's1',
      name: 'Studio Lead',
      email: 'seller@wearwise.studio',
      role: 'seller',
      status: 'active',
      seller_approved: true,
      brand_id: 'e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e',
      store_name: 'WearWise Official Studio',
    };
    mockSessionFetch(seller);
    const { unmount: unmount2 } = renderAt('/wardrobe');
    await waitFor(() => {
      expect(screen.getByTestId('shopper-access-denied')).toBeTruthy();
    });
    unmount2();

    renderAt('/seller/dashboard');
    await waitFor(() => {
      expect(screen.getByTestId('seller-portal-shell')).toBeTruthy();
      expect(screen.getByTestId('seller-portal-nav')).toBeTruthy();
    });
    expect(screen.queryByText('Wardrobe')).toBeNull();
    expect(screen.queryByText('AI Stylist')).toBeNull();
  });
});
