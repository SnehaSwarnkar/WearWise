import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import Header from '../pages/Header';
import { ARTICULATED_POSES, ArticulationState, NEUTRAL_POSE } from './ArticulatedPoseLibrary';
import { SIM_FABRICS, SimulationMetrics, WeldedClothSolver } from './WeldedClothSolver';

interface SliderDef {
  key: keyof ArticulationState;
  label: string;
  min: number;
  max: number;
}

const JOINT_SLIDERS: SliderDef[] = [
  { key: 'shoulderElevL', label: 'L Shoulder Elev (Abduct)', min: 0, max: 90 },
  { key: 'shoulderElevR', label: 'R Shoulder Elev (Abduct)', min: 0, max: 90 },
  { key: 'armForwardL', label: 'L Arm Forward Flex', min: 0, max: 80 },
  { key: 'armForwardR', label: 'R Arm Forward Flex', min: 0, max: 80 },
  { key: 'clavicleLift', label: 'Clavicle Shrug', min: 0, max: 20 },
  { key: 'elbowFlexL', label: 'L Elbow Flexion', min: 0, max: 110 },
  { key: 'elbowFlexR', label: 'R Elbow Flexion', min: 0, max: 110 },
  { key: 'forearmTwist', label: 'Forearm Twist', min: -45, max: 45 },
  { key: 'wristFlex', label: 'Wrist Flexion', min: -25, max: 25 },
  { key: 'torsoForwardLean', label: 'Torso Forward Lean', min: -15, max: 30 },
  { key: 'torsoLateralLean', label: 'Torso Lateral Lean', min: -20, max: 20 },
  { key: 'torsoTwist', label: 'Torso Axial Twist', min: -30, max: 30 },
];

export default function Phase10SimPage() {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const solverRef = useRef<WeldedClothSolver>(new WeldedClothSolver());
  const garmentGroupRef = useRef<THREE.Group | null>(null);

  const [activePoseId, setActivePoseId] = useState<string>('P0');
  const [poseState, setPoseState] = useState<ArticulationState>({ ...NEUTRAL_POSE });
  const [fabricId, setFabricId] = useState('waffle_knit_240');
  const [wireframe, setWireframe] = useState(false);
  const [rigInfo, setRigInfo] = useState<{ boneCount: number; hasSkinnedMesh: boolean } | null>(null);
  const [metrics, setMetrics] = useState<SimulationMetrics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#5a0b23');

    const width = container.clientWidth || 860;
    const height = 620;
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.05, 50);
    camera.position.set(0, 1.15, 2.05);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1.05, -0.05);
    controls.update();

    scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
    keyLight.position.set(1.5, 2.5, 2.5);
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xffd6e7, 0.65);
    fillLight.position.set(-1.5, 1.0, -1.5);
    scene.add(fillLight);

    const loader = new GLTFLoader();
    const solver = solverRef.current;
    (window as any).__phase10Solver = solver;

    Promise.all([
      new Promise<any>((res, rej) => loader.load('/experimental_phase10/anny_rigged_male_exp.glb', res, undefined, rej)),
      new Promise<any>((res, rej) => loader.load('/experimental_phase10/TSH-EXP-PHASE10_M.glb', res, undefined, rej)),
    ])
      .then(([avatarGltf, garmentGltf]) => {
        const avatarScene = avatarGltf.scene as THREE.Group;
        const garmentScene = garmentGltf.scene as THREE.Group;
        scene.add(avatarScene);
        scene.add(garmentScene);
        garmentGroupRef.current = garmentScene;

        const rInfo = solver.bindAvatar(avatarScene);
        solver.bindGarment(garmentScene);
        setRigInfo(rInfo);
        setMetrics(solver.getMetrics());
      })
      .catch((err) => {
        setLoadError(err?.message || 'Failed to load Phase 10 experimental assets');
      });

    let rafId = 0;
    let lastTime = performance.now();
    let frameCounter = 0;

    const animate = (now: number) => {
      const dt = Math.min(0.033, Math.max(0.001, (now - lastTime) / 1000));
      lastTime = now;

      solver.step(dt);
      controls.update();
      renderer.render(scene, camera);

      frameCounter++;
      if (frameCounter % 6 === 0) {
        setMetrics(solver.getMetrics());
      }
      rafId = requestAnimationFrame(animate);
    };
    rafId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafId);
      controls.dispose();
      renderer.dispose();
    };
  }, []);

  useEffect(() => {
    solverRef.current.setTargetPose(poseState);
  }, [poseState]);

  useEffect(() => {
    solverRef.current.setFabric(fabricId);
  }, [fabricId]);

  useEffect(() => {
    if (!garmentGroupRef.current) return;
    garmentGroupRef.current.traverse((obj) => {
      const m = obj as THREE.Mesh;
      if (m.isMesh && m.material) {
        const mat = m.material as THREE.MeshStandardMaterial;
        mat.wireframe = wireframe;
      }
    });
  }, [wireframe]);

  const handleSelectPreset = (id: string, state: ArticulationState) => {
    setActivePoseId(id);
    setPoseState({ ...state });
  };

  const handleReset = () => {
    setActivePoseId('P0');
    setPoseState({ ...NEUTRAL_POSE });
    solverRef.current.reset();
    setMetrics(solverRef.current.getMetrics());
  };

  return (
    <div style={{ minHeight: '100vh', background: '#fdfbf7' }}>
      <Header />
      <main style={{ maxWidth: '1320px', margin: '0 auto', padding: '20px 24px' }}>
        <div style={{ marginBottom: '14px' }}>
          <span style={{ fontSize: '11px', fontWeight: 900, letterSpacing: '1px', color: '#be185d' }}>
            EXPERIMENTAL PHASE 10.4–10.8 PROTOTYPE · ISOLATED SANDBOX
          </span>
          <h1 style={{ fontSize: '25px', fontWeight: 900, margin: '4px 0' }}>
            Articulated Anny Rig + Hybrid Anatomical Collision + Welded XPBD Cloth
          </h1>
          <p style={{ fontSize: '13px', color: '#475569', margin: 0 }}>
            Experimental assets (<code>anny_rigged_male_exp.glb</code> + <code>TSH-EXP-PHASE10_M.glb</code>). Protected Rev3 &amp; shopper Try-On remain untouched.
          </p>
        </div>

        {loadError && (
          <div style={{ padding: '12px', background: '#fef2f2', border: '1px solid #ef4444', borderRadius: '8px', color: '#991b1b', marginBottom: '12px' }}>
            {loadError}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1.45fr 1fr', gap: '18px', alignItems: 'start' }}>
          <div>
            <div style={{ border: '2px solid #0f172a', borderRadius: '12px', overflow: 'hidden', background: '#5a0b23' }}>
              <div ref={mountRef} style={{ width: '100%', height: '620px' }} />
            </div>

            {/* Live Measured Telemetry */}
            <div
              data-testid="phase10-telemetry"
              data-metrics={metrics ? JSON.stringify(metrics) : ''}
              style={{
                marginTop: '14px',
                background: '#0f172a',
                color: '#f8fafc',
                borderRadius: '12px',
                padding: '14px 16px',
                fontSize: '12px',
                fontFamily: 'monospace',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '6px 16px',
              }}
            >
              <strong style={{ color: '#d8ff3f', gridColumn: '1 / -1' }}>
                LIVE SIMULATION TELEMETRY ({activePoseId} · {SIM_FABRICS[fabricId]?.name})
              </strong>
              {rigInfo && (
                <div>Rig: SkinnedMesh={String(rigInfo.hasSkinnedMesh)} | Bones={rigInfo.boneCount}</div>
              )}
              {metrics && (
                <>
                  <div>Colliders: {metrics.colliderCapsules} Capsules + {metrics.colliderUpperTris.toLocaleString()} Tris</div>
                  <div>Garment: {metrics.garmentVertices.toLocaleString()} Verts → {metrics.particleCount.toLocaleString()} Welded</div>
                  <div>Constraints: {metrics.constraintCount.toLocaleString()} ({metrics.structuralConstraints} Struct, {metrics.bendingConstraints} Bend)</div>
                  <div>Solve: {metrics.lastSolveMs} ms (Col: {metrics.collisionTimeMs} ms)</div>
                  <div>FPS: {metrics.fps} (Avg {metrics.avgFps}, Min {metrics.minFps}) | P95: {metrics.p95FrameMs} ms</div>
                  <div>Displacement: Max {metrics.maxDisplacementCm} cm | Avg {metrics.avgDisplacementCm} cm</div>
                  <div>Stretch Ratio: Max {metrics.maxStretchRatio} | Mean {metrics.meanStretchRatio} | Comp {metrics.maxCompressionRatio}</div>
                  <div>Bend Dev: Max {metrics.maxBendDeviation} | Mean {metrics.meanBendDeviation} | Res {metrics.constraintResidual} mm</div>
                  <div>Velocity: Max {metrics.maxVelocityMs} m/s | Seam Sep: {metrics.seamSeparationMm} mm</div>
                  <div>Penetration: {metrics.penetratingParticles}/{metrics.particleCount} | Max {metrics.maxPenetrationMm} mm | Mean {metrics.meanPenetrationMm} mm</div>
                  <div>Corrections/Step: {metrics.capsuleCorrections} Cap + {metrics.meshCorrections} Mesh{metrics.heapMB !== null ? ` | Heap: ${metrics.heapMB} MB` : ''}</div>
                </>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Pose Presets P0-P11 */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong style={{ fontSize: '12px' }}>ARTICULATED POSE LIBRARY (P0–P11)</strong>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    type="button"
                    data-testid="wireframe-btn"
                    onClick={() => setWireframe(!wireframe)}
                    style={{ padding: '4px 8px', fontSize: '11px', fontWeight: 700, border: '1px solid #0f172a', borderRadius: '5px', cursor: 'pointer' }}
                  >
                    {wireframe ? 'Solid' : 'Wireframe'}
                  </button>
                  <button
                    type="button"
                    data-testid="reset-pose-btn"
                    onClick={handleReset}
                    style={{ padding: '4px 8px', fontSize: '11px', fontWeight: 700, border: '1px solid #0f172a', borderRadius: '5px', background: '#f1f5f9', cursor: 'pointer' }}
                  >
                    Reset P0
                  </button>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px' }}>
                {ARTICULATED_POSES.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    data-testid={`pose-btn-${p.id}`}
                    title={p.description}
                    onClick={() => handleSelectPreset(p.id, p.state)}
                    style={{
                      padding: '6px 6px',
                      borderRadius: '6px',
                      border: '1.5px solid #0f172a',
                      background: activePoseId === p.id ? '#ff3d9a' : '#f8fafc',
                      color: activePoseId === p.id ? '#fff' : '#0f172a',
                      fontWeight: 800,
                      fontSize: '10.5px',
                      cursor: 'pointer',
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Fabric Selection */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <strong style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>FABRIC MECHANICAL PROFILE</strong>
              <div style={{ display: 'flex', gap: '8px' }}>
                {Object.values(SIM_FABRICS).map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    data-testid={`fabric-btn-${f.id}`}
                    onClick={() => setFabricId(f.id)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '6px',
                      border: '1.5px solid #0f172a',
                      background: fabricId === f.id ? '#d8ff3f' : '#f8fafc',
                      fontWeight: 800,
                      fontSize: '11px',
                      cursor: 'pointer',
                    }}
                  >
                    {f.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Continuous Joint Controls */}
            <div style={{ background: '#fff', border: '2px solid #0f172a', borderRadius: '12px', padding: '14px' }}>
              <strong style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>CONTINUOUS JOINT ROTATION CONTROLS (DEG)</strong>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 12px' }}>
                {JOINT_SLIDERS.map((s) => (
                  <label key={s.key} style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
                      <span>{s.label}</span>
                      <span>{poseState[s.key]}°</span>
                    </span>
                    <input
                      type="range"
                      data-testid={`slider-${s.key}`}
                      min={s.min}
                      max={s.max}
                      step={1}
                      value={poseState[s.key]}
                      onChange={(e) => {
                        setActivePoseId('CUSTOM');
                        setPoseState((prev) => ({ ...prev, [s.key]: Number(e.target.value) }));
                      }}
                    />
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
