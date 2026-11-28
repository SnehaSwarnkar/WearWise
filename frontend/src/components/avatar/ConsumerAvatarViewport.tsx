import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { Loader2, RotateCcw } from 'lucide-react';
import { devAuthHeaderProvider, getBodyApiBase } from '../../api/client';

interface ConsumerAvatarViewportProps {
  assetUrl?: string | null;
  height?: number | string;
  emptyTitle?: string;
  emptySubtitle?: string;
  autoRotate?: boolean;
}

/**
 * Clean, flicker-free consumer 3D avatar preview.
 * Keeps a single WebGL scene & renderer mounted across regenerations and swaps
 * the loaded GLTF mesh atomically once ready, with zero internal telemetry.
 */
export const ConsumerAvatarViewport: React.FC<ConsumerAvatarViewportProps> = ({
  assetUrl,
  height = 480,
  emptyTitle = 'Your 3D body preview will appear here',
  emptySubtitle = 'Fill in your height and proportions, then generate your personal preview.',
  autoRotate = false,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const modelGroupRef = useRef<THREE.Group | null>(null);
  const requestSeqRef = useRef(0);

  const [isUpdating, setIsUpdating] = useState(false);
  const [hasModel, setHasModel] = useState(false);
  const [loadFailed, setLoadFailed] = useState(false);

  // Mount persistent Three.js stage once
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#f4efe8');
    sceneRef.current = scene;

    const w = el.clientWidth || 520;
    const h = typeof height === 'number' ? height : el.clientHeight || 480;
    const camera = new THREE.PerspectiveCamera(40, w / h, 0.05, 40);
    camera.position.set(0, 1.08, 2.35);
    cameraRef.current = camera;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    } catch {
      return;
    }
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    el.innerHTML = '';
    el.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.target.set(0, 0.92, 0);
    controls.minDistance = 1.1;
    controls.maxDistance = 4.2;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 1.2;
    controls.update();
    controlsRef.current = controls;

    // Warm studio 3-point lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.75));
    const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.45);
    keyLight.position.set(1.8, 2.8, 2.6);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xe0e7ff, 0.65);
    fillLight.position.set(-2.0, 1.4, -1.2);
    scene.add(fillLight);
    const rimLight = new THREE.DirectionalLight(0xfdf2f8, 0.55);
    rimLight.position.set(0, 2.0, -2.5);
    scene.add(rimLight);

    // Subtle circular turntable pedestal
    const plinth = new THREE.Mesh(
      new THREE.CylinderGeometry(0.46, 0.50, 0.03, 48),
      new THREE.MeshStandardMaterial({ color: '#e5ddd2', roughness: 0.7, metalness: 0.05 })
    );
    plinth.position.y = -0.015;
    scene.add(plinth);

    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const cw = containerRef.current.clientWidth || 520;
      const ch = typeof height === 'number' ? height : containerRef.current.clientHeight || 480;
      cameraRef.current.aspect = cw / ch;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(cw, ch);
    };
    window.addEventListener('resize', handleResize);

    let rafId = 0;
    const renderLoop = () => {
      rafId = requestAnimationFrame(renderLoop);
      controls.update();
      renderer.render(scene, camera);
    };
    renderLoop();

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', handleResize);
      controls.dispose();
      renderer.dispose();
      sceneRef.current = null;
      rendererRef.current = null;
      controlsRef.current = null;
      modelGroupRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Atomically load & swap avatar GLB without tearing down WebGL context
  useEffect(() => {
    if (!assetUrl || !sceneRef.current) {
      if (!assetUrl && modelGroupRef.current && sceneRef.current) {
        sceneRef.current.remove(modelGroupRef.current);
        modelGroupRef.current = null;
        setHasModel(false);
      }
      return;
    }

    const seq = ++requestSeqRef.current;
    setIsUpdating(true);
    setLoadFailed(false);

    const resolvedUrl =
      assetUrl.startsWith('http') || assetUrl.startsWith('/api/')
        ? assetUrl.startsWith('/api/')
          ? `${getBodyApiBase()}${assetUrl}`
          : assetUrl
        : assetUrl;

    const loader = new GLTFLoader();
    loader.setWithCredentials(true);

    fetch(resolvedUrl, {
      credentials: 'include',
      headers: devAuthHeaderProvider.getAuthHeaders(),
      cache: 'no-store',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Unable to load avatar preview');
        return res.arrayBuffer();
      })
      .then((buf) => {
        if (seq !== requestSeqRef.current) return;
        loader.parse(
          buf,
          '',
          (gltf) => {
            if (seq !== requestSeqRef.current || !sceneRef.current) return;
            const nextGroup = gltf.scene;
            // Apply warm ceramic mannequin shading consistently
            nextGroup.traverse((obj) => {
              const mesh = obj as THREE.Mesh;
              if (mesh.isMesh) {
                mesh.material = new THREE.MeshStandardMaterial({
                  color: '#d9c5b2',
                  roughness: 0.62,
                  metalness: 0.04,
                });
              }
            });

            // Normalize feet onto y = 0 and center X/Z smoothly
            const box = new THREE.Box3().setFromObject(nextGroup);
            const size = new THREE.Vector3();
            const center = new THREE.Vector3();
            box.getSize(size);
            box.getCenter(center);
            nextGroup.position.x -= center.x;
            nextGroup.position.z -= center.z;
            nextGroup.position.y -= box.min.y;

            if (modelGroupRef.current) {
              sceneRef.current.remove(modelGroupRef.current);
              modelGroupRef.current.traverse((o) => {
                const m = o as THREE.Mesh;
                if (m.isMesh) {
                  m.geometry?.dispose();
                  if (Array.isArray(m.material)) m.material.forEach((mm) => mm.dispose());
                  else m.material?.dispose();
                }
              });
            }

            sceneRef.current.add(nextGroup);
            modelGroupRef.current = nextGroup;
            setHasModel(true);
            setIsUpdating(false);

            if (controlsRef.current && cameraRef.current && size.y > 0.5) {
              controlsRef.current.target.set(0, size.y * 0.53, 0);
              controlsRef.current.update();
            }
          },
          () => {
            if (seq === requestSeqRef.current) {
              setLoadFailed(true);
              setIsUpdating(false);
            }
          }
        );
      })
      .catch(() => {
        if (seq === requestSeqRef.current) {
          setLoadFailed(true);
          setIsUpdating(false);
        }
      });
  }, [assetUrl]);

  const handleResetView = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    cameraRef.current.position.set(0, 1.08, 2.35);
    controlsRef.current.target.set(0, 0.92, 0);
    controlsRef.current.update();
  };

  return (
    <div
      data-testid="consumer-avatar-viewport"
      style={{
        position: 'relative',
        width: '100%',
        height: typeof height === 'number' ? `${height}px` : height,
        background: '#f4efe8',
        border: '2.5px solid #151515',
        boxShadow: '6px 6px 0 #151515',
        overflow: 'hidden',
      }}
    >
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {!hasModel && !isUpdating && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '28px',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              background: '#ffffff',
              border: '2px solid #151515',
              padding: '20px 24px',
              maxWidth: '340px',
            }}
          >
            <strong style={{ display: 'block', fontSize: '15px', marginBottom: '6px' }}>{emptyTitle}</strong>
            <span style={{ fontSize: '13px', color: '#454854', lineHeight: 1.5 }}>{emptySubtitle}</span>
          </div>
        </div>
      )}

      {isUpdating && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            background: '#ffffff',
            border: '2px solid #151515',
            fontSize: '12px',
            fontWeight: 800,
          }}
        >
          <Loader2 size={14} className="animate-spin" />
          Updating your preview…
        </div>
      )}

      {loadFailed && (
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            right: '12px',
            padding: '8px 12px',
            background: '#fee2e2',
            border: '2px solid #991b1b',
            color: '#991b1b',
            fontSize: '12px',
            fontWeight: 700,
          }}
        >
          We could not display the 3D model preview right now. Please click Regenerate Preview.
        </div>
      )}

      {hasModel && (
        <div style={{ position: 'absolute', bottom: '12px', right: '12px', display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={handleResetView}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              background: '#ffffff',
              border: '2px solid #151515',
              padding: '6px 10px',
              fontSize: '11px',
              fontWeight: 800,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={13} /> Reset View
          </button>
        </div>
      )}
    </div>
  );
};
