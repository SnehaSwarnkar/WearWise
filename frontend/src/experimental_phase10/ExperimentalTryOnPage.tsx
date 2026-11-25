import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import Header from '../pages/Header';
import { ARTICULATED_POSES, ArticulationState, NEUTRAL_POSE } from './ArticulatedPoseLibrary';
import { SIM_FABRICS } from './FabricProfiles';
import { ClientMetrics, WorkerClothClient } from './WorkerClothClient';

const BODY_ENGINE_BASE = 'http://127.0.0.1:8000';
const COMMERCE_BASE = 'http://127.0.0.1:8001';

interface AvatarOption {
  id: string;
  label: string;
  glbUrl: string;
  statureCm: number;
  chestCm: number;
  waistCm: number;
  shoulderCm: number;
  isPrivate: boolean;
}

const STAGING_AVATAR_PROFILES: AvatarOption[] = [
  {
    id: 'PROFILE_B_ATHLETIC_MALE',
    label: 'Athletic Male (178.5 cm)',
    glbUrl: '/experimental_phase11/PROFILE_B_ATHLETIC_MALE.glb',
    statureCm: 178.5,
    chestCm: 85.44,
    waistCm: 67.3,
    shoulderCm: 41.54,
    isPrivate: false,
  },
  {
    id: 'PROFILE_A_SLIM_MALE',
    label: 'Slim Male (172.0 cm)',
    glbUrl: '/experimental_phase11/PROFILE_A_SLIM_MALE.glb',
    statureCm: 172.0,
    chestCm: 81.74,
    waistCm: 64.09,
    shoulderCm: 39.19,
    isPrivate: false,
  },
  {
    id: 'PROFILE_C_BROAD_MALE',
    label: 'Broad Male (184.0 cm)',
    glbUrl: '/experimental_phase11/PROFILE_C_BROAD_MALE.glb',
    statureCm: 184.0,
    chestCm: 88.71,
    waistCm: 80.12,
    shoulderCm: 43.68,
    isPrivate: false,
  },
  {
    id: 'PROFILE_D_PETITE_FEMININE',
    label: 'Petite Feminine (161.0 cm)',
    glbUrl: '/experimental_phase11/PROFILE_D_PETITE_FEMININE.glb',
    statureCm: 161.0,
    chestCm: 83.91,
    waistCm: 64.98,
    shoulderCm: 37.13,
    isPrivate: false,
  },
  {
    id: 'PROFILE_E_TALL_NEUTRAL',
    label: 'Tall Neutral (180.0 cm)',
    glbUrl: '/experimental_phase11/PROFILE_E_TALL_NEUTRAL.glb',
    statureCm: 180.0,
    chestCm: 88.03,
    waistCm: 71.97,
    shoulderCm: 40.78,
    isPrivate: false,
  },
];

interface ResolvedGarmentAsset {
  garment_id: string;
  sku: string;
  name: string;
  status: string;
  revision: number;
  version: string;
  size: string;
  available_sizes: string[];
  asset_url: string;
  sha256?: string;
  fabric_profile?: {
    id?: string;
    name?: string;
    gsm?: number;
    thickness_mm?: number;
    provisional?: boolean;
  };
  measurements?: Record<string, any>;
  qa_status?: string;
}

const CONSUMER_POSE_IDS = ['P0', 'P1', 'P2', 'P3', 'P6', 'P9', 'P11'];

function mapFabricToSolverId(backendFabricId?: string): string {
  if (!backendFabricId) return 'waffle_knit_240';
  if (backendFabricId.includes('poplin')) return 'rigid_poplin_140';
  return 'waffle_knit_240';
}

function classifyFit(chestEase: number, shoulderEase: number): string {
  if (chestEase < 0 || shoulderEase < -1.5) return 'Too tight';
  if (chestEase < 5) return 'Close fit';
  if (chestEase <= 12) return 'Regular fit';
  if (chestEase <= 20) return 'Relaxed fit';
  return 'Too loose';
}

export default function ExperimentalTryOnPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const sku = searchParams.get('sku') || 'TSH-WW-PHASE11-ACCEPTANCE-001';
  const requestedRev = searchParams.get('revision');
  const [selectedSize, setSelectedSize] = useState<string>(searchParams.get('size') || 'M');
  const [selectedAvatarId, setSelectedAvatarId] = useState<string>(STAGING_AVATAR_PROFILES[0].id);

  const [garmentMeta, setGarmentMeta] = useState<ResolvedGarmentAsset | null>(null);
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [activePoseId, setActivePoseId] = useState<string>('P0');
  const [paused, setPaused] = useState<boolean>(false);
  const [showDevDiag, setShowDevDiag] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<ClientMetrics | null>(null);
  const [cartMsg, setCartMsg] = useState<string | null>(null);

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
      const revQuery = requestedRev ? `&revision=${encodeURIComponent(requestedRev)}` : '';
      const metaUrl = `${BODY_ENGINE_BASE}/api/v1/merchant/garments/${encodeURIComponent(sku)}/shopper-asset?size=${encodeURIComponent(selectedSize)}${revQuery}`;
      const res = await fetch(metaUrl, { cache: 'no-store' });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Failed to resolve garment ${sku} size ${selectedSize} (HTTP ${res.status})`);
      }
      const meta: ResolvedGarmentAsset = await res.json();
      setGarmentMeta(meta);
      setLoadState('ready');
    } catch (e: any) {
      setGarmentMeta(null);
      setLoadState('error');
      setErrorMsg(e?.message || 'Failed to resolve published staging garment asset.');
    }
  }, [sku, selectedSize, requestedRev]);

  useEffect(() => {
    resolveAndLoad();
  }, [resolveAndLoad]);

  // Mount & run Three.js + Web Worker cloth simulation when meta & avatar are ready
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
    client.setCallbacks(
      (m) => setMetrics(m),
      (msg) => setErrorMsg(msg)
    );

    const loader = new GLTFLoader();
    const garmentAssetFullUrl = garmentMeta.asset_url.startsWith('http')
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

        // Align garment collar/torso anchor to the personalised avatar's neck01 rest position
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
        const m0 = client.getMetrics();
        if (m0) setMetrics(m0);
      })
      .catch((err) => {
        if (disposed) return;
        setLoadState('error');
        setErrorMsg(`Asset load failure: ${err?.message || 'Unable to load GLB'}`);
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
    if (!garmentMeta) return;
    setCartMsg('Adding to staging cart...');
    try {
      const sessKey = 'wearwise_cart_session_id';
      let sid = localStorage.getItem(sessKey);
      if (!sid) {
        sid = `sess_${Math.random().toString(36).slice(2, 11)}`;
        localStorage.setItem(sessKey, sid);
      }
      const res = await fetch(`${COMMERCE_BASE}/api/cart/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sid,
          item: {
            id: 1,
            sku: garmentMeta.sku,
            published_revision: garmentMeta.revision,
            name: garmentMeta.name,
            price: 2999,
            size: selectedSize,
            quantity: 1,
          },
        }),
      });
      if (!res.ok) {
        throw new Error(`Cart API HTTP ${res.status}`);
      }
      setCartMsg(`Added ${garmentMeta.sku} (Size ${selectedSize}, Rev ${garmentMeta.revision}) to cart.`);
    } catch (e: any) {
      setCartMsg(`Cart request failed: ${e?.message || 'Unable to add item'}`);
    }
  };

  const fitSummary = useMemo(() => {
    const gm = garmentMeta?.measurements;
    if (!gm) return null;
    const gChest = Number(gm.chest_circumference_cm ?? gm.chest_cm ?? (selectedSize === 'S' ? 96 : selectedSize === 'L' ? 112 : 104));
    const gWaist = Number(gm.waist_circumference_cm ?? gm.waist_cm ?? (selectedSize === 'S' ? 92 : selectedSize === 'L' ? 108 : 100));
    const gShoulder = Number(gm.shoulder_width_cm ?? gm.shoulder_cm ?? (selectedSize === 'S' ? 43 : selectedSize === 'L' ? 49 : 46));
    const chestEase = Number((gChest - activeAvatar.chestCm).toFixed(1));
    const waistEase = Number((gWaist - activeAvatar.waistCm).toFixed(1));
    const shoulderEase = Number((gShoulder - activeAvatar.shoulderCm).toFixed(1));
    return {
      chestEase,
      waistEase,
      shoulderEase,
      classification: classifyFit(chestEase, shoulderEase),
    };
  }, [garmentMeta, activeAvatar, selectedSize]);

  const solverFabId = mapFabricToSolverId(garmentMeta?.fabric_profile?.id);
  const solverFab = SIM_FABRICS[solverFabId];

  return (
    <div style={{ minHeight: '100vh', background: '#fdfbf7' }}>
      <Header />
      <main style={{ maxWidth: '1320px', margin: '0 auto', padding: '20px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '14px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '1px', color: '#be185d' }}>
              STAGING 3D TRY-ON · PERSONALISED AVATAR &amp; APPROVED GARMENT TWIN
            </span>
            <h1 style={{ fontSize: '25px', fontWeight: 900, margin: '4px 0' }}>
              {garmentMeta?.name || sku}
            </h1>
            <p style={{ fontSize: '13px', color: '#475569', margin: 0 }}>
              SKU: <code>{sku}</code> · Revision: <strong>{garmentMeta?.revision ?? requestedRev ?? '—'}</strong> · Size: <strong>{selectedSize}</strong>
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link to="/cart" style={{ padding: '8px 14px', borderRadius: '8px', border: '2px solid #0f172a', fontWeight: 800, fontSize: '12px', textDecoration: 'none', color: '#0f172a', background: '#fff' }}>
              View Cart
            </Link>
            <button
              type="button"
              data-testid="add-to-cart-btn"
              disabled={loadState !== 'ready'}
              onClick={handleAddToCart}
              style={{ padding: '8px 16px', borderRadius: '8px', border: '2px solid #0f172a', fontWeight: 900, fontSize: '12px', background: '#d8ff3f', cursor: loadState === 'ready' ? 'pointer' : 'not-allowed' }}
            >
              Add Size {selectedSize} to Cart
            </button>
          </div>
        </div>

        {cartMsg && (
          <div data-testid="cart-status-banner" style={{ padding: '10px 14px', background: '#ecfccb', border: '1.5px solid #4d7c0f', borderRadius: '8px', fontSize: '12px', fontWeight: 700, marginBottom: '12px' }}>
            {cartMsg}
          </div>
        )}

        {loadState === 'error' && (
          <div data-testid="tryon-error-banner" style={{ padding: '14px', background: '#fef2f2', border: '2px solid #dc2626', borderRadius: '10px', color: '#991b1b', marginBottom: '14px' }}>
            <strong>Simulation Stopped (Fail-Closed):</strong> {errorMsg}
            <button type="button" onClick={resolveAndLoad} style={{ marginLeft: '12px', padding: '4px 10px', fontWeight: 800, cursor: 'pointer' }}>
              Retry
            </button>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '18px', alignItems: 'start' }}>
          <div>
            <div style={{ position: 'relative', border: '2px solid #0f172a', borderRadius: '12px', overflow: 'hidden', background: '#5a0b23', minHeight: '560px' }}>
              {loadState === 'loading' && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800 }}>
                  Loading personalised avatar &amp; approved garment revision...
                </div>
              )}
              <div ref={mountRef} style={{ width: '100%', height: '560px' }} />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Size Comparison */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <strong style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>1. SELECT GARMENT SIZE</strong>
              <div style={{ display: 'flex', gap: '8px' }}>
                {['S', 'M', 'L'].map((sz) => (
                  <button
                    key={sz}
                    type="button"
                    data-testid={`size-btn-${sz}`}
                    onClick={() => handleSizeChange(sz)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '6px',
                      border: '1.5px solid #0f172a',
                      background: selectedSize === sz ? '#ff3d9a' : '#f8fafc',
                      color: selectedSize === sz ? '#fff' : '#0f172a',
                      fontWeight: 900,
                      cursor: 'pointer',
                    }}
                  >
                    Size {sz}
                  </button>
                ))}
              </div>
            </div>

            {/* Avatar Profile Selection */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <strong style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>2. PERSONALISED AVATAR PROFILE</strong>
              <select
                data-testid="avatar-select"
                value={selectedAvatarId}
                onChange={(e) => setSelectedAvatarId(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1.5px solid #0f172a', fontWeight: 700, fontSize: '12px' }}
              >
                {STAGING_AVATAR_PROFILES.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label} — Chest {a.chestCm} cm
                  </option>
                ))}
              </select>
            </div>

            {/* Honest Fit Summary */}
            {fitSummary && (
              <div data-testid="fit-summary-card" style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
                <strong style={{ fontSize: '12px', display: 'block', marginBottom: '6px' }}>HONEST FIT SUMMARY (SIZE {selectedSize})</strong>
                <div style={{ fontSize: '16px', fontWeight: 900, color: '#be185d', marginBottom: '6px' }}>
                  {fitSummary.classification}
                </div>
                <div style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 10px' }}>
                  <div>Chest Ease: <strong>+{fitSummary.chestEase} cm</strong></div>
                  <div>Waist Ease: <strong>+{fitSummary.waistEase} cm</strong></div>
                  <div>Shoulder Ease: <strong>{fitSummary.shoulderEase >= 0 ? `+${fitSummary.shoulderEase}` : fitSummary.shoulderEase} cm</strong></div>
                  <div>Fabric: <strong>{solverFab?.arealDensityGsm ?? 240} GSM</strong></div>
                </div>
                <p style={{ fontSize: '11px', color: '#64748b', margin: '8px 0 0' }}>
                  Geometric ease reflects static pattern dimensions; dynamic drape uses provisional fabric parameters.
                </p>
              </div>
            )}

            {/* Consumer Pose & Camera Controls */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong style={{ fontSize: '12px' }}>3. TRY-ON POSES &amp; CONTROLS</strong>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button type="button" data-testid="sim-toggle-btn" onClick={() => setPaused(!paused)} style={{ padding: '4px 8px', fontSize: '11px', fontWeight: 700, border: '1px solid #0f172a', borderRadius: '5px', cursor: 'pointer' }}>
                    {paused ? 'Resume' : 'Pause'}
                  </button>
                  <button type="button" data-testid="reset-sim-btn" onClick={handleResetPose} style={{ padding: '4px 8px', fontSize: '11px', fontWeight: 700, border: '1px solid #0f172a', borderRadius: '5px', cursor: 'pointer' }}>
                    Reset
                  </button>
                  <button type="button" data-testid="cam-reset-btn" onClick={handleResetCamera} style={{ padding: '4px 8px', fontSize: '11px', fontWeight: 700, border: '1px solid #0f172a', borderRadius: '5px', cursor: 'pointer' }}>
                    Cam
                  </button>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                {ARTICULATED_POSES.filter((p) => CONSUMER_POSE_IDS.includes(p.id)).map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    data-testid={`tryon-pose-${p.id}`}
                    onClick={() => handlePoseSelect(p.id)}
                    style={{
                      padding: '6px 8px',
                      borderRadius: '6px',
                      border: '1.5px solid #0f172a',
                      background: activePoseId === p.id ? '#ff3d9a' : '#f8fafc',
                      color: activePoseId === p.id ? '#fff' : '#0f172a',
                      fontWeight: 800,
                      fontSize: '11px',
                      cursor: 'pointer',
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Collapsible Developer Diagnostics */}
            <div style={{ background: '#0f172a', color: '#f8fafc', borderRadius: '10px', padding: '10px 14px', fontSize: '11px', fontFamily: 'monospace' }}>
              <button
                type="button"
                data-testid="toggle-dev-diag"
                onClick={() => setShowDevDiag(!showDevDiag)}
                style={{ background: 'none', border: 'none', color: '#d8ff3f', fontWeight: 800, cursor: 'pointer', padding: 0, fontFamily: 'monospace' }}
              >
                {showDevDiag ? '▼' : '▶'} Developer Diagnostics ({garmentMeta?.sku ?? sku} · Rev {garmentMeta?.revision ?? '—'} · {selectedSize})
              </button>
              {showDevDiag && (
                <div data-testid="dev-diagnostics" data-metrics={metrics ? JSON.stringify(metrics) : ''} style={{ marginTop: '8px', lineHeight: 1.5 }}>
                  <div>Avatar: {activeAvatar.id} | SHA: {garmentMeta?.sha256?.slice(0, 12) ?? 'n/a'}...</div>
                  <div>QA: {garmentMeta?.qa_status ?? 'UNKNOWN'} | Fabric: {garmentMeta?.fabric_profile?.id ?? 'default'}</div>
                  {metrics && (
                    <>
                      <div>Mode: {metrics.workerMode} | State: {metrics.simState} | FPS: {metrics.fps} (Avg {metrics.avgFps})</div>
                      <div>Solve: {metrics.lastSolveMs} ms | Seam Sep: {metrics.seamSeparationMm} mm | Pen: {metrics.penetratingParticles}/{metrics.particleCount}</div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
