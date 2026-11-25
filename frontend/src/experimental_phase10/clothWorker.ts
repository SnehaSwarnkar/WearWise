/**
 * WearWise Phase 10.9 — Off-Thread XPBD + Anatomical Collision Web Worker
 * ========================================================================
 * Runs WeldedClothSolver + AnatomicalCollider off the main UI/render thread
 * using Transferable ArrayBuffer ping-pong (no SharedArrayBuffer COOP/COEP
 * header dependency) and monotonic reset-epoch fencing.
 */

import * as THREE from 'three';
import { ArticulationState } from './ArticulatedPoseLibrary';
import { SimulationMetrics, WeldedClothSolver } from './WeldedClothSolver';

export interface SerializedAvatarInit {
  positions: Float32Array;
  indices: Uint32Array;
  skinIndices: Uint16Array;
  skinWeights: Float32Array;
  boneNames: string[];
  boneParents: number[];
  boneLocalMatrices: Float32Array; // 16 floats per bone
  inverseBindMatrices: Float32Array; // 16 floats per bone
}

export interface SerializedGarmentMesh {
  name: string;
  positions: Float32Array;
  indices: Uint32Array;
}

export type WorkerInMsg =
  | { type: 'INIT'; epoch: number; avatar: SerializedAvatarInit; garmentMeshes: SerializedGarmentMesh[] }
  | { type: 'STEP'; epoch: number; dtSec: number; pose: ArticulationState; fabricId: string }
  | { type: 'RESET'; epoch: number }
  | { type: 'RECYCLE'; buffer: ArrayBuffer };

export type WorkerOutMsg =
  | { type: 'INIT_OK'; epoch: number; rigInfo: { boneCount: number; hasSkinnedMesh: boolean }; metrics: SimulationMetrics }
  | { type: 'FRAME'; epoch: number; posBuffer: ArrayBuffer; metrics: SimulationMetrics; workerSolveMs: number }
  | { type: 'RESET_ACK'; epoch: number; posBuffer: ArrayBuffer; metrics: SimulationMetrics }
  | { type: 'ERROR'; epoch: number; message: string };

const solver = new WeldedClothSolver();
let recycledBuffer: Float32Array | undefined;
let initialized = false;

function buildWorkerAvatar(data: SerializedAvatarInit): THREE.Group {
  const group = new THREE.Group();
  const bones: THREE.Bone[] = [];
  const mat = new THREE.Matrix4();

  for (let i = 0; i < data.boneNames.length; i++) {
    const b = new THREE.Bone();
    b.name = data.boneNames[i];
    mat.fromArray(data.boneLocalMatrices, i * 16);
    mat.decompose(b.position, b.quaternion, b.scale);
    bones.push(b);
  }

  const rootBones: THREE.Bone[] = [];
  for (let i = 0; i < bones.length; i++) {
    const p = data.boneParents[i];
    if (p >= 0 && p < bones.length) {
      bones[p].add(bones[i]);
    } else {
      rootBones.push(bones[i]);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(data.positions, 3));
  geom.setAttribute('skinIndex', new THREE.BufferAttribute(data.skinIndices, 4));
  geom.setAttribute('skinWeight', new THREE.BufferAttribute(data.skinWeights, 4));
  geom.setIndex(new THREE.BufferAttribute(data.indices, 1));

  const ibms: THREE.Matrix4[] = [];
  for (let i = 0; i < bones.length; i++) {
    const m = new THREE.Matrix4().fromArray(data.inverseBindMatrices, i * 16);
    ibms.push(m);
  }

  const skeleton = new THREE.Skeleton(bones, ibms);
  const skMesh = new THREE.SkinnedMesh(geom, new THREE.MeshBasicMaterial());
  for (const rb of rootBones) skMesh.add(rb);
  skMesh.bind(skeleton);
  group.add(skMesh);
  group.updateMatrixWorld(true);
  return group;
}

function buildWorkerGarment(meshes: SerializedGarmentMesh[]): THREE.Group {
  const group = new THREE.Group();
  for (const m of meshes) {
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(m.positions, 3));
    geom.setIndex(new THREE.BufferAttribute(m.indices, 1));
    const mesh = new THREE.Mesh(geom, new THREE.MeshBasicMaterial());
    mesh.name = m.name;
    group.add(mesh);
  }
  return group;
}

self.onmessage = (ev: MessageEvent<WorkerInMsg>) => {
  const msg = ev.data;
  try {
    if (msg.type === 'RECYCLE') {
      recycledBuffer = new Float32Array(msg.buffer);
      return;
    }

    if (msg.type === 'INIT') {
      const av = buildWorkerAvatar(msg.avatar);
      const gm = buildWorkerGarment(msg.garmentMeshes);
      const rigInfo = solver.bindAvatar(av);
      solver.bindGarment(gm);
      initialized = true;
      const metrics = solver.getMetrics();
      (self as unknown as Worker).postMessage({ type: 'INIT_OK', epoch: msg.epoch, rigInfo, metrics } as WorkerOutMsg);
      return;
    }

    if (!initialized) return;

    if (msg.type === 'RESET') {
      solver.reset();
      const outArr = solver.getParticleBufferCopy(recycledBuffer);
      recycledBuffer = undefined;
      const metrics = solver.getMetrics();
      (self as unknown as Worker).postMessage(
        { type: 'RESET_ACK', epoch: msg.epoch, posBuffer: outArr.buffer, metrics } as WorkerOutMsg,
        [outArr.buffer]
      );
      return;
    }

    if (msg.type === 'STEP') {
      const t0 = performance.now();
      solver.setFabric(msg.fabricId);
      solver.setTargetPose(msg.pose);
      solver.step(msg.dtSec);
      const workerSolveMs = performance.now() - t0;
      const outArr = solver.getParticleBufferCopy(recycledBuffer);
      recycledBuffer = undefined;
      const metrics = solver.getMetrics();
      (self as unknown as Worker).postMessage(
        { type: 'FRAME', epoch: msg.epoch, posBuffer: outArr.buffer, metrics, workerSolveMs } as WorkerOutMsg,
        [outArr.buffer]
      );
    }
  } catch (err: any) {
    (self as unknown as Worker).postMessage({
      type: 'ERROR',
      epoch: 'epoch' in msg ? msg.epoch : 0,
      message: err?.message || String(err),
    } as WorkerOutMsg);
  }
};
