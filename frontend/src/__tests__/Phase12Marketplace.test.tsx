import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { StoreAuthProvider } from '../context/AuthContext';
import { BodyEngineAuthProvider } from '../context/BodyEngineAuthContext';
import Explore from '../pages/Explore';
import ProductDetailPage from '../pages/ProductDetailPage';
import ImageTryOnPage from '../pages/ImageTryOnPage';
import MerchantGarmentStudio from '../pages/MerchantGarmentStudio';

const SAMPLE_IMAGE_ONLY_READY = {
  id: 2,
  sku: 'TSH-WW-OVERSIZE-002',
  name: 'Cloud Oversized Shirt',
  category: 'Tops',
  price: 1199,
  colors: ['#d8ff3f', '#ffffff'],
  brand: 'WEARWISE EDIT',
  seller_name: 'WEARWISE EDIT',
  description: 'A relaxed oversized shirt.',
  available_sizes: ['S', 'M', 'L'],
  tryOnCapabilities: {
    mode: 'IMAGE_ONLY',
    sellerImageTryOnEnabled: true,
    sellerThreeDTryOnEnabled: false,
    vtonServiceConfigured: true,
    vtonServiceHealthy: true,
    imageTryOnEnabled: true,
    imageTryOnReady: true,
    threeDTryOnEnabled: false,
    imageDisabledReason: null,
    threeDDisabledReason: 'The seller has not enabled Interactive 3D Try-On for this item.',
  },
};

const SAMPLE_3D_ONLY_PRODUCT = {
  id: 10,
  sku: 'TSH-3D-ONLY-010',
  name: '3D Exclusive Knit Tee',
  category: 'Tops',
  price: 2499,
  colors: ['#151515'],
  brand: 'WEARWISE STUDIO',
  seller_name: 'WEARWISE STUDIO',
  description: 'Available strictly in 3D fitting.',
  available_sizes: ['S', 'M', 'L'],
  published_revision: 1,
  tryOnCapabilities: {
    mode: 'THREE_D_ONLY',
    sellerImageTryOnEnabled: false,
    sellerThreeDTryOnEnabled: true,
    vtonServiceConfigured: true,
    vtonServiceHealthy: true,
    imageTryOnEnabled: false,
    threeDTryOnEnabled: true,
    imageDisabledReason: 'The seller configured this item exclusively for Interactive 3D Try-On.',
    threeDDisabledReason: null,
  },
};

const SAMPLE_BOTH_PROVIDER_DOWN = {
  id: 1,
  sku: 'TSH-WW-CREW-001',
  name: 'Cherry Baby Tee',
  category: 'Tops',
  price: 799,
  colors: ['#ff3d9a', '#ffffff'],
  brand: 'WEARWISE EDIT',
  seller_name: 'WEARWISE EDIT',
  description: 'Dual-mode flagship tee.',
  available_sizes: ['S', 'M', 'L'],
  published_revision: 1,
  tryOnCapabilities: {
    mode: 'IMAGE_AND_THREE_D',
    sellerImageTryOnEnabled: true,
    sellerThreeDTryOnEnabled: true,
    vtonServiceConfigured: false,
    vtonServiceHealthy: false,
    imageTryOnEnabled: false,
    imageTryOnReady: false,
    threeDTryOnEnabled: true,
    threeDTryOnReady: true,
    imageDisabledReason: 'Image Try-On service is currently unavailable until an external AI try-on provider is connected.',
    threeDDisabledReason: null,
  },
};

describe('Phase 12.1 Dual-Mode Virtual Try-On Marketplace', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders Explore with clothing category tabs and capability badges', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/products')) {
        return Promise.resolve({
          ok: true,
          json: async () => [SAMPLE_BOTH_PROVIDER_DOWN, SAMPLE_IMAGE_ONLY_READY],
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
    }) as any;

    render(
      <MemoryRouter initialEntries={['/explore']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <Explore />
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cherry Baby Tee')).toBeTruthy();
    });
    for (const cat of ['All', 'Tops', 'Shirts', 'Trousers', 'Jeans', 'Skirts', 'Dresses', 'Jackets']) {
      expect(screen.getByTestId(`category-tab-${cat}`)).toBeTruthy();
    }
  });

  it('enforces separated seller + service capabilities on PDP across all three scenarios', async () => {
    // 1. IMAGE_ONLY with healthy VTON + empty reviews
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/reviews')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ sku: 'TSH-WW-OVERSIZE-002', review_count: 0, average_rating: null, reviews: [] }),
        });
      }
      if (url.includes('/api/products/sku/')) {
        return Promise.resolve({ ok: true, json: async () => SAMPLE_IMAGE_ONLY_READY });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
    }) as any;

    const { unmount } = render(
      <MemoryRouter initialEntries={['/product/TSH-WW-OVERSIZE-002']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <Routes>
              <Route path="/product/:sku" element={<ProductDetailPage />} />
            </Routes>
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('pdp-title').textContent).toBe('Cloud Oversized Shirt');
    });
    expect(screen.getByTestId('pdp-rating-summary').textContent).toContain('No customer reviews yet');
    expect(screen.getByTestId('pdp-reviews-empty')).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/AI Recommended For You|Recommended Products/i);

    fireEvent.click(screen.getByTestId('open-tryon-selector-btn'));
    expect((screen.getByTestId('tryon-mode-image-btn') as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId('tryon-mode-3d-btn') as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByTestId('three-d-tryon-disabled-reason').textContent).toContain('not enabled Interactive 3D');
    unmount();

    // 2. THREE_D_ONLY
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/reviews')) {
        return Promise.resolve({ ok: true, json: async () => ({ review_count: 0, average_rating: null, reviews: [] }) });
      }
      if (url.includes('/api/products/sku/')) {
        return Promise.resolve({ ok: true, json: async () => SAMPLE_3D_ONLY_PRODUCT });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
    }) as any;

    const u2 = render(
      <MemoryRouter initialEntries={['/product/TSH-3D-ONLY-010?openTryOn=1']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <Routes>
              <Route path="/product/:sku" element={<ProductDetailPage />} />
            </Routes>
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId('tryon-mode-selector')).toBeTruthy();
    });
    expect((screen.getByTestId('tryon-mode-image-btn') as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId('tryon-mode-3d-btn') as HTMLButtonElement).disabled).toBe(false);
    expect(screen.getByTestId('image-tryon-disabled-reason').textContent).toContain('exclusively for Interactive 3D');
    u2.unmount();

    // 3. IMAGE_AND_THREE_D when VTON service is unavailable: Image greyed out BEFORE entering broken flow, 3D active
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/reviews')) {
        return Promise.resolve({ ok: true, json: async () => ({ review_count: 0, average_rating: null, reviews: [] }) });
      }
      if (url.includes('/api/products/sku/')) {
        return Promise.resolve({ ok: true, json: async () => SAMPLE_BOTH_PROVIDER_DOWN });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
    }) as any;

    render(
      <MemoryRouter initialEntries={['/product/TSH-WW-CREW-001?openTryOn=1']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <Routes>
              <Route path="/product/:sku" element={<ProductDetailPage />} />
            </Routes>
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByTestId('tryon-mode-selector')).toBeTruthy();
    });
    expect((screen.getByTestId('tryon-mode-image-btn') as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId('tryon-mode-3d-btn') as HTMLButtonElement).disabled).toBe(false);
    expect(screen.getByTestId('image-tryon-disabled-reason').textContent).toContain('unavailable');
  });

  it('disables submission and shows honest banner on ImageTryOnPage when VTON provider is unavailable', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/try-on/vton/providers')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            available: false,
            configured: false,
            status: 'provider_unavailable',
            unavailable_reason: 'External VTON provider not configured.',
          }),
        });
      }
      if (url.includes('/api/products/sku/')) {
        return Promise.resolve({ ok: true, json: async () => SAMPLE_BOTH_PROVIDER_DOWN });
      }
      return Promise.resolve({ ok: true, json: async () => ({ items: [] }) });
    }) as any;

    render(
      <MemoryRouter initialEntries={['/image-try-on?sku=TSH-WW-CREW-001&size=M']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <ImageTryOnPage />
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('image-tryon-blocked-banner')).toBeTruthy();
    });
    expect(screen.getByTestId('image-tryon-blocked-banner').textContent).toContain('unavailable');
    expect(screen.queryByTestId('vton-file-input')).toBeNull();
  });

  it('shows Virtual Try-On Options in Seller Studio and lets IMAGE_ONLY skip 3D setup', () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }) as any;

    render(
      <MemoryRouter initialEntries={['/merchant-studio']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <MerchantGarmentStudio />
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByTestId('seller-tryon-options')).toBeTruthy();
    expect(screen.getByTestId('seller-mode-IMAGE_ONLY')).toBeTruthy();
    expect(screen.getByTestId('seller-mode-THREE_D_ONLY')).toBeTruthy();
    expect(screen.getByTestId('seller-mode-IMAGE_AND_THREE_D')).toBeTruthy();

    fireEvent.click(screen.getByTestId('seller-mode-IMAGE_ONLY'));
    expect(screen.getByTestId('seller-mode-IMAGE_ONLY').textContent).toContain('✓');
  });
});
