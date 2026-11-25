import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StoreAuthProvider } from '../../context/AuthContext';
import { BodyEngineAuthProvider } from '../../context/BodyEngineAuthContext';
import ExperimentalTryOnPage from '../ExperimentalTryOnPage';
import MerchantGarmentStudio from '../../pages/MerchantGarmentStudio';

// Mock Three.js WebGLRenderer & OrbitControls in JSDOM
vi.mock('three', async () => {
  const actual = await vi.importActual<typeof import('three')>('three');
  return {
    ...actual,
    WebGLRenderer: class {
      toneMapping = 0;
      domElement = document.createElement('canvas');
      setSize = vi.fn();
      setPixelRatio = vi.fn();
      render = vi.fn();
      dispose = vi.fn();
    },
  };
});

vi.mock('three/examples/jsm/controls/OrbitControls.js', () => ({
  OrbitControls: class {
    target = { set: vi.fn() };
    update = vi.fn();
    dispose = vi.fn();
  },
}));

vi.mock('three/examples/jsm/loaders/GLTFLoader.js', () => ({
  GLTFLoader: class {
    load = vi.fn();
  },
}));

describe('Phase 11.5 Simplified Shopper & Seller UX', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        garment_id: 'g-1',
        sku: 'TSH-WW-PHASE11-ACCEPTANCE-001',
        name: 'Phase 11 Acceptance Crew Tee',
        status: 'published',
        revision: 1,
        size: 'M',
        available_sizes: ['S', 'M', 'L'],
        asset_url: '/api/v1/merchant/garments/g-1/revisions/1/assets/M',
        fabric_profile: { id: 'cotton_waffle_knit_240gsm', name: 'Cotton Waffle Knit (240 GSM)', gsm: 240 },
        measurements: { chest_circumference_cm: 104, waist_circumference_cm: 100, shoulder_width_cm: 46 },
      }),
    }) as any;
  });

  it('renders shopper Try-On with clear size recommendation and zero engineering jargon', async () => {
    render(
      <MemoryRouter initialEntries={['/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <ExperimentalTryOnPage />
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('recommended-size').textContent).toBe('L');
    });
    expect(screen.getByTestId('expected-fit').textContent).toBe('Snug fit');

    const bodyText = document.body.textContent || '';
    expect(bodyText).toContain('Your Recommended Size');
    expect(bodyText).toContain('Why this size?');
    expect(bodyText).toContain('Compare Sizes');
    expect(bodyText).not.toMatch(/web_worker|SHA-256|Developer Diagnostics|FPS|Welded Particles/i);
  });

  it('renders Seller Product Studio with simplified stage labels and status guidance', () => {
    render(
      <MemoryRouter initialEntries={['/merchant-studio']}>
        <BodyEngineAuthProvider>
          <StoreAuthProvider>
            <MerchantGarmentStudio />
          </StoreAuthProvider>
        </BodyEngineAuthProvider>
      </MemoryRouter>
    );

    const bodyText = document.body.textContent || '';
    expect(bodyText).toContain('Seller Product Studio');
    expect(bodyText).toContain('Add product details');
    expect(bodyText).toContain('Upload product photos');
    expect(bodyText).toContain('Preview & publish');
    expect(screen.getByTestId('seller-status-summary')).toBeTruthy();
    expect(bodyText).not.toContain('RUNNING 13-STAGE PIPELINE');
  });
});
