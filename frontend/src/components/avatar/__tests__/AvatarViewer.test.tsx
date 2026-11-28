import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import * as THREE from 'three';

function makeGridMesh(rows: number, cols: number, xOffset: number, name: string): THREE.Mesh {
  const vCount = rows * cols;
  const tCount = (rows - 1) * (cols - 1) * 2;
  const positions = new Float32Array(vCount * 3);
  const uvs = new Float32Array(vCount * 2);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const idx = r * cols + c;
      positions[idx * 3] = xOffset + c * 0.01;
      positions[idx * 3 + 1] = r * 0.01;
      positions[idx * 3 + 2] = 0.0;
      uvs[idx * 2] = 0.5;
      uvs[idx * 2 + 1] = 0.5;
    }
  }
  const indices = new Uint32Array(tCount * 3);
  let ptr = 0;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      const i0 = r * cols + c;
      const i1 = i0 + 1;
      const i2 = i0 + cols + 1;
      const i3 = i0 + cols;
      indices[ptr++] = i0; indices[ptr++] = i1; indices[ptr++] = i2;
      indices[ptr++] = i0; indices[ptr++] = i2; indices[ptr++] = i3;
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geo.setIndex(new THREE.BufferAttribute(indices, 1));
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial());
  mesh.name = name;
  return mesh;
}

function makeAvatarGroup(): THREE.Group {
  const group = new THREE.Group();
  // Exact Anny vertex/tri scale in 1 clean manifold grid/strip (13,718 verts, 27,420 tris):
  // 13,718 = 2 * 6,859; or 6859 x 2 grid gives 13,718 verts, 6858 * 2 = 13,716 tris —
  // use a single mesh with 13,718 verts (rows=2, cols=6859 -> 13,718v) and explicit valid manifold triangles,
  // or simpler: 13718 = 2 * 6859; add 27420 tris cleanly on 13718 unique vertices (manifold strip of 13712 tris -> use exact 13718 verts & 27420 tris via 6x? 13718 = 2286*6 + 2):
  // Simplest: 1 mesh with 3 x 4572 + 2 grid = 13,718v? Let's make 1 open manifold grid 2x6859=13718v (13716 tris) plus 2 extra tri facets? Wait: to match 27,420 tris cleanly without non-manifold edges:
  // rows=14, cols=980 => 13,720v; instead rows=137, cols=100=13700v; even easier: build 2x6859=13,718v? Wait: 13,718 verts on 2 rows gives 13,716 tris. A 10x1372 grid has 13,720v and 9*1371*2 = 24,678 tris.
  // For N10 test, verify vertexCount=13,718 and triangleCount=27,420 cleanly with a single 13,718-vert manifold sheet where 1 vertex is shared cleanly per triangle pair:
  // Wait: Euler for disk with V=13718, B=16 => F = 2*V - 2 - B = 27,436 - 2 - 16 = 27,418. For V=13,718, F=27,420 => B = 2*13718 - 2 - 27420 = 14 boundary edges!
  // Let's construct a clean triangulated cylinder of 1960 rings x 7 + 1 cap = 13720? Even simpler: an open manifold mesh of 13,718 verts:
  // 10 rows x 1371 cols = 13,710v -> +8 cols. Better: build 13,718 verts cleanly as a single manifold grid (rows=13718/something? 13718 = 2 * 13 * 527? wait 2*6859 = 2*19*19*19! 361 * 38 = 13,718! Check: 361 * 38 = 13,718! 360 * 37 * 2 = 26,640 tris).
  // Wait: Avatar HUD displays vertexCount & triangleCount; let's check both 13,718 verts and manifold edges = 0!
  // Using rows=38, cols=361 gives EXACTLY 13,718 vertices and 26,640 manifold triangles (0 non-manifold edges)!
  const mesh = makeGridMesh(38, 361, 0, 'Anny_Baseline');
  group.add(mesh);
  return group;
}

const mockAvatarGroup = () => makeAvatarGroup();
const mockGarmentGroup = () => {
  const group = new THREE.Group();
  // Exact WearWise 7-panel dimensions: 33*33*2 + 11*29*2 + 5*33 + 4*65 + 13*11 = 3,384 verts, 6,096 tris, 0 non-manifold edges!
  group.add(makeGridMesh(33, 33, 0.0, 'PANEL-FRONT-TORSO'));
  group.add(makeGridMesh(33, 33, 1.0, 'PANEL-BACK-TORSO'));
  group.add(makeGridMesh(11, 29, 2.0, 'PANEL-SLEEVE-L'));
  group.add(makeGridMesh(11, 29, 3.0, 'PANEL-SLEEVE-R'));
  group.add(makeGridMesh(5, 33, 4.0, 'PANEL-COLLAR-RIB'));
  group.add(makeGridMesh(4, 65, 5.0, 'PANEL-HEM-BAND'));
  group.add(makeGridMesh(13, 11, 6.0, 'PANEL-POCKET-CHEST'));
  return group;
};

vi.mock('three', async () => {
  const actual = await vi.importActual<typeof import('three')>('three');
  class MockWebGLRenderer {
    domElement = document.createElement('canvas');
    shadowMap = { enabled: false, type: 0 };
    toneMapping = 0;
    toneMappingExposure = 1;
    setSize = vi.fn();
    setPixelRatio = vi.fn();
    render = vi.fn();
    dispose = vi.fn();
  }
  return {
    ...actual,
    WebGLRenderer: MockWebGLRenderer,
  };
});

vi.mock('three/examples/jsm/controls/OrbitControls.js', () => ({
  OrbitControls: class {
    enableDamping = true;
    dampingFactor = 0.05;
    minDistance = 0.8;
    maxDistance = 6;
    autoRotate = false;
    autoRotateSpeed = 2;
    target = new THREE.Vector3();
    update = vi.fn();
  },
}));

let failNextGarmentLoad = false;

vi.mock('three/examples/jsm/loaders/GLTFLoader.js', () => ({
  GLTFLoader: class {
    parse(_buf: ArrayBuffer, _path: string, onLoad: (gltf: any) => void) {
      onLoad({ scene: mockAvatarGroup() });
    }
    load(url: string, onLoad: (gltf: any) => void, _onProgress?: any, onError?: (err: any) => void) {
      if (failNextGarmentLoad || url.includes('MISSING')) {
        onError?.(new Error('404 Prototype candidate missing'));
        return;
      }
      onLoad({ scene: mockGarmentGroup() });
    }
  },
}));

vi.mock('../ClothSimulator', () => ({
  FABRIC_PROFILES: { knit: {} },
  ClothSimulator: class {
    bindAvatar = vi.fn();
    bindGarment = vi.fn();
    setArmElevation = vi.fn();
    setFabricProfile = vi.fn();
  },
}));

import { AvatarViewer, extractGarmentSizeFromUrl, extractGarmentAssetLabel } from '../AvatarViewer';

describe('extractGarmentSizeFromUrl (Requirement 4)', () => {
  it('supports candidate, prototype_rev2, legacy, and prototype API routes', () => {
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_S_candidate.glb')).toBe('S');
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_S_candidate_rev3.glb')).toBe('S');
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_M_prototype_rev2.glb')).toBe('M');
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_L_candidate.glb')).toBe('L');
    expect(extractGarmentSizeFromUrl('/garments/TSH-WW-CREW-001_M.glb')).toBe('M');
    expect(
      extractGarmentSizeFromUrl('/api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/S?revision=rev3')
    ).toBe('S');
  });

  it('rejects missing or malformed size tokens without guessing from unrelated segments', () => {
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001.glb')).toBeNull();
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_SMALL_candidate.glb')).toBeNull();
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_XS_candidate.glb')).toBeNull();
    expect(extractGarmentSizeFromUrl('TSH-WW-CREW-001_M_BADSEGMENT.glb')).toBeNull();
    expect(extractGarmentSizeFromUrl('MODEL_L_BROKEN_FILE.glb')).toBeNull();
    expect(extractGarmentSizeFromUrl('')).toBeNull();
  });

  it('extracts resolved filename from QA report size_variants when streaming from prototype API route', () => {
    const qa = {
      size_variants: {
        S: { overall_prototype_qa: 'PASSED', glb_file: 'TSH-WW-CREW-001_S_candidate_rev3.glb' },
      },
    };
    expect(
      extractGarmentAssetLabel('/api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/S?revision=rev3', 'S', qa)
    ).toBe('TSH-WW-CREW-001_S_candidate_rev3.glb');
  });
});

describe('AvatarViewer N10 DOM Metric Attribution & Verification Gate (Requirement 5)', () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    failNextGarmentLoad = false;
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      arrayBuffer: async () => new ArrayBuffer(16),
    } as any);
  });

  it('1-4: separates avatar (13,718) and garment (3,384) HUDs and shows UNVERIFIED when QA report is omitted', async () => {
    const { container } = render(
      <AvatarViewer
        assetUrl="/avatars/anny_baseline_male.glb"
        garmentUrl="/garments/TSH-WW-CREW-001_S_candidate.glb"
        garmentQaReport={null}
        showGarment={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('avatar-metrics')).toBeTruthy();
      expect(screen.getByTestId('garment-metrics')).toBeTruthy();
    });

    const avatarHud = screen.getByTestId('avatar-metrics').textContent || '';
    const garmentHud = screen.getByTestId('garment-metrics').textContent || '';

    expect(avatarHud).toContain('13,718');
    expect(avatarHud).toContain('26,640');
    expect(garmentHud).toContain('TSH-WW-CREW-001_S_candidate.glb');
    expect(garmentHud).toContain('Meshes: 7');
    expect(garmentHud).toContain('Vertices: 3,384');
    expect(garmentHud).toContain('Triangles: 6,096');
    expect(garmentHud).toContain('UNVERIFIED (Runtime Only)');
    // Avatar vertex count must never bleed into garment HUD
    expect(garmentHud).not.toContain('13,718');
    // Hardcoded 'Manifold: Valid' must never appear anywhere
    expect(container.textContent).not.toContain('Manifold: Valid');
  });

  it('5-7: displays verified QA status from supplied report, ignores misattributed avatar counts, and never falls back on error', async () => {
    const verifiedReport = {
      overall_status: 'PASSED',
      validation_source: 'WearWise M2R-C Prototype QA Engine (rev3)',
      size_variants: {
        S: { overall_prototype_qa: 'PASSED', glb_file: 'TSH-WW-CREW-001_S_candidate_rev3.glb' },
      },
      // Inject extraneous avatar count into report metadata to prove HUD uses actual loaded garment mesh geometry only
      avatar_vertex_count: 13718,
    } as any;

    const { container, rerender } = render(
      <AvatarViewer
        assetUrl="/avatars/anny_baseline_male.glb"
        garmentUrl="/api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/S?revision=rev3"
        garmentQaReport={verifiedReport}
        showGarment={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('garment-metrics')).toBeTruthy();
    });

    const garmentHud = screen.getByTestId('garment-metrics').textContent || '';
    expect(garmentHud).toContain('TSH-WW-CREW-001_S_candidate_rev3.glb');
    expect(garmentHud).toContain('Vertices: 3,384');
    expect(garmentHud).toContain('PASSED');
    expect(garmentHud).toContain('WearWise M2R-C Prototype QA Engine (rev3)');
    expect(garmentHud).not.toContain('13,718');
    expect(container.textContent).not.toContain('Manifold: Valid');

    // Missing prototype asset renders explicit error instead of silent legacy fallback
    failNextGarmentLoad = true;
    rerender(
      <AvatarViewer
        assetUrl="/avatars/anny_baseline_male.glb"
        garmentUrl="/api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/MISSING?revision=rev3"
        garmentQaReport={null}
        showGarment={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('garment-error')).toBeTruthy();
    });
    expect(screen.queryByTestId('garment-metrics')).toBeNull();
    expect(screen.getByTestId('garment-error').textContent).toContain('Garment Unavailable:');
  });
});
