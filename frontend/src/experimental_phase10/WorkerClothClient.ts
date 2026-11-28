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
import {
  applyArticulatedPoseToRig,
  createPoseRigScratch,
  SimulationLifecycleState,
  SimulationMetrics,
  WeldedClothSolver,
} from './WeldedClothSolver';

export type ClothVisualizationMode = 'normal' | 'strain';

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
  private vizMode: ClothVisualizationMode = 'normal';

  private garmentBindings: {
    mesh: THREE.Mesh;
    vertexToParticle: Int32Array;
    vertCount: number;
    origMatColor?: THREE.Color;
    origVertexColors?: boolean;
  }[] = [];
  private mainBones = new Map<string, THREE.Bone>();
  private mainRestQuats = new Map<string, THREE.Quaternion>();
  private mainRestUpperWorldQuats: { L?: THREE.Quaternion; R?: THREE.Quaternion } = {};
  private poseScratch = createPoseRigScratch();
  private currentPose: ArticulationState = { ...NEUTRAL_POSE };
  private targetPose: ArticulationState = { ...NEUTRAL_POSE };
  private fabricId = 'waffle_knit_240';
  private latestStrain: Float32Array = new Float32Array(0);

  private lastStepSentAt = 0;
  private workerCommMs = 0;
  private latestMetrics: ClientMetrics | null = null;
  private onMetricsCb?: (m: ClientMetrics) => void;
  private onErrorCb?: (msg: string) => void;

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
              const sBuf = 'strainBuffer' in msg ? msg.strainBuffer : undefined;
              const xfer: Transferable[] = sBuf ? [msg.posBuffer, sBuf] : [msg.posBuffer];
              w.postMessage({ type: 'RECYCLE', buffer: msg.posBuffer, strainBuffer: sBuf } as WorkerInMsg, xfer);
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
            const strainArr = new Float32Array(msg.strainBuffer);
            if (this.latestStrain.length !== strainArr.length) {
              this.latestStrain = new Float32Array(strainArr.length);
            }
            this.latestStrain.set(strainArr);
            this.applyPositionsToMainMeshes(posArr);
            this.applyStrainColorsIfEnabled();
            w.postMessage(
              { type: 'RECYCLE', buffer: msg.posBuffer, strainBuffer: msg.strainBuffer } as WorkerInMsg,
              [msg.posBuffer, msg.strainBuffer]
            );

            this.state = msg.metrics.simState;
            this.latestMetrics = { ...msg.metrics, workerMode: 'web_worker', workerCommMs: this.workerCommMs };
            this.onMetricsCb?.(this.latestMetrics);
            return;
          }

          if (msg.type === 'RESET_ACK') {
            this.busy = false;
            const posArr = new Float32Array(msg.posBuffer);
            const strainArr = new Float32Array(msg.strainBuffer);
            if (this.latestStrain.length !== strainArr.length) {
              this.latestStrain = new Float32Array(strainArr.length);
            }
            this.latestStrain.set(strainArr);
            this.applyPositionsToMainMeshes(posArr);
            this.applyStrainColorsIfEnabled();
            w.postMessage(
              { type: 'RECYCLE', buffer: msg.posBuffer, strainBuffer: msg.strainBuffer } as WorkerInMsg,
              [msg.posBuffer, msg.strainBuffer]
            );

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
    this.mainRestUpperWorldQuats = {};
    this.garmentBindings = [];
    avatarRoot.updateMatrixWorld(true);

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
            if (name === 'upperarm01.L') {
              const wq = new THREE.Quaternion();
              b.getWorldQuaternion(wq);
              this.mainRestUpperWorldQuats.L = wq;
            } else if (name === 'upperarm01.R') {
              const wq = new THREE.Quaternion();
              b.getWorldQuaternion(wq);
              this.mainRestUpperWorldQuats.R = wq;
            }
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
      const mat = m.material as THREE.MeshStandardMaterial | undefined;
      this.garmentBindings.push({
        mesh: m,
        vertexToParticle: vToP,
        vertCount: posAttr.count,
        origMatColor: mat?.color ? mat.color.clone() : undefined,
        origVertexColors: Boolean(mat?.vertexColors),
      });
    });
    this.latestStrain = new Float32Array(nextIdx);
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

  private applyPoseToMainSkeleton(pose: ArticulationState): void {
    applyArticulatedPoseToRig(this.mainBones, this.mainRestQuats, this.mainRestUpperWorldQuats, pose, this.poseScratch);
  }

  public setVisualizationMode(mode: ClothVisualizationMode): void {
    this.vizMode = mode;
    for (const b of this.garmentBindings) {
      const mat = b.mesh.material as THREE.MeshStandardMaterial | undefined;
      if (!mat) continue;
      if (mode === 'strain') {
        mat.vertexColors = true;
        if (mat.color) mat.color.setHex(0xffffff);
      } else {
        mat.vertexColors = Boolean(b.origVertexColors);
        if (mat.color && b.origMatColor) mat.color.copy(b.origMatColor);
      }
      mat.needsUpdate = true;
    }
    this.applyStrainColorsIfEnabled();
  }

  private applyStrainColorsIfEnabled(): void {
    if (this.vizMode !== 'strain' || this.latestStrain.length === 0) return;
    // Map simulated relative edge stretch into perceptual fit heatmap colors:
    //   <= -1.5%: relaxed blue  |  ~0%: emerald green  |  ~3%: amber  |  >= 6%: tight red
    for (const b of this.garmentBindings) {
      let colorAttr = b.mesh.geometry.attributes.color as THREE.BufferAttribute | undefined;
      if (!colorAttr || colorAttr.count !== b.vertCount) {
        colorAttr = new THREE.BufferAttribute(new Float32Array(b.vertCount * 3), 3);
        b.mesh.geometry.setAttribute('color', colorAttr);
      }
      for (let i = 0; i < b.vertCount; i++) {
        const s = this.latestStrain[b.vertexToParticle[i]] || 0;
        let r = 0.14, g = 0.72, bl = 0.46; // Comfortable emerald default
        if (s < -0.008) {
          // Relaxed / loose drape -> cool blue
          const t = Math.min(1, (-s - 0.008) / 0.032);
          r = 0.16 - 0.04 * t;
          g = 0.72 - 0.24 * t;
          bl = 0.50 + 0.46 * t;
        } else if (s <= 0.022) {
          // Comfortable -> soft lime-green
          const t = Math.max(0, (s + 0.008) / 0.03);
          r = 0.14 + 0.42 * t;
          g = 0.72 + 0.12 * t;
          bl = 0.46 - 0.24 * t;
        } else if (s <= 0.048) {
          // Fitted/snug amber -> warm orange
          const t = (s - 0.022) / 0.026;
          r = 0.88 + 0.10 * t;
          g = 0.80 - 0.36 * t;
          bl = 0.16 - 0.06 * t;
        } else {
          // High simulated stretch -> tight red
          const t = Math.min(1, (s - 0.048) / 0.035);
          r = 0.96 - 0.06 * t;
          g = 0.36 - 0.24 * t;
          bl = 0.12 + 0.08 * t;
        }
        colorAttr.setXYZ(i, r, g, bl);
      }
      colorAttr.needsUpdate = true;
    }
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
      this.latestStrain = this.fallbackSolver.getStrainBufferCopy(this.latestStrain);
      this.applyStrainColorsIfEnabled();
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
          pose: { ...this.currentPose },
          fabricId: this.fabricId,
        } as WorkerInMsg);
      }
    } else {
      this.fallbackSolver.setFabric(this.fabricId);
      this.fallbackSolver.setExactPose(this.currentPose);
      this.fallbackSolver.step(dtSec);
      this.latestStrain = this.fallbackSolver.getStrainBufferCopy(this.latestStrain);
      this.applyStrainColorsIfEnabled();
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
