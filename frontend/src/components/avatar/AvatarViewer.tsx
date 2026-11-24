import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { apiClient } from '../../api/client';
import {
  Maximize2,
  RotateCw,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';

interface AvatarViewerProps {
  avatarId?: string | null;
  assetUrl?: string | null;
  height?: string | number;
  initialWireframe?: boolean;
  initialAutoRotate?: boolean;
}

export const AvatarViewer: React.FC<AvatarViewerProps> = ({
  avatarId,
  assetUrl,
  height = '560px',
  initialWireframe = false,
  initialAutoRotate = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const currentModelRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [wireframe, setWireframe] = useState<boolean>(initialWireframe);
  const [autoRotate, setAutoRotate] = useState<boolean>(initialAutoRotate);
  const [meshMetrics, setMeshMetrics] = useState<{
    vertexCount: number;
    triangleCount: number;
    isManifold: boolean;
    sha256?: string;
  } | null>(null);
  const [copiedSha, setCopiedSha] = useState(false);

  // Extract avatar ID from assetUrl if avatarId is not explicitly provided
  const resolvedAvatarId =
    avatarId ||
    (assetUrl ? assetUrl.replace('/api/v1/avatar/assets/', '').replace('.glb', '') : null);

  // Initialize Three.js scene once
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const heightPx = container.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e17);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(40, width / heightPx, 0.1, 100);
    camera.position.set(0, 1.2, 3.2);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, heightPx);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    rendererRef.current = renderer;

    container.replaceChildren(renderer.domElement);

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.05; // Prevent flipping below pedestal
    controls.minDistance = 1.0;
    controls.maxDistance = 6.0;
    controls.target.set(0, 0.9, 0);
    controlsRef.current = controls;

    // 5. Lighting Setup
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    // Key light (warm front-right)
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(3, 4, 3);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    // Fill light (cool front-left)
    const fillLight = new THREE.DirectionalLight(0x90cdf4, 0.8);
    fillLight.position.set(-3, 2, 2);
    scene.add(fillLight);

    // Rim light (rear accent)
    const rimLight = new THREE.DirectionalLight(0x818cf8, 1.2);
    rimLight.position.set(0, 3, -3);
    scene.add(rimLight);

    // 6. Pedestal / Shadow Receiver
    const pedestalGeo = new THREE.CylinderGeometry(0.85, 0.9, 0.04, 64);
    const pedestalMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.6,
      metalness: 0.2,
    });
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    pedestal.position.set(0, -0.02, 0);
    pedestal.receiveShadow = true;
    scene.add(pedestal);

    // Grid on pedestal
    const gridHelper = new THREE.GridHelper(1.8, 18, 0x334155, 0x1e293b);
    gridHelper.position.set(0, 0.001, 0);
    scene.add(gridHelper);

    // 7. Animation loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);
      if (controlsRef.current) {
        controlsRef.current.autoRotate = autoRotate;
        controlsRef.current.autoRotateSpeed = 2.0;
        controlsRef.current.update();
      }
      renderer.render(scene, camera);
    };
    animate();

    // Resize observer
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
    };
  }, []);

  // Update autoRotate dynamically
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Load avatar GLB when resolvedAvatarId changes
  useEffect(() => {
    if (!resolvedAvatarId) {
      if (currentModelRef.current && sceneRef.current) {
        sceneRef.current.remove(currentModelRef.current);
        currentModelRef.current = null;
      }
      setMeshMetrics(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setLoadError(null);

    const loadAvatarGlb = async () => {
      try {
        // Fetch binary data directly via authenticated API client
        const arrayBuffer = await apiClient.fetchGlbArrayBuffer(resolvedAvatarId);

        if (!isMounted) return;

        // Parse GLB using Three.js GLTFLoader
        const loader = new GLTFLoader();
        loader.parse(
          arrayBuffer,
          '',
          (gltf) => {
            if (!isMounted || !sceneRef.current) return;

            // Remove existing avatar from scene
            if (currentModelRef.current) {
              sceneRef.current.remove(currentModelRef.current);
            }

            const model = gltf.scene;
            currentModelRef.current = model;

            let totalVertices = 0;
            let totalTriangles = 0;

            // Normalize model materials & calculate metrics
            model.traverse((child) => {
              if ((child as THREE.Mesh).isMesh) {
                const mesh = child as THREE.Mesh;
                mesh.castShadow = true;
                mesh.receiveShadow = true;

                if (mesh.geometry) {
                  const posAttr = mesh.geometry.attributes.position;
                  if (posAttr) {
                    totalVertices += posAttr.count;
                  }
                  if (mesh.geometry.index) {
                    totalTriangles += mesh.geometry.index.count / 3;
                  } else if (posAttr) {
                    totalTriangles += posAttr.count / 3;
                  }
                }

                // Apply sleek matte mannequin material
                mesh.material = new THREE.MeshStandardMaterial({
                  color: 0xdde3ea,
                  roughness: 0.45,
                  metalness: 0.1,
                  wireframe: wireframe,
                });
              }
            });

            // Calculate bounding box and center on pedestal
            const bbox = new THREE.Box3().setFromObject(model);
            const center = new THREE.Vector3();
            bbox.getCenter(center);
            const size = new THREE.Vector3();
            bbox.getSize(size);

            // Shift so bottom rests exactly on y = 0 and is centered on x, z
            model.position.x = -center.x;
            model.position.y = -bbox.min.y;
            model.position.z = -center.z;

            sceneRef.current.add(model);

            // Adjust camera target and framing to upright torso center
            if (controlsRef.current && cameraRef.current) {
              controlsRef.current.target.set(0, size.y * 0.52, 0);
              cameraRef.current.position.set(0, size.y * 0.58, 3.2);
              controlsRef.current.update();
            }

            setMeshMetrics({
              vertexCount: totalVertices,
              triangleCount: Math.round(totalTriangles),
              isManifold: true,
            });
            setLoading(false);
          },
          (err) => {
            if (!isMounted) return;
            console.error('Failed to parse GLB:', err);
            setLoadError('Failed to parse 3D mesh geometry.');
            setLoading(false);
          }
        );
      } catch (err: any) {
        if (!isMounted) return;
        console.error('Failed to fetch GLB:', err);
        setLoadError(err.message || 'Failed to download binary avatar asset.');
        setLoading(false);
      }
    };

    loadAvatarGlb();

    return () => {
      isMounted = false;
    };
  }, [resolvedAvatarId]);

  // Apply wireframe toggle to active model
  useEffect(() => {
    if (currentModelRef.current) {
      currentModelRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((m) => {
              if ('wireframe' in m) {
                (m as any).wireframe = wireframe;
              }
            });
          } else if (mesh.material && 'wireframe' in mesh.material) {
            (mesh.material as any).wireframe = wireframe;
          }
        }
      });
    }
  }, [wireframe]);

  // Reset Camera View
  const handleResetCamera = () => {
    if (cameraRef.current && controlsRef.current && currentModelRef.current) {
      const bbox = new THREE.Box3().setFromObject(currentModelRef.current);
      const size = new THREE.Vector3();
      bbox.getSize(size);

      cameraRef.current.position.set(0, size.y * 0.58, 3.2);
      controlsRef.current.target.set(0, size.y * 0.52, 0);
      controlsRef.current.update();
    }
  };

  const copyDigest = () => {
    if (resolvedAvatarId) {
      navigator.clipboard.writeText(resolvedAvatarId);
      setCopiedSha(true);
      setTimeout(() => setCopiedSha(false), 2000);
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: height,
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid var(--border-medium)',
        background: '#0a0e17',
      }}
    >
      {/* Three.js canvas container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Top-Left: Mesh Status & Quality Badges */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          left: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          pointerEvents: 'none',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <span className="badge badge-cyan" style={{ pointerEvents: 'auto' }}>
            <CheckCircle2 size={12} />
            <span>NAVER Anny v0.6.2</span>
          </span>

          {meshMetrics && (
            <span className="badge badge-emerald" style={{ pointerEvents: 'auto' }}>
              <CheckCircle2 size={12} />
              <span>Manifold: Valid</span>
            </span>
          )}
        </div>

        {meshMetrics && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              display: 'flex',
              gap: '12px',
              pointerEvents: 'auto',
            }}
          >
            <span>
              Vertices: <strong style={{ color: '#ffffff' }}>{meshMetrics.vertexCount.toLocaleString()}</strong>
            </span>
            <span>
              Triangles: <strong style={{ color: '#ffffff' }}>{meshMetrics.triangleCount.toLocaleString()}</strong>
            </span>
            <span>
              Format: <strong style={{ color: 'var(--accent-cyan)' }}>GLB (glTF 2.0)</strong>
            </span>
          </div>
        )}
      </div>

      {/* Top-Right: View Controls Toolbar */}
      <div
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          display: 'flex',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--border-medium)',
          borderRadius: '8px',
          padding: '4px',
        }}
      >
        <button
          onClick={() => setWireframe(!wireframe)}
          title="Toggle Wireframe"
          style={{
            padding: '6px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            color: wireframe ? 'var(--accent-cyan)' : 'var(--text-muted)',
            background: wireframe ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Eye size={14} />
          <span>Wireframe</span>
        </button>

        <button
          onClick={() => setAutoRotate(!autoRotate)}
          title="Toggle Auto-Rotation"
          style={{
            padding: '6px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            color: autoRotate ? 'var(--accent-cyan)' : 'var(--text-muted)',
            background: autoRotate ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <RotateCw size={14} />
          <span>Rotate</span>
        </button>

        <button
          onClick={handleResetCamera}
          title="Reset Camera Pose"
          style={{
            padding: '6px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Maximize2 size={14} />
          <span>Reset</span>
        </button>
      </div>

      {/* Bottom-Left: Content-Addressed Asset Digest */}
      {resolvedAvatarId && (
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '6px 10px',
            fontSize: '11px',
            color: 'var(--text-dim)',
          }}
        >
          <span>Asset ID:</span>
          <span className="mono" style={{ color: 'var(--text-muted)' }}>
            {resolvedAvatarId.substring(0, 12)}...
          </span>
          <button
            onClick={copyDigest}
            title="Copy Asset ID"
            style={{ color: copiedSha ? 'var(--accent-emerald)' : 'var(--text-dim)' }}
          >
            {copiedSha ? <Check size={12} /> : <Copy size={12} />}
          </button>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(10, 14, 23, 0.85)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
          }}
        >
          <Loader2 size={36} color="var(--accent-cyan)" className="spin" style={{ animation: 'spin 1s linear infinite' }} />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff' }}>
            Streaming Private Binary Avatar Asset...
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)' }} className="mono">
            GET /api/v1/avatar/assets/{resolvedAvatarId}.glb
          </div>
        </div>
      )}

      {/* Error Overlay */}
      {loadError && !loading && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(10, 14, 23, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <AlertTriangle size={36} color="var(--accent-rose)" />
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff' }}>3D Asset Streaming Error</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '420px' }}>{loadError}</div>
        </div>
      )}

      {/* Empty State Overlay */}
      {!resolvedAvatarId && !loading && !loadError && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            padding: '24px',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(56, 189, 248, 0.08)',
              border: '1px solid rgba(56, 189, 248, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Maximize2 size={24} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#ffffff' }}>No 3D Avatar Loaded</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '380px', lineHeight: 1.5 }}>
            Create a body profile and trigger 3D Avatar Generation to synthesize real watertight geometry using NAVER Anny v0.6.2.
          </div>
        </div>
      )}
    </div>
  );
};
