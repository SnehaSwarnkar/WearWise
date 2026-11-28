import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { apiClient } from '../../api/client';
import { ClothSimulator, FABRIC_PROFILES } from './ClothSimulator';
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

interface GarmentQaSummary {
  overall_status?: string;
  statuses?: Record<string, string>;
  validation_source?: string;
  size_variants?: Record<string, { overall_prototype_qa?: string; glb_file?: string; revision?: string }>;
}

interface AvatarViewerProps {
  avatarId?: string | null;
  assetUrl?: string | null;
  garmentUrl?: string | null;
  garmentScale?: number;
  showGarment?: boolean;
  garmentQaReport?: GarmentQaSummary | null;
  garmentUnavailableError?: string | null;
  height?: string | number;
  initialWireframe?: boolean;
  initialAutoRotate?: boolean;
  studioBackground?: string;
  armAngle?: number;
  fabricProfile?: string;
}

/**
 * Extracts explicit garment size token (S | M | L) from a GLB filename or prototype asset URL
 * without guessing from unrelated segments.
 * Supports:
 * - TSH-WW-CREW-001_S_candidate.glb
 * - TSH-WW-CREW-001_S_candidate_rev3.glb
 * - TSH-WW-CREW-001_M_prototype_rev2.glb
 * - TSH-WW-CREW-001_L.glb
 * - /api/v1/merchant/garments/prototype-preview/TSH-WW-CREW-001/assets/S?revision=rev3
 */
export function extractGarmentSizeFromUrl(garmentUrlOrFilename: string): 'S' | 'M' | 'L' | null {
  if (!garmentUrlOrFilename || typeof garmentUrlOrFilename !== 'string') return null;
  const cleanPath = garmentUrlOrFilename.split('?')[0].split('#')[0].trim();
  if (!cleanPath) return null;

  const protoRouteMatch = cleanPath.match(/\/(?:prototype-preview|revisions)\/[^/]+\/assets\/([SML])$/);
  if (protoRouteMatch) {
    return protoRouteMatch[1] as 'S' | 'M' | 'L';
  }

  const basename = cleanPath.split('/').pop() || cleanPath;
  const fileMatch = basename.match(/_([SML])(?:_(?:candidate|prototype)(?:_rev\d+)?|_rev\d+)?\.glb$/i);
  if (fileMatch) {
    return fileMatch[1].toUpperCase() as 'S' | 'M' | 'L';
  }
  return null;
}

export function extractGarmentAssetLabel(
  garmentUrl: string,
  matchedSize: 'S' | 'M' | 'L' | null,
  garmentQaReport?: GarmentQaSummary | null
): string {
  const fromQa = matchedSize ? garmentQaReport?.size_variants?.[matchedSize]?.glb_file : undefined;
  if (fromQa) return fromQa;
  const cleanPath = garmentUrl.split('?')[0].split('#')[0];
  return cleanPath.split('/').pop() || cleanPath;
}

interface AnalyzedGeometryMetrics {
  meshCount: number;
  vertexCount: number;
  triangleCount: number;
  nonManifoldEdges: number;
  boundaryEdges: number;
  hasTexCoords: boolean;
}

function analyzeSceneGeometry(root: THREE.Object3D): AnalyzedGeometryMetrics {
  let meshCount = 0;
  let vertexCount = 0;
  let triangleCount = 0;
  let hasTexCoords = true;

  const posToWeldId = new Map<string, number>();
  let nextWeldId = 0;
  const edgeCounts = new Map<string, number>();

  root.traverse((child) => {
    if ((child as THREE.Mesh).isMesh) {
      const mesh = child as THREE.Mesh;
      meshCount += 1;
      const geo = mesh.geometry;
      if (!geo) return;
      const posAttr = geo.attributes.position;
      if (!posAttr) return;
      if (!geo.attributes.uv) hasTexCoords = false;

      vertexCount += posAttr.count;
      const indexAttr = geo.index;
      const triCount = indexAttr ? Math.floor(indexAttr.count / 3) : Math.floor(posAttr.count / 3);
      triangleCount += triCount;

      const localWeldIds = new Int32Array(posAttr.count);
      for (let i = 0; i < posAttr.count; i++) {
        const key = `${Math.round(posAttr.getX(i) * 1e4)},${Math.round(posAttr.getY(i) * 1e4)},${Math.round(posAttr.getZ(i) * 1e4)}`;
        let wid = posToWeldId.get(key);
        if (wid === undefined) {
          wid = nextWeldId++;
          posToWeldId.set(key, wid);
        }
        localWeldIds[i] = wid;
      }

      for (let t = 0; t < triCount; t++) {
        const i0 = indexAttr ? indexAttr.getX(t * 3) : t * 3;
        const i1 = indexAttr ? indexAttr.getX(t * 3 + 1) : t * 3 + 1;
        const i2 = indexAttr ? indexAttr.getX(t * 3 + 2) : t * 3 + 2;
        const a = localWeldIds[i0];
        const b = localWeldIds[i1];
        const c = localWeldIds[i2];
        const edges: [number, number][] = [[a, b], [b, c], [c, a]];
        for (const [u, v] of edges) {
          if (u === v) continue;
          const ek = u < v ? `${u}:${v}` : `${v}:${u}`;
          edgeCounts.set(ek, (edgeCounts.get(ek) || 0) + 1);
        }
      }
    }
  });

  let nonManifoldEdges = 0;
  let boundaryEdges = 0;
  edgeCounts.forEach((cnt) => {
    if (cnt > 2) nonManifoldEdges += 1;
    else if (cnt === 1) boundaryEdges += 1;
  });

  return { meshCount, vertexCount, triangleCount, nonManifoldEdges, boundaryEdges, hasTexCoords };
}

export const AvatarViewer: React.FC<AvatarViewerProps> = ({
  avatarId,
  assetUrl,
  garmentUrl,
  garmentScale = 1.0,
  showGarment = true,
  garmentQaReport = null,
  garmentUnavailableError = null,
  height = '560px',
  initialWireframe = false,
  initialAutoRotate = false,
  studioBackground = '#720e2c',
  armAngle = 0,
  fabricProfile = 'knit',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const currentModelRef = useRef<THREE.Group | null>(null);
  const currentGarmentRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const simulatorRef = useRef<ClothSimulator>(new ClothSimulator());

  const [loading, setLoading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [wireframe, setWireframe] = useState<boolean>(initialWireframe);
  const [autoRotate, setAutoRotate] = useState<boolean>(initialAutoRotate);
  const [avatarMetrics, setAvatarMetrics] = useState<{
    assetName: string;
    meshCount: number;
    vertexCount: number;
    triangleCount: number;
    nonManifoldEdges: number;
    boundaryEdges: number;
    topologyLabel: string;
    validationSource: string;
  } | null>(null);
  const [garmentMetrics, setGarmentMetrics] = useState<{
    assetName: string;
    meshCount: number;
    vertexCount: number;
    triangleCount: number;
    nonManifoldEdges: number;
    boundaryEdges: number;
    hasTexCoords: boolean;
    topologyLabel: string;
    qaStatus: string;
    qaSource: string;
  } | null>(null);
  const [garmentLoadError, setGarmentLoadError] = useState<string | null>(null);
  const [copiedSha, setCopiedSha] = useState(false);

  // Extract avatar ID from assetUrl if avatarId is not explicitly provided
  const resolvedAvatarId =
    avatarId ||
    (assetUrl ? assetUrl.replace('/api/v1/avatar/assets/', '').replace('.glb', '') : null);

  // Fits camera to model bounding box considering container dimensions and overlay clearances
  const fitCameraToModel = useCallback((model: THREE.Object3D) => {
    if (!cameraRef.current || !controlsRef.current || !containerRef.current) return;

    const bbox = new THREE.Box3().setFromObject(model);
    const size = new THREE.Vector3();
    bbox.getSize(size);

    // Upright fashion studio framing centered on mannequin torso
    const targetY = size.y > 0 ? size.y * 0.58 : 0.92;
    cameraRef.current.position.set(0, targetY + 0.05, 2.50);
    controlsRef.current.target.set(0, targetY, 0);
    controlsRef.current.update();
  }, []);

  // Initialize Three.js scene once
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const heightPx = container.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(studioBackground || 0x720e2c);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(38, width / heightPx, 0.1, 100);
    camera.position.set(0, 0.95, 2.50);
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
    controls.maxPolarAngle = Math.PI / 2 + 0.05; // Prevent flipping below ground
    controls.minDistance = 0.8;
    controls.maxDistance = 6.0;
    controls.target.set(0, 0.92, 0);
    controlsRef.current = controls;

    // 5. Lighting Setup (Soft High-Fashion 3-Point Studio Lighting)
    const ambientLight = new THREE.AmbientLight(0xfff5f0, 0.70);
    scene.add(ambientLight);

    // Key light (warm front-right)
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
    keyLight.position.set(2.5, 4.0, 3.0);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.bias = -0.0001;
    scene.add(keyLight);

    // Fill light (soft cool front-left)
    const fillLight = new THREE.DirectionalLight(0xfce7f3, 0.80);
    fillLight.position.set(-2.5, 2.5, 2.5);
    scene.add(fillLight);

    // Rim light (rear edge highlight against burgundy background)
    const rimLight = new THREE.DirectionalLight(0xffffff, 1.15);
    rimLight.position.set(0, 3.5, -2.5);
    scene.add(rimLight);

    // 6. Seamless Ground Shadow Receiver
    const floorGeo = new THREE.PlaneGeometry(10, 10);
    const floorMat = new THREE.ShadowMaterial({ opacity: 0.28 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0.0;
    floor.receiveShadow = true;
    scene.add(floor);

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
      if (currentModelRef.current) {
        fitCameraToModel(currentModelRef.current);
      }
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

  // Load avatar GLB when resolvedAvatarId or assetUrl changes
  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setLoadError(null);

    const loadAvatarGlb = async () => {
      try {
        let arrayBuffer: ArrayBuffer;
        if (assetUrl && (assetUrl.startsWith('/') || assetUrl.startsWith('http'))) {
          const res = await fetch(assetUrl);
          if (!res.ok) throw new Error(`Failed to load 3D avatar asset from ${assetUrl}`);
          arrayBuffer = await res.arrayBuffer();
        } else if (resolvedAvatarId) {
          arrayBuffer = await apiClient.fetchGlbArrayBuffer(resolvedAvatarId);
        } else {
          // Fallback to local baseline Anny mannequin
          const res = await fetch('/avatars/anny_baseline_male.glb');
          if (!res.ok) throw new Error('Baseline avatar mesh not found');
          arrayBuffer = await res.arrayBuffer();
        }

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

                // Apply pearl-white smooth mannequin material matching reference design
                mesh.material = new THREE.MeshStandardMaterial({
                  color: 0xf5f7fa,
                  roughness: 0.32,
                  metalness: 0.08,
                  wireframe: wireframe,
                });
              }
            });

            // Calculate bounding box and center on ground
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

            // Bind avatar to kinematics simulator
            simulatorRef.current.bindAvatar(model);
            if (armAngle > 0) {
              simulatorRef.current.setArmElevation(armAngle);
            }

            // Dynamically fit camera framing to model bounding box & overlay clearance
            fitCameraToModel(model);

            const avatarGeoStats = analyzeSceneGeometry(model);
            const avatarTopoLabel =
              avatarGeoStats.nonManifoldEdges > 0
                ? `Non-Manifold (${avatarGeoStats.nonManifoldEdges} edges)`
                : avatarGeoStats.boundaryEdges === 0
                  ? 'Watertight Manifold (Runtime)'
                  : `Open Manifold (${avatarGeoStats.boundaryEdges} boundary)`;
            const avatarAssetName = assetUrl
              ? assetUrl.split('/').pop() || 'avatar.glb'
              : resolvedAvatarId || 'anny_baseline_male.glb';

            setAvatarMetrics({
              assetName: avatarAssetName,
              meshCount: avatarGeoStats.meshCount,
              vertexCount: avatarGeoStats.vertexCount,
              triangleCount: avatarGeoStats.triangleCount,
              nonManifoldEdges: avatarGeoStats.nonManifoldEdges,
              boundaryEdges: avatarGeoStats.boundaryEdges,
              topologyLabel: avatarTopoLabel,
              validationSource: 'Runtime glTF Geometry Check',
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
  }, [resolvedAvatarId, assetUrl]);

  // Load and overlay 3D Garment Mesh
  useEffect(() => {
    if (!sceneRef.current) return;

    if (!garmentUrl || showGarment === false) {
      if (currentGarmentRef.current) {
        sceneRef.current.remove(currentGarmentRef.current);
        currentGarmentRef.current = null;
      }
      setGarmentMetrics(null);
      setGarmentLoadError(null);
      return;
    }

    let isMounted = true;
    setGarmentMetrics(null);
    setGarmentLoadError(null);
    const loader = new GLTFLoader();
    loader.load(
      garmentUrl,
      (gltf) => {
        if (!isMounted || !sceneRef.current) return;
        if (currentGarmentRef.current) {
          sceneRef.current.remove(currentGarmentRef.current);
        }

        const garment = gltf.scene;
        currentGarmentRef.current = garment;

        const scale = garmentScale || 1.0;
        garment.scale.set(scale, scale, scale);

        if (currentModelRef.current) {
          garment.position.copy(currentModelRef.current.position);
        }

        sceneRef.current.add(garment);

        const gStats = analyzeSceneGeometry(garment);
        const matchedSize = extractGarmentSizeFromUrl(garmentUrl);
        const garmentFile = extractGarmentAssetLabel(garmentUrl, matchedSize, garmentQaReport);

        let qaStatus = 'UNVERIFIED (Runtime Only)';
        let qaSource = 'Runtime glTF Check (No Verified QA Report)';
        if (garmentQaReport) {
          const sizeStatus =
            matchedSize && garmentQaReport.size_variants?.[matchedSize]?.overall_prototype_qa;
          const rawStatus =
            sizeStatus ||
            garmentQaReport.statuses?.overall_prototype_qa ||
            garmentQaReport.overall_status;
          if (rawStatus) {
            qaStatus = String(rawStatus).toUpperCase();
            qaSource = garmentQaReport.validation_source || 'Verified Asset QA Report';
          }
        }
        if (gStats.nonManifoldEdges > 0) {
          qaStatus = `FAILED (${gStats.nonManifoldEdges} Non-Manifold Edges)`;
          qaSource = 'Runtime glTF Edge Incidence Check';
        }

        const garmentTopoLabel =
          gStats.nonManifoldEdges > 0
            ? `Non-Manifold (${gStats.nonManifoldEdges})`
            : gStats.boundaryEdges > 0
              ? `Open-Shell Manifold (${gStats.boundaryEdges} boundary edges)`
              : 'Watertight Manifold (Runtime)';

        setGarmentMetrics({
          assetName: garmentFile,
          meshCount: gStats.meshCount,
          vertexCount: gStats.vertexCount,
          triangleCount: gStats.triangleCount,
          nonManifoldEdges: gStats.nonManifoldEdges,
          boundaryEdges: gStats.boundaryEdges,
          hasTexCoords: gStats.hasTexCoords,
          topologyLabel: garmentTopoLabel,
          qaStatus,
          qaSource,
        });

        // Bind garment to cloth simulator and sync arm angle
        simulatorRef.current.bindGarment(garment);
        if (armAngle > 0) {
          simulatorRef.current.setArmElevation(armAngle);
        }
      },
      undefined,
      (err) => {
        console.warn('Could not load 3D garment mesh:', err);
        if (isMounted) {
          setGarmentMetrics(null);
          setGarmentLoadError(`Prototype/garment asset unavailable (${garmentUrl})`);
        }
      }
    );

    return () => {
      isMounted = false;
    };
  }, [garmentUrl, showGarment, garmentQaReport]);

  // Dynamic arm elevation motion
  useEffect(() => {
    if (simulatorRef.current) {
      simulatorRef.current.setArmElevation(armAngle || 0);
    }
  }, [armAngle]);

  // Dynamic fabric profile update
  useEffect(() => {
    if (simulatorRef.current && fabricProfile) {
      simulatorRef.current.setFabricProfile(fabricProfile);
    }
  }, [fabricProfile]);

  // Dynamic studio background update
  useEffect(() => {
    if (sceneRef.current && studioBackground) {
      sceneRef.current.background = new THREE.Color(studioBackground);
    }
  }, [studioBackground]);

  // Adjust garment scaling dynamically on size changes
  useEffect(() => {
    if (currentGarmentRef.current) {
      const scale = garmentScale || 1.0;
      currentGarmentRef.current.scale.set(scale, scale, scale);
    }
  }, [garmentScale]);

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
    if (currentModelRef.current) {
      fitCameraToModel(currentModelRef.current);
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
        background: studioBackground || '#720e2c',
      }}
    >
      {/* Three.js canvas container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Top-Left: Separated Avatar & Garment Telemetry HUD */}
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
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <span className="badge badge-cyan" style={{ pointerEvents: 'auto' }}>
            <CheckCircle2 size={12} />
            <span>NAVER Anny v0.6.2</span>
          </span>

          {avatarMetrics && (
            <span
              className={`badge ${avatarMetrics.nonManifoldEdges === 0 ? 'badge-emerald' : 'badge-rose'}`}
              style={{ pointerEvents: 'auto' }}
              title={avatarMetrics.validationSource}
            >
              {avatarMetrics.nonManifoldEdges === 0 ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
              <span>{avatarMetrics.topologyLabel}</span>
            </span>
          )}
        </div>

        {avatarMetrics && (
          <div
            data-testid="avatar-metrics"
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              display: 'flex',
              gap: '10px',
              flexWrap: 'wrap',
              pointerEvents: 'auto',
            }}
          >
            <strong style={{ color: 'var(--accent-cyan)' }}>Avatar:</strong>
            <span>
              Meshes: <strong style={{ color: '#ffffff' }}>{avatarMetrics.meshCount}</strong>
            </span>
            <span>
              Vertices: <strong style={{ color: '#ffffff' }}>{avatarMetrics.vertexCount.toLocaleString()}</strong>
            </span>
            <span>
              Triangles: <strong style={{ color: '#ffffff' }}>{avatarMetrics.triangleCount.toLocaleString()}</strong>
            </span>
            <span>
              Source: <strong style={{ color: '#cbd5e1' }}>{avatarMetrics.validationSource}</strong>
            </span>
      </div>
        )}

        {garmentMetrics && (
          <div
            data-testid="garment-metrics"
            style={{
              background: 'rgba(15, 23, 42, 0.88)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(244, 114, 182, 0.45)',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              display: 'flex',
              gap: '10px',
              flexWrap: 'wrap',
              pointerEvents: 'auto',
            }}
          >
            <strong style={{ color: '#f9a8d4' }}>Garment ({garmentMetrics.assetName}):</strong>
            <span>
              Meshes: <strong style={{ color: '#ffffff' }}>{garmentMetrics.meshCount}</strong>
            </span>
            <span>
              Vertices: <strong style={{ color: '#ffffff' }}>{garmentMetrics.vertexCount.toLocaleString()}</strong>
            </span>
            <span>
              Triangles: <strong style={{ color: '#ffffff' }}>{garmentMetrics.triangleCount.toLocaleString()}</strong>
            </span>
            <span>
              Topology: <strong style={{ color: '#cbd5e1' }}>{garmentMetrics.topologyLabel}</strong>
            </span>
            <span>
              QA:{' '}
              <strong style={{ color: garmentMetrics.qaStatus.startsWith('PASS') ? '#34d399' : '#fbbf24' }}>
                {garmentMetrics.qaStatus}
              </strong>{' '}
              <span style={{ color: '#94a3b8' }}>({garmentMetrics.qaSource})</span>
            </span>
      </div>
        )}
        {(garmentUnavailableError || garmentLoadError) && (
          <div
            data-testid="garment-error"
            style={{
              background: 'rgba(127, 29, 29, 0.92)',
              border: '1px solid #f87171',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '11px',
              color: '#fecaca',
              pointerEvents: 'auto',
            }}
          >
            <strong>Garment Unavailable:</strong> {garmentUnavailableError || garmentLoadError}
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
