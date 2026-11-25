import { describe, it, expect } from 'vitest';
import * as THREE from 'three';
import { WeldedClothSolver } from '../WeldedClothSolver';
import { ARTICULATED_POSES } from '../ArticulatedPoseLibrary';

function buildMockRiggedAvatar(): THREE.Group {
  const group = new THREE.Group();
  const root = new THREE.Bone();
  root.name = 'root';
  const spine02 = new THREE.Bone();
  spine02.name = 'spine02';
  spine02.position.set(0, 1.03, -0.14);
  root.add(spine02);

  const spine01 = new THREE.Bone();
  spine01.name = 'spine01';
  spine01.position.set(0, 0.12, -0.02);
  spine02.add(spine01);

  const clavL = new THREE.Bone();
  clavL.name = 'clavicleL'; // Tests dot-stripped GLTFLoader name matching
  clavL.position.set(0.02, 0.11, 0.08);
  spine01.add(clavL);

  const upL = new THREE.Bone();
  upL.name = 'upperarm01L';
  upL.position.set(0.14, -0.03, -0.01);
  clavL.add(upL);

  const lowL = new THREE.Bone();
  lowL.name = 'lowerarm01L';
  lowL.position.set(0.16, -0.18, 0.0);
  upL.add(lowL);

  const upR = new THREE.Bone();
  upR.name = 'upperarm01.R'; // Tests dotted name matching
  upR.position.set(-0.16, 0.08, 0.07);
  spine01.add(upR);

  const geom = new THREE.BoxGeometry(0.3, 0.4, 0.2);
  geom.translate(0, 1.05, -0.1);
  const posCount = geom.attributes.position.count;
  const skinIdx = new Uint16Array(posCount * 4);
  const skinWgt = new Float32Array(posCount * 4);
  for (let i = 0; i < posCount; i++) {
    skinIdx[i * 4] = 1; // spine02
    skinWgt[i * 4] = 1.0;
  }
  geom.setAttribute('skinIndex', new THREE.BufferAttribute(skinIdx, 4));
  geom.setAttribute('skinWeight', new THREE.BufferAttribute(skinWgt, 4));

  const skMesh = new THREE.SkinnedMesh(geom, new THREE.MeshBasicMaterial());
  const skeleton = new THREE.Skeleton([root, spine02, spine01, clavL, upL, lowL, upR]);
  skMesh.add(root);
  skMesh.bind(skeleton);
  group.add(skMesh);
  return group;
}

function buildMockTwoPanelGarment(): THREE.Group {
  const group = new THREE.Group();

  // Panel 1: Torso front quad
  const g1 = new THREE.BufferGeometry();
  g1.setAttribute(
    'position',
    new THREE.Float32BufferAttribute([
      -0.15, 0.90, 0.05,
       0.15, 0.90, 0.05,
       0.15, 1.25, 0.05,
      -0.15, 1.25, 0.05,
    ], 3)
  );
  g1.setIndex([0, 1, 2, 0, 2, 3]);
  const m1 = new THREE.Mesh(g1, new THREE.MeshBasicMaterial());
  m1.name = 'PANEL-FRONT-TORSO';

  // Panel 2: Left sleeve sharing coincident seam vertices at x=0.15, y=1.25, z=0.05
  const g2 = new THREE.BufferGeometry();
  g2.setAttribute(
    'position',
    new THREE.Float32BufferAttribute([
      0.15, 0.90, 0.05,
      0.32, 1.05, 0.05,
      0.15, 1.25, 0.05,
    ], 3)
  );
  g2.setIndex([0, 1, 2]);
  const m2 = new THREE.Mesh(g2, new THREE.MeshBasicMaterial());
  m2.name = 'PANEL-SLEEVE-L';

  // Panel 3: Collar sharing top edge
  const g3 = new THREE.BufferGeometry();
  g3.setAttribute(
    'position',
    new THREE.Float32BufferAttribute([
      -0.15, 1.25, 0.05,
       0.15, 1.25, 0.05,
       0.00, 1.32, 0.05,
    ], 3)
  );
  g3.setIndex([0, 1, 2]);
  const m3 = new THREE.Mesh(g3, new THREE.MeshBasicMaterial());
  m3.name = 'PANEL-COLLAR-RIB';

  group.add(m1, m2, m3);
  return group;
}

describe('WeldedClothSolver (Phase 10.4-10.7)', () => {
  it('welds coincident seam vertices across multiple panels and builds structural + bending constraints', () => {
    const solver = new WeldedClothSolver();
    const avatar = buildMockRiggedAvatar();
    const garment = buildMockTwoPanelGarment();

    const rig = solver.bindAvatar(avatar);
    expect(rig.hasSkinnedMesh).toBe(true);
    expect(rig.boneCount).toBe(7);

    solver.bindGarment(garment);
    const m = solver.getMetrics();
    expect(m.garmentVertices).toBe(10); // 4 + 3 + 3
    expect(m.particleCount).toBe(6); // 4 seam vertices welded
    expect(m.structuralConstraints).toBeGreaterThan(0);
    expect(m.bendingConstraints).toBeGreaterThan(0);
    expect(m.seamSeparationMm).toBe(0);
  });

  it('articulates skeleton bones across pose transitions and recovers cleanly on reset', () => {
    const solver = new WeldedClothSolver();
    const avatar = buildMockRiggedAvatar();
    const garment = buildMockTwoPanelGarment();
    solver.bindAvatar(avatar);
    solver.bindGarment(garment);

    const p3 = ARTICULATED_POSES.find((p) => p.id === 'P3')!;
    solver.setTargetPose(p3.state);
    for (let i = 0; i < 30; i++) {
      solver.step(1 / 60);
    }
    const elevated = solver.getMetrics();
    expect(elevated.maxDisplacementCm).toBeGreaterThan(0.5);
    expect(Number.isFinite(elevated.maxStretchRatio)).toBe(true);
    expect(elevated.seamSeparationMm).toBe(0);

    solver.reset();
    const afterReset = solver.getMetrics();
    expect(afterReset.maxDisplacementCm).toBe(0);
  });

  it('produces distinct mechanical metrics between Waffle Knit (240 GSM) and Structured Poplin (140 GSM)', () => {
    const runWithFabric = (fabId: string) => {
      const solver = new WeldedClothSolver();
      solver.bindAvatar(buildMockRiggedAvatar());
      solver.bindGarment(buildMockTwoPanelGarment());
      solver.setFabric(fabId);
      const p11 = ARTICULATED_POSES.find((p) => p.id === 'P11')!;
      solver.setTargetPose(p11.state);
      for (let i = 0; i < 40; i++) solver.step(1 / 60);
      return solver.getMetrics();
    };

    const knit = runWithFabric('waffle_knit_240');
    const poplin = runWithFabric('rigid_poplin_140');
    expect(knit.maxDisplacementCm).not.toBe(poplin.maxDisplacementCm);
    expect(knit.maxStretchRatio).toBeGreaterThanOrEqual(poplin.maxStretchRatio * 0.99);
  });
});
