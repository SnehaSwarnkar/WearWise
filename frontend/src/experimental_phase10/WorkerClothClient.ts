/**
 * WearWise Phase 10.9 — Main-Thread Simulation Coordinator (Worker + Fallback)
 * ============================================================================
 * - Manages Web Worker lifecycle, zero-copy transferable buffer recycling,
 *   monotonic epoch fencing for deterministic reset synchronization, and
 *   automatic main-thread fallback if Worker init/runtime fails.
 */

import * as THREE from 'three';
import { ArticulationState, NEUTRAL_POSE } from './ArticulatedPoseLibrary';
import {
  SerializedAvatarInit,
  SerializedGarmentMesh,
  WorkerInMsg,
  WorkerOutMsg,
} from './clothWorker';
import { SimulationLifecycleState, SimulationMetrics, WeldedClothSolver } from './WeldedClothSolver';

export interface ClientMetrics extends SimulationMetrics {
  workerMode: 'web_worker' | 'main_thread_fallback';
  workerCommMs: number;
}

export class WorkerClothClient {
  private worker: Worker | null = null;
  private fallbackSolver = new WeldedClothSolver();
  private useWorker = false;
  private busy = false;
  private epoch = 0;
  private state: SimulationLifecycleState = 'IDLE';

  private garmentBindings: { mesh: THREE.Mesh; vertexToParticle: Int32Array; vertCount: number }[] = [];
  private mainBones = new Map<string, THREE.Bone>();
  private mainRestQuats = new Map<string, THREE.Quaternion>();
  private currentPose: ArticulationState = { ...NEUTRAL_POSE };
  private targetPose: ArticulationState = { ...NEUTRAL_POSE };
  private fabricId = 'waffle_knit_240';

  private lastStepSentAt = 0;
  private workerCommMs = 0;
  private latestMetrics: ClientMetrics | null = null;
  private onMetricsCb?: (m: ClientMetrics) => void;
  private onErrorCb?: (msg: string) => void;

  private tmpParentQ = new THREE.Quaternion();
  private tmpInvParentQ = new THREE.Quaternion();
  private tmpQ = new THREE.Quaternion();
  private tmpLocalQ = new THREE.Quaternion();

  public setCallbacks(onMetrics: (m: ClientMetrics) => void, onError?: (msg: string) => void): void {
    this.onMetricsCb = onMetrics;
    this.onErrorCb = onError;
  }

  public init(avatarRoot: THREE.Object3D, garmentRoot: THREE.Object3D): Promise<{ boneCount: number; hasSkinnedMesh: boolean }> {
    this.state = 'INITIALIZING';
    this.epoch++;
    const initEpoch = this.epoch;

    // Always bind main-thread skeleton for visual Three.js SkinnedMesh rendering
    this.bindMainThreadSkeletonAndGarment(avatarRoot, garmentRoot);

    // Also keep fallback solver ready
    const rigInfo = this.fallbackSolver.bindAvatar(avatarRoot);
    this.fallbackSolver.bindGarment(garmentRoot);

    if (typeof Worker === 'undefined') {
      this.useWorker = false;
      this.state = 'STABLE';
      this.latestMetrics = { ...this.fallbackSolver.getMetrics(), workerMode: 'main_thread_fallback', workerCommMs: 0 };
      this.onMetricsCb?.(this.latestMetrics);
      return Promise.resolve(rigInfo);
    }

    return new Promise((resolve) => {
      try {
        const w = new Worker(new URL('./clothWorker.ts', import.meta.url), { type: 'module' });
        this.worker = w;
        const avatarData = this.serializeAvatar(avatarRoot);
        const garmentMeshes = this.serializeGarment(garmentRoot);

        if (!avatarData) {
          throw new Error('No SkinnedMesh found on avatar');
        }

        const timeoutId = setTimeout(() => {
          if (this.state === 'INITIALIZING') {
            this.fallbackToMainThread('Worker init timeout', rigInfo, resolve);
          }
        }, 4000);

        w.onmessage = (ev: MessageEvent<WorkerOutMsg>) => {
          const msg = ev.data;
          if (msg.epoch !== this.epoch) {
            // Recycle stale buffers cleanly without mutating state
            if ('posBuffer' in msg && msg.posBuffer) {
              w.postMessage({ type: 'RECYCLE', buffer: msg.posBuffer } as WorkerInMsg, [msg.posBuffer]);
            }
            return;
          }

          if (msg.type === 'INIT_OK') {
            clearTimeout(timeoutId);
            this.useWorker = true;
            this.state = 'STABLE';
            this.latestMetrics = { ...msg.metrics, simState: 'STABLE', workerMode: 'web_worker', workerCommMs: 0 };
            this.onMetricsCb?.(this.latestMetrics);
            resolve(msg.rigInfo);
            return;
          }

          if (msg.type === 'FRAME') {
            this.busy = false;
            const rtt = Math.max(0, performance.now() - this.lastStepSentAt - msg.workerSolveMs);
            this.workerCommMs = Number(rtt.toFixed(2));
            const posArr = new Float32Array(msg.posBuffer);
            this.applyPositionsToMainMeshes(posArr);
            w.postMessage({ type: 'RECYCLE', buffer: msg.posBuffer } as WorkerInMsg, [msg.posBuffer]);

            this.state = msg.metrics.simState;
            this.latestMetrics = { ...msg.metrics, workerMode: 'web_worker', workerCommMs: this.workerCommMs };
            this.onMetricsCb?.(this.latestMetrics);
            return;
          }

          if (msg.type === 'RESET_ACK') {
            this.busy = false;
            const posArr = new Float32Array(msg.posBuffer);
            this.applyPositionsToMainMeshes(posArr);
            w.postMessage({ type: 'RECYCLE', buffer: msg.posBuffer } as WorkerInMsg, [msg.posBuffer]);

            this.state = 'STABLE';
            this.latestMetrics = {
              ...msg.metrics,
              simState: 'STABLE',
              resetEpoch: this.epoch,
              workerMode: 'web_worker',
              workerCommMs: 0,
            };
            this.onMetricsCb?.(this.latestMetrics);
            return;
          }

          if (msg.type === 'ERROR') {
            clearTimeout(timeoutId);
            this.fallbackToMainThread(msg.message, rigInfo, resolve);
          }
        };

        w.onerror = (err) => {
          clearTimeout(timeoutId);
          this.fallbackToMainThread(err.message || 'Worker runtime error', rigInfo, resolve);
        };

        const transferables: Transferable[] = [
          avatarData.positions.buffer,
          avatarData.indices.buffer,
          avatarData.skinIndices.buffer,
          avatarData.skinWeights.buffer,
          avatarData.boneLocalMatrices.buffer,
          avatarData.inverseBindMatrices.buffer,
          ...garmentMeshes.flatMap((g) => [g.positions.buffer, g.indices.buffer]),
        ];

        w.postMessage({ type: 'INIT', epoch: initEpoch, avatar: avatarData, garmentMeshes } as WorkerInMsg, transferables);
      } catch (e: any) {
        this.fallbackToMainThread(e?.message || 'Worker unsupported', rigInfo, resolve);
      }
    });
  }

  private fallbackToMainThread(
    reason: string,
    rigInfo: { boneCount: number; hasSkinnedMesh: boolean },
    resolve?: (v: { boneCount: number; hasSkinnedMesh: boolean }) => void
  ): void {
    this.worker?.terminate();
    this.worker = null;
    this.useWorker = false;
    this.busy = false;
    this.state = 'STABLE';
    this.onErrorCb?.(`Worker fallback active: ${reason}`);
    this.latestMetrics = { ...this.fallbackSolver.getMetrics(), workerMode: 'main_thread_fallback', workerCommMs: 0 };
    this.onMetricsCb?.(this.latestMetrics);
    resolve?.(rigInfo);
  }

  private bindMainThreadSkeletonAndGarment(avatarRoot: THREE.Object3D, garmentRoot: THREE.Object3D): void {
    this.mainBones.clear();
    this.mainRestQuats.clear();
    this.garmentBindings = [];

    avatarRoot.traverse((obj) => {
      const sk = obj as THREE.SkinnedMesh;
      if (sk.isSkinnedMesh && sk.skeleton) {
        const wanted = [
          'spine04', 'spine03', 'spine02', 'spine01',
          'clavicle.L', 'clavicle.R',
          'shoulder01.L', 'shoulder01.R',
          'upperarm01.L', 'upperarm01.R',
          'lowerarm01.L', 'lowerarm01.R',
          'lowerarm02.L', 'lowerarm02.R',
          'wrist.L', 'wrist.R',
        ];
        for (const name of wanted) {
          const clean = name.replace(/\./g, '');
          const b = sk.skeleton.bones.find((bn) => bn.name === name || bn.name === clean);
          if (b) {
            this.mainBones.set(name, b);
            this.mainRestQuats.set(name, b.quaternion.clone());
          }
        }
      }
    });

    const spatialMap = new Map<string, number>();
    let nextIdx = 0;
    const quantKey = (x: number, y: number, z: number) =>
      `${Math.round(x * 2000)}_${Math.round(y * 2000)}_${Math.round(z * 2000)}`;

    garmentRoot.traverse((obj) => {
      const m = obj as THREE.Mesh;
      if (!m.isMesh) return;
      const posAttr = m.geometry.attributes.position;
      if (!posAttr) return;
      const vToP = new Int32Array(posAttr.count);
      for (let i = 0; i < posAttr.count; i++) {
        const k = quantKey(posAttr.getX(i), posAttr.getY(i), posAttr.getZ(i));
        let p = spatialMap.get(k);
        if (p === undefined) {
          p = nextIdx++;
          spatialMap.set(k, p);
        }
        vToP[i] = p;
      }
      this.garmentBindings.push({ mesh: m, vertexToParticle: vToP, vertCount: posAttr.count });
    });
  }

  private serializeAvatar(avatarRoot: THREE.Object3D): SerializedAvatarInit | null {
    let skMesh: THREE.SkinnedMesh | null = null;
    avatarRoot.traverse((obj) => {
      if ((obj as THREE.SkinnedMesh).isSkinnedMesh && !skMesh) {
        skMesh = obj as THREE.SkinnedMesh;
      }
    });
    if (!skMesh) return null;
    const sk = (skMesh as THREE.SkinnedMesh).skeleton;
    const geom = (skMesh as THREE.SkinnedMesh).geometry;

    const pos = new Float32Array(geom.attributes.position.array as ArrayLike<number>);
    const idx = new Uint32Array(geom.index!.array as ArrayLike<number>);
    const skinIndices = new Uint16Array(geom.attributes.skinIndex.array as ArrayLike<number>);
    const skinWeights = new Float32Array(geom.attributes.skinWeight.array as ArrayLike<number>);

    const boneNames = sk.bones.map((b) => b.name);
    const boneParents = sk.bones.map((b) => (b.parent && (b.parent as THREE.Bone).isBone ? sk.bones.indexOf(b.parent as THREE.Bone) : -1));
    const boneLocalMatrices = new Float32Array(sk.bones.length * 16);
    const inverseBindMatrices = new Float32Array(sk.bones.length * 16);
    for (let i = 0; i < sk.bones.length; i++) {
      sk.bones[i].updateMatrix();
      sk.bones[i].matrix.toArray(boneLocalMatrices, i * 16);
      if (sk.boneInverses[i]) {
        sk.boneInverses[i].toArray(inverseBindMatrices, i * 16);
      }
    }

    return { positions: pos, indices: idx, skinIndices, skinWeights, boneNames, boneParents, boneLocalMatrices, inverseBindMatrices };
  }

  private serializeGarment(garmentRoot: THREE.Object3D): SerializedGarmentMesh[] {
    const out: SerializedGarmentMesh[] = [];
    garmentRoot.traverse((obj) => {
      const m = obj as THREE.Mesh;
      if (!m.isMesh || !m.geometry.attributes.position || !m.geometry.index) return;
      out.push({
        name: m.name,
        positions: new Float32Array(m.geometry.attributes.position.array as ArrayLike<number>),
        indices: new Uint32Array(m.geometry.index.array as ArrayLike<number>),
      });
    });
    return out;
  }

  private applyPositionsToMainMeshes(posArr: Float32Array): void {
    for (const b of this.garmentBindings) {
      const attr = b.mesh.geometry.attributes.position;
      for (let i = 0; i < b.vertCount; i++) {
        const p = b.vertexToParticle[i] * 3;
        attr.setXYZ(i, posArr[p], posArr[p + 1], posArr[p + 2]);
      }
      attr.needsUpdate = true;
      b.mesh.geometry.computeVertexNormals();
    }
  }

  private rotateMainBoneWorldAxis(boneName: string, axis: THREE.Vector3, angleDeg: number, accumulate = false): void {
    const bone = this.mainBones.get(boneName);
    const restQ = this.mainRestQuats.get(boneName);
    if (!bone || !restQ) return;
    if (!accumulate) bone.quaternion.copy(restQ);
    if (Math.abs(angleDeg) < 1e-4) {
      bone.updateMatrixWorld(true);
      return;
    }
    const rad = (angleDeg * Math.PI) / 180.0;
    if (bone.parent) {
      bone.parent.updateMatrixWorld(true);
      bone.parent.getWorldQuaternion(this.tmpParentQ);
      this.tmpInvParentQ.copy(this.tmpParentQ).invert();
      this.tmpQ.setFromAxisAngle(axis, rad);
      this.tmpLocalQ.copy(this.tmpInvParentQ).multiply(this.tmpQ).multiply(this.tmpParentQ);
      bone.quaternion.premultiply(this.tmpLocalQ);
    }
    bone.updateMatrixWorld(true);
  }

  private applyPoseToMainSkeleton(pose: ArticulationState): void {
    const axisX = new THREE.Vector3(1, 0, 0);
    const axisY = new THREE.Vector3(0, 1, 0);
    const axisZ = new THREE.Vector3(0, 0, 1);

    const spineNames = ['spine04', 'spine03', 'spine02', 'spine01'];
    for (const s of spineNames) {
      this.rotateMainBoneWorldAxis(s, axisX, pose.torsoForwardLean / 4, false);
      this.rotateMainBoneWorldAxis(s, axisZ, -pose.torsoLateralLean / 4, true);
      this.rotateMainBoneWorldAxis(s, axisY, pose.torsoTwist / 4, true);
    }
    this.rotateMainBoneWorldAxis('clavicle.L', axisZ, pose.clavicleLift, false);
    this.rotateMainBoneWorldAxis('clavicle.R', axisZ, -pose.clavicleLift, false);
    this.rotateMainBoneWorldAxis('upperarm01.L', axisZ, pose.shoulderElevL, false);
    this.rotateMainBoneWorldAxis('upperarm01.L', axisX, -pose.armForwardL, true);
    this.rotateMainBoneWorldAxis('upperarm01.R', axisZ, -pose.shoulderElevR, false);
    this.rotateMainBoneWorldAxis('upperarm01.R', axisX, -pose.armForwardR, true);
    this.rotateMainBoneWorldAxis('lowerarm01.L', axisX, -pose.elbowFlexL, false);
    this.rotateMainBoneWorldAxis('lowerarm01.R', axisX, -pose.elbowFlexR, false);

    const fL = this.mainBones.get('lowerarm02.L'), rFL = this.mainRestQuats.get('lowerarm02.L');
    if (fL && rFL) { fL.quaternion.copy(rFL).multiply(this.tmpQ.setFromAxisAngle(axisY, (pose.forearmTwist * Math.PI) / 180)); fL.updateMatrixWorld(true); }
    const fR = this.mainBones.get('lowerarm02.R'), rFR = this.mainRestQuats.get('lowerarm02.R');
    if (fR && rFR) { fR.quaternion.copy(rFR).multiply(this.tmpQ.setFromAxisAngle(axisY, (-pose.forearmTwist * Math.PI) / 180)); fR.updateMatrixWorld(true); }
    const wL = this.mainBones.get('wrist.L'), rWL = this.mainRestQuats.get('wrist.L');
    if (wL && rWL) { wL.quaternion.copy(rWL).multiply(this.tmpQ.setFromAxisAngle(axisX, (pose.wristFlex * Math.PI) / 180)); wL.updateMatrixWorld(true); }
    const wR = this.mainBones.get('wrist.R'), rWR = this.mainRestQuats.get('wrist.R');
    if (wR && rWR) { wR.quaternion.copy(rWR).multiply(this.tmpQ.setFromAxisAngle(axisX, (pose.wristFlex * Math.PI) / 180)); wR.updateMatrixWorld(true); }
  }

  public setTargetPose(pose: Partial<ArticulationState>): void {
    this.targetPose = { ...this.targetPose, ...pose };
  }

  public setFabric(fabricId: string): void {
    this.fabricId = fabricId;
  }

  public reset(): void {
    this.state = 'RESETTING';
    this.epoch++;
    this.targetPose = { ...NEUTRAL_POSE };
    this.currentPose = { ...NEUTRAL_POSE };
    this.applyPoseToMainSkeleton(this.currentPose);

    if (this.useWorker && this.worker) {
      this.busy = true;
      this.worker.postMessage({ type: 'RESET', epoch: this.epoch } as WorkerInMsg);
    } else {
      this.fallbackSolver.reset();
      this.state = 'STABLE';
      this.latestMetrics = { ...this.fallbackSolver.getMetrics(), simState: 'STABLE', resetEpoch: this.epoch, workerMode: 'main_thread_fallback', workerCommMs: 0 };
      this.onMetricsCb?.(this.latestMetrics);
    }
  }

  public step(dtSec: number): void {
    if (this.state === 'IDLE' || this.state === 'INITIALIZING' || this.state === 'RESETTING') return;

    const lerpFactor = Math.min(1, dtSec * 8.5);
    (Object.keys(this.currentPose) as (keyof ArticulationState)[]).forEach((k) => {
      const diff = this.targetPose[k] - this.currentPose[k];
      this.currentPose[k] += Math.abs(diff) < 0.08 ? diff : diff * lerpFactor;
    });
    this.applyPoseToMainSkeleton(this.currentPose);

    if (this.useWorker && this.worker) {
      if (!this.busy) {
        this.busy = true;
        this.lastStepSentAt = performance.now();
        this.worker.postMessage({
          type: 'STEP',
          epoch: this.epoch,
          dtSec,
          pose: this.targetPose,
          fabricId: this.fabricId,
        } as WorkerInMsg);
      }
    } else {
      this.fallbackSolver.setFabric(this.fabricId);
      this.fallbackSolver.setTargetPose(this.targetPose);
      this.fallbackSolver.step(dtSec);
      this.latestMetrics = { ...this.fallbackSolver.getMetrics(), workerMode: 'main_thread_fallback', workerCommMs: 0 };
    }
  }

  public getMetrics(): ClientMetrics | null {
    return this.latestMetrics;
  }

  public dispose(): void {
    this.worker?.terminate();
    this.worker = null;
  }
}
