import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import Header from '../pages/Header';
import { addToCart } from '../api/cart';
import { fetchProductBySku } from '../api/products';
import { ARTICULATED_POSES } from './ArticulatedPoseLibrary';
import { WorkerClothClient } from './WorkerClothClient';

const BODY_ENGINE_BASE = 'http://127.0.0.1:8000';

interface AvatarOption {
  id: string;
  label: string;
  glbUrl: string;
  statureCm: number;
  chestCm: number;
  waistCm: number;
  shoulderCm: number;
}

// Calibrated Anny profiles from Phase 11.5 closed-loop validation
const STAGING_AVATAR_PROFILES: AvatarOption[] = [
  {
    id: 'PROFILE_B_ATHLETIC_MALE',
    label: 'Athletic Build (178.5 cm · Chest 100 cm)',
    glbUrl: '/experimental_phase11/PROFILE_B_ATHLETIC_MALE.glb',
    statureCm: 178.5,
    chestCm: 100.16,
    waistCm: 81.66,
    shoulderCm: 42.75,
  },
  {
    id: 'PROFILE_A_SLIM_MALE',
    label: 'Slim Build (172.0 cm · Chest 91.5 cm)',
    glbUrl: '/experimental_phase11/PROFILE_A_SLIM_MALE.glb',
    statureCm: 172.0,
    chestCm: 91.49,
    waistCm: 74.84,
    shoulderCm: 40.02,
  },
  {
    id: 'PROFILE_C_BROAD_MALE',
    label: 'Broad Build (184.0 cm · Chest 110 cm)',
    glbUrl: '/experimental_phase11/PROFILE_C_BROAD_MALE.glb',
    statureCm: 184.0,
    chestCm: 109.96,
    waistCm: 90.59,
    shoulderCm: 45.59,
  },
  {
    id: 'PROFILE_D_PETITE_FEMININE',
    label: 'Petite Build (161.0 cm · Chest 86 cm)',
    glbUrl: '/experimental_phase11/PROFILE_D_PETITE_FEMININE.glb',
    statureCm: 161.0,
    chestCm: 86.2,
    waistCm: 67.86,
    shoulderCm: 37.3,
  },
  {
    id: 'PROFILE_E_TALL_NEUTRAL',
    label: 'Tall Neutral Build (180.0 cm · Chest 97 cm)',
    glbUrl: '/experimental_phase11/PROFILE_E_TALL_NEUTRAL.glb',
    statureCm: 180.0,
    chestCm: 97.06,
    waistCm: 79.4,
    shoulderCm: 41.57,
  },
];

interface ResolvedGarmentAsset {
  garment_id: string;
  sku: string;
  name: string;
  status: string;
  revision: number;
  size: string;
  available_sizes: string[];
  asset_url: string;
  fabric_profile?: {
    id?: string;
    name?: string;
    gsm?: number;
  };
  measurements?: Record<string, any>;
  all_size_measurements?: Record<string, Record<string, any>>;
}

const CONSUMER_POSES = [
  { id: 'P0', label: 'Standing Natural' },
  { id: 'P1', label: 'Arms Raised Slightly' },
  { id: 'P2', label: 'Arms Out (T-Pose)' },
  { id: 'P3', label: 'Arms Overhead' },
  { id: 'P6', label: 'Elbows Bent' },
  { id: 'P9', label: 'Leaning Forward' },
];

const DEFAULT_SIZE_CHEST: Record<string, number> = { S: 96, M: 104, L: 112 };
const DEFAULT_SIZE_WAIST: Record<string, number> = { S: 92, M: 100, L: 108 };
const DEFAULT_SIZE_SHOULDER: Record<string, number> = { S: 43, M: 46, L: 49 };

function mapFabricToSolverId(backendFabricId?: string): string {
  if (!backendFabricId) return 'waffle_knit_240';
  if (backendFabricId.includes('poplin')) return 'rigid_poplin_140';
  return 'waffle_knit_240';
}

type FitLabel = 'Too tight' | 'Snug fit' | 'Regular fit' | 'Relaxed fit' | 'Too loose' | 'Recommendation unavailable';

function classifyFit(chestEase: number, shoulderEase: number): FitLabel {
  if (chestEase < 0 || shoulderEase < -1.5) return 'Too tight';
  if (chestEase < 5) return 'Snug fit';
  if (chestEase <= 12) return 'Regular fit';
  if (chestEase <= 20) return 'Relaxed fit';
  return 'Too loose';
}

function describeFitReason(size: string, fit: FitLabel, chestEase: number): string {
  if (fit === 'Regular fit') {
    return `Size ${size} is closest to your body measurements and should provide a comfortable everyday fit.`;
  }
  if (fit === 'Snug fit') {
    return `Size ${size} sits closer to the chest and shoulders for a tailored feel.`;
  }
  if (fit === 'Relaxed fit') {
    return `Size ${size} gives extra room around the chest (+${chestEase.toFixed(0)} cm) for a looser silhouette.`;
  }
  if (fit === 'Too tight') {
    return `Size ${size} may feel tight across the chest or shoulders. Consider sizing up.`;
  }
  if (fit === 'Too loose') {
    return `Size ${size} will drape noticeably oversized on your frame. Consider sizing down.`;
  }
  return 'Your size recommendation is currently unavailable. Please check your measurements or choose using the size guide.';
}

export default function ExperimentalTryOnPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sku = searchParams.get('sku') || 'TSH-WW-PHASE11-ACCEPTANCE-001';
  const requestedRev = searchParams.get('revision');
  const selectedColor = searchParams.get('color') || 'Coral Pink';
  const [selectedSize, setSelectedSize] = useState<string>(searchParams.get('size') || 'M');
  const [selectedAvatarId, setSelectedAvatarId] = useState<string>(STAGING_AVATAR_PROFILES[0].id);

  const [garmentMeta, setGarmentMeta] = useState<ResolvedGarmentAsset | null>(null);
  const [catalogProduct, setCatalogProduct] = useState<any>(null);
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [activePoseId, setActivePoseId] = useState<string>('P0');
  const [paused, setPaused] = useState<boolean>(false);
  const [cartMsg, setCartMsg] = useState<string | null>(null);
  const [addingToCart, setAddingToCart] = useState<boolean>(false);

  const mountRef = useRef<HTMLDivElement | null>(null);
  const clientRef = useRef<WorkerClothClient | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const pausedRef = useRef<boolean>(false);

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  const activeAvatar = useMemo(
    () => STAGING_AVATAR_PROFILES.find((a) => a.id === selectedAvatarId) || STAGING_AVATAR_PROFILES[0],
    [selectedAvatarId]
  );

  const resolveAndLoad = useCallback(async () => {
    setLoadState('loading');
    setErrorMsg(null);
    setCartMsg(null);

    try {
      const prod = await fetchProductBySku(sku).catch(() => null);
      setCatalogProduct(prod);
      if (prod?.tryOnCapabilities && prod.tryOnCapabilities.threeDTryOnEnabled === false) {
        setGarmentMeta(null);
        setLoadState('error');
        setErrorMsg(
          prod.tryOnCapabilities.threeDDisabledReason ||
            'Interactive 3D Try-On is disabled by the seller for this item.'
        );
        return;
      }

      const revQuery = requestedRev ? `&revision=${encodeURIComponent(requestedRev)}` : '';
      const metaUrl = `${BODY_ENGINE_BASE}/api/v1/merchant/garments/${encodeURIComponent(sku)}/shopper-asset?size=${encodeURIComponent(selectedSize)}${revQuery}`;
      const res = await fetch(metaUrl, { cache: 'no-store' });
      if (!res.ok) {
        throw new Error('This garment or size is currently unavailable for try-on.');
      }
      const meta: ResolvedGarmentAsset = await res.json();
      setGarmentMeta(meta);
      setLoadState('ready');
    } catch {
      setGarmentMeta(null);
      setLoadState('error');
      setErrorMsg('We could not load the 3D preview for this garment and size right now. Please try another size or return to the catalog.');
    }
  }, [sku, selectedSize, requestedRev]);

  useEffect(() => {
    resolveAndLoad();
  }, [resolveAndLoad]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container || loadState !== 'ready' || !garmentMeta) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#5a0b23');

    const width = container.clientWidth || 760;
    const height = 560;
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.05, 50);
    camera.position.set(0, 1.15, 2.05);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1.05, -0.05);
    controls.update();
    controlsRef.current = controls;

    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(1.5, 2.5, 2.5);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xffd6e7, 0.65);
    fillLight.position.set(-1.5, 1.0, -1.5);
    scene.add(fillLight);

    const client = new WorkerClothClient();
    clientRef.current = client;

    const loader = new GLTFLoader();
    const garmentAssetFullUrl =
      garmentMeta.asset_url.startsWith('http') || garmentMeta.asset_url.startsWith('/garments/')
        ? garmentMeta.asset_url
        : `${BODY_ENGINE_BASE}${garmentMeta.asset_url}`;

    let disposed = false;
    Promise.all([
      new Promise<any>((res, rej) => loader.load(activeAvatar.glbUrl, res, undefined, rej)),
      new Promise<any>((res, rej) => loader.load(garmentAssetFullUrl, res, undefined, rej)),
    ])
      .then(async ([avatarGltf, garmentGltf]) => {
        if (disposed) return;
        const avatarScene = avatarGltf.scene as THREE.Group;
        const garmentScene = garmentGltf.scene as THREE.Group;
        scene.add(avatarScene);
        scene.add(garmentScene);

        avatarScene.updateMatrixWorld(true);
        let neckBone: THREE.Object3D | null = null;
        avatarScene.traverse((o) => {
          if (o.name === 'neck01') neckBone = o;
        });
        if (neckBone) {
          const avNeck = new THREE.Vector3();
          (neckBone as THREE.Object3D).getWorldPosition(avNeck);

          const collarBox = new THREE.Box3();
          let hasCollar = false;
          garmentScene.traverse((o) => {
            const m = o as THREE.Mesh;
            if (m.isMesh && m.name.includes('COLLAR')) {
              m.geometry.computeBoundingBox();
              if (m.geometry.boundingBox) {
                collarBox.union(m.geometry.boundingBox);
                hasCollar = true;
              }
            }
          });
          if (hasCollar) {
            const gCollar = new THREE.Vector3();
            collarBox.getCenter(gCollar);
            const dx = avNeck.x - gCollar.x;
            const dy = avNeck.y - gCollar.y - 0.015;
            const dz = avNeck.z - gCollar.z + 0.025;
            garmentScene.traverse((o) => {
              const m = o as THREE.Mesh;
              if (m.isMesh && m.geometry.attributes.position) {
                m.geometry.translate(dx, dy, dz);
              }
            });
          }
        }

        await client.init(avatarScene, garmentScene);
        client.setFabric(mapFabricToSolverId(garmentMeta.fabric_profile?.id));
        const poseObj = ARTICULATED_POSES.find((p) => p.id === activePoseId);
        if (poseObj) client.setTargetPose(poseObj.state);
      })
      .catch(() => {
        if (disposed) return;
        setLoadState('error');
        setErrorMsg('Unable to display the 3D garment right now. Please refresh or choose another size.');
      });

    let rafId = 0;
    let lastTime = performance.now();
    const animate = (now: number) => {
      const dt = Math.min(0.033, Math.max(0.001, (now - lastTime) / 1000));
      lastTime = now;

      if (!pausedRef.current) {
        client.step(dt);
      }
      controls.update();
      renderer.render(scene, camera);
      rafId = requestAnimationFrame(animate);
    };
    rafId = requestAnimationFrame(animate);

    return () => {
      disposed = true;
      cancelAnimationFrame(rafId);
      client.dispose();
      controls.dispose();
      renderer.dispose();
    };
  }, [loadState, garmentMeta, activeAvatar]);

  const handlePoseSelect = (pid: string) => {
    setActivePoseId(pid);
    const p = ARTICULATED_POSES.find((x) => x.id === pid);
    if (p && clientRef.current) {
      clientRef.current.setTargetPose(p.state);
    }
  };

  const handleResetPose = () => {
    setActivePoseId('P0');
    clientRef.current?.reset();
  };

  const handleResetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 1.15, 2.05);
      controlsRef.current.target.set(0, 1.05, -0.05);
      controlsRef.current.update();
    }
  };

  const handleSizeChange = (sz: string) => {
    setSelectedSize(sz);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('size', sz);
      return next;
    });
  };

  const handleAddToCart = async () => {
    if (!garmentMeta || addingToCart) return;
    setAddingToCart(true);
    setCartMsg(null);
    try {
      await addToCart({
        id: catalogProduct?.id || 1,
        sku: garmentMeta.sku,
        published_revision: garmentMeta.revision,
        name: garmentMeta.name,
        price: catalogProduct?.price || 2999,
        size: selectedSize,
        quantity: 1,
        image: catalogProduct?.image || undefined,
        brand: catalogProduct?.seller_name || catalogProduct?.brand || 'WEARWISE EDIT',
        color: selectedColor,
      });
      setCartMsg(`Added ${garmentMeta.name} (Size ${selectedSize}) to your bag.`);
    } catch {
      setCartMsg('We could not add this item to your bag right now. Please try again.');
    } finally {
      setAddingToCart(false);
    }
  };

  // Compute shopper-friendly size recommendation & per-size comparison
  const fitGuidance = useMemo(() => {
    const sizes = garmentMeta?.available_sizes?.length ? garmentMeta.available_sizes : ['S', 'M', 'L'];
    const allM = garmentMeta?.all_size_measurements || {};
    const getDims = (sz: string) => {
      const m = allM[sz] || (sz === selectedSize ? garmentMeta?.measurements : null) || {};
      return {
        chest: Number(m.chest_circumference_cm ?? m.chest_cm ?? DEFAULT_SIZE_CHEST[sz] ?? 104),
        waist: Number(m.waist_circumference_cm ?? m.waist_cm ?? DEFAULT_SIZE_WAIST[sz] ?? 100),
        shoulder: Number(m.shoulder_width_cm ?? m.shoulder_cm ?? DEFAULT_SIZE_SHOULDER[sz] ?? 46),
      };
    };

    const comparisons = sizes.map((sz) => {
      const d = getDims(sz);
      const chestEase = Number((d.chest - activeAvatar.chestCm).toFixed(1));
      const shoulderEase = Number((d.shoulder - activeAvatar.shoulderCm).toFixed(1));
      const fit = classifyFit(chestEase, shoulderEase);
      return { size: sz, chestEase, shoulderEase, fit, dims: d };
    });

    const regularMatch = comparisons.find((c) => c.fit === 'Regular fit');
    const snugMatch = comparisons.find((c) => c.fit === 'Snug fit');
    const relaxedMatch = comparisons.find((c) => c.fit === 'Relaxed fit');
    const recommended = regularMatch || snugMatch || relaxedMatch || null;
    const currentComp = comparisons.find((c) => c.size === selectedSize) || comparisons[0];

    return {
      recommendedSize: recommended?.size || null,
      expectedFit: currentComp?.fit || 'Recommendation unavailable',
      reason: recommended
        ? describeFitReason(selectedSize, currentComp.fit, currentComp.chestEase)
        : 'Your size recommendation is currently unavailable. Please check your measurements or choose using the size guide.',
      comparisons,
      selectedDims: currentComp.dims,
    };
  }, [garmentMeta, activeAvatar, selectedSize]);

  return (
    <div style={{ minHeight: '100vh', background: '#FFF8F1', color: '#151515' }}>
      <Header />
      <main style={{ maxWidth: '1260px', margin: '0 auto', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: 800, letterSpacing: '0.8px', color: '#FF3D9A', textTransform: 'uppercase' }}>
              Virtual Fitting Room
            </span>
            <h1 style={{ fontSize: '28px', fontWeight: 900, margin: '4px 0' }}>
              {catalogProduct?.name || garmentMeta?.name || 'Boxy Crew Tee'}
            </h1>
            <p style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#151515' }}>
              ₹{Number(catalogProduct?.price || 2999).toLocaleString('en-IN')} · Size {selectedSize} · {garmentMeta?.fabric_profile?.name || 'Cotton Waffle Knit (240 GSM)'}
            </p>
            <div style={{ marginTop: '6px' }}>
              <Link to={`/product/${encodeURIComponent(sku)}`} style={{ fontSize: '12px', fontWeight: 800, color: '#151515', textDecoration: 'underline' }}>
                ← Back to Product Details
              </Link>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <Link
              to="/cart"
              data-testid="view-cart-link"
              style={{ padding: '10px 16px', borderRadius: '10px', border: '2px solid #151515', fontWeight: 800, fontSize: '13px', textDecoration: 'none', color: '#151515', background: '#fff' }}
            >
              View Bag
            </Link>
            <button
              type="button"
              data-testid="add-to-cart-btn"
              disabled={loadState !== 'ready' || addingToCart}
              onClick={handleAddToCart}
              style={{
                padding: '10px 20px',
                borderRadius: '10px',
                border: '2px solid #151515',
                fontWeight: 900,
                fontSize: '13px',
                background: '#D8FF3F',
                cursor: loadState === 'ready' && !addingToCart ? 'pointer' : 'not-allowed',
              }}
            >
              {addingToCart ? 'Adding...' : `Add Size ${selectedSize} to Bag`}
            </button>
          </div>
        </div>

        {cartMsg && (
          <div data-testid="cart-status-banner" style={{ padding: '12px 16px', background: '#ecfccb', border: '2px solid #151515', borderRadius: '10px', fontSize: '13px', fontWeight: 700, marginBottom: '14px' }}>
            {cartMsg}{' '}
            <Link to="/cart" style={{ color: '#151515', textDecoration: 'underline', marginLeft: '6px' }}>
              Go to Bag
            </Link>
          </div>
        )}

        {loadState === 'error' && (
          <div data-testid="tryon-error-banner" style={{ padding: '14px', background: '#fef2f2', border: '2px solid #dc2626', borderRadius: '10px', color: '#991b1b', marginBottom: '14px', fontSize: '13px', fontWeight: 700 }}>
            {errorMsg}
            <button type="button" onClick={resolveAndLoad} style={{ marginLeft: '12px', padding: '5px 12px', fontWeight: 800, borderRadius: '6px', border: '1px solid #991b1b', background: '#fff', cursor: 'pointer' }}>
              Try Again
            </button>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', alignItems: 'start' }}>
          {/* 3D Try-On Viewport */}
          <div style={{ position: 'relative', border: '2px solid #151515', borderRadius: '14px', overflow: 'hidden', background: '#5a0b23', minHeight: '560px' }}>
            {loadState === 'loading' && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800 }}>
                Preparing your 3D fit preview...
              </div>
            )}
            <div ref={mountRef} style={{ width: '100%', height: '560px' }} />
          </div>

          {/* Shopper Fit & Purchase Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Size Recommendation & Fit Card */}
            <div data-testid="fit-summary-card" style={{ background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Your Recommended Size</div>
                  <div data-testid="recommended-size" style={{ fontSize: '24px', fontWeight: 900, color: '#FF3D9A' }}>
                    {fitGuidance.recommendedSize || 'Unavailable'}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>Expected Fit (Size {selectedSize})</div>
                  <div data-testid="expected-fit" style={{ fontSize: '16px', fontWeight: 900 }}>
                    {fitGuidance.expectedFit}
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#334155', margin: '0 0 12px', lineHeight: 1.45 }}>
                <strong>Why this size?</strong> {fitGuidance.reason}
              </p>

              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '10px' }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#64748b', marginBottom: '6px', textTransform: 'uppercase' }}>Compare Sizes</div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {fitGuidance.comparisons.map((c) => (
                    <button
                      key={c.size}
                      type="button"
                      data-testid={`size-btn-${c.size}`}
                      onClick={() => handleSizeChange(c.size)}
                      style={{
                        flex: 1,
                        padding: '8px 6px',
                        borderRadius: '8px',
                        border: '2px solid #151515',
                        background: selectedSize === c.size ? '#FF3D9A' : '#FFF8F1',
                        color: selectedSize === c.size ? '#fff' : '#151515',
                        fontWeight: 800,
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      <div>Size {c.size}</div>
                      <div style={{ fontSize: '10.5px', fontWeight: 700, opacity: 0.9 }}>{c.fit}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Body Profile Selector */}
            <div style={{ background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '16px' }}>
              <label style={{ fontSize: '12px', fontWeight: 800, display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>
                Your Body Profile
              </label>
              <select
                data-testid="avatar-select"
                value={selectedAvatarId}
                onChange={(e) => setSelectedAvatarId(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '2px solid #151515', fontWeight: 700, fontSize: '13px', background: '#FFF8F1' }}
              >
                {STAGING_AVATAR_PROFILES.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#475569', marginTop: '8px' }}>
                <span>Your chest: <strong>{Math.round(activeAvatar.chestCm)} cm</strong></span>
                <span>Garment chest ({selectedSize}): <strong>{fitGuidance.selectedDims.chest} cm</strong></span>
              </div>
            </div>

            {/* Simple Pose & View Controls */}
            <div style={{ background: '#fff', border: '2px solid #151515', borderRadius: '14px', padding: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <strong style={{ fontSize: '12px', textTransform: 'uppercase' }}>Move &amp; Inspect</strong>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button type="button" data-testid="sim-toggle-btn" onClick={() => setPaused(!paused)} style={{ padding: '4px 10px', fontSize: '11px', fontWeight: 800, border: '1.5px solid #151515', borderRadius: '6px', background: '#fff', cursor: 'pointer' }}>
                    {paused ? 'Resume' : 'Pause'}
                  </button>
                  <button type="button" data-testid="reset-sim-btn" onClick={handleResetPose} style={{ padding: '4px 10px', fontSize: '11px', fontWeight: 800, border: '1.5px solid #151515', borderRadius: '6px', background: '#fff', cursor: 'pointer' }}>
                    Reset Pose
                  </button>
                  <button type="button" data-testid="cam-reset-btn" onClick={handleResetCamera} style={{ padding: '4px 10px', fontSize: '11px', fontWeight: 800, border: '1.5px solid #151515', borderRadius: '6px', background: '#fff', cursor: 'pointer' }}>
                    Reset View
                  </button>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {CONSUMER_POSES.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    data-testid={`tryon-pose-${p.id}`}
                    onClick={() => handlePoseSelect(p.id)}
                    style={{
                      padding: '8px',
                      borderRadius: '8px',
                      border: '1.5px solid #151515',
                      background: activePoseId === p.id ? '#FF3D9A' : '#FFF8F1',
                      color: activePoseId === p.id ? '#fff' : '#151515',
                      fontWeight: 800,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
