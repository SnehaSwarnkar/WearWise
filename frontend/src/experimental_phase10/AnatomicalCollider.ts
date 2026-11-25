/**
 * WearWise Phase 10.4 — Hybrid Anatomical Collision System
 * ========================================================
 * Combines:
 * 1. Live bone-driven anatomical capsule hierarchy (waist, chest L/R, neck,
 *    clavicle/deltoid L/R, upperarm L/R, forearm L/R) to prevent tunneling.
 * 2. CPU-skinned upper-body Anny triangle mesh + flat 3D spatial hash
 *    broad-phase for accurate pectoral, shoulder, axillary, back & neck contact.
 * 3. Zero-allocation typed-array reuse for 60 FPS browser execution.
 */

import * as THREE from 'three';

export interface CapsuleCollider {
  name: string;
  a: THREE.Vector3;
  b: THREE.Vector3;
  radius: number;
}

export interface PenetrationReport {
  totalParticles: number;
  penetratingCount: number;
  maxPenetrationMm: number;
  meanPenetrationMm: number;
}

export interface CollisionStepStats {
  capsuleCorrections: number;
  meshCorrections: number;
  tunnelingIncidents: number;
  collisionTimeMs: number;
}

const TABLE_SIZE = 4096; // Power of 2 for fast bitmasking
const CELL_SIZE = 0.055; // 5.5 cm spatial hash cell

export class AnatomicalCollider {
  private skeleton: THREE.Skeleton | null = null;
  private bindMatrix = new THREE.Matrix4();
  private bindMatrixInverse = new THREE.Matrix4();

  // Bone references for anatomical capsules
  private bPelvisL: THREE.Bone | null = null;
  private bPelvisR: THREE.Bone | null = null;
  private bSpine05: THREE.Bone | null = null;
  private bSpine03: THREE.Bone | null = null;
  private bSpine02: THREE.Bone | null = null;
  private bSpine01: THREE.Bone | null = null;
  private bNeck01: THREE.Bone | null = null;
  private bNeck03: THREE.Bone | null = null;
  private bClavL: THREE.Bone | null = null;
  private bClavR: THREE.Bone | null = null;
  private bShoulderL: THREE.Bone | null = null;
  private bShoulderR: THREE.Bone | null = null;
  private bUpperL: THREE.Bone | null = null;
  private bUpperR: THREE.Bone | null = null;
  private bLowerL: THREE.Bone | null = null;
  private bLowerR: THREE.Bone | null = null;
  private bWristL: THREE.Bone | null = null;
  private bWristR: THREE.Bone | null = null;

  private capsules: CapsuleCollider[] = [];

  // Upper-body skinned mesh subset for narrow-phase triangle collision
  private upperVertCount = 0;
  private upperTriCount = 0;
  private restPos!: Float32Array;
  private skinJoints!: Uint16Array;
  private skinWeights!: Float32Array;
  private skinnedPos!: Float32Array;
  private triIndices!: Uint32Array;
  private triNormals!: Float32Array;
  private triMinX!: Float32Array;
  private triMinY!: Float32Array;
  private triMinZ!: Float32Array;
  private triMaxX!: Float32Array;
  private triMaxY!: Float32Array;
  private triMaxZ!: Float32Array;

  // Flat spatial hash (head[hash] -> entryIdx, next[entryIdx], triId[entryIdx])
  private hashHead = new Int32Array(TABLE_SIZE);
  private entryTri = new Int32Array(65536);
  private entryNext = new Int32Array(65536);
  private entryCount = 0;
  private triVisited = new Uint32Array(0);
  private visitStamp = 1;

  private tmpA = new THREE.Vector3();
  private tmpB = new THREE.Vector3();
  private tmpC = new THREE.Vector3();
  private tmpD = new THREE.Vector3();
  private tmpSpine = new THREE.Vector3();
  private tmpNeck = new THREE.Vector3();

  public bind(skMesh: THREE.SkinnedMesh): void {
    this.skeleton = skMesh.skeleton;
    this.bindMatrix.copy(skMesh.bindMatrix);
    this.bindMatrixInverse.copy(skMesh.bindMatrixInverse);

    const findBone = (name: string) => {
      const clean = name.replace(/\./g, '');
      return this.skeleton!.bones.find((b) => b.name === name || b.name === clean) || null;
    };

    this.bPelvisL = findBone('pelvis.L');
    this.bPelvisR = findBone('pelvis.R');
    this.bSpine05 = findBone('spine05');
    this.bSpine03 = findBone('spine03');
    this.bSpine02 = findBone('spine02');
    this.bSpine01 = findBone('spine01');
    this.bNeck01 = findBone('neck01');
    this.bNeck03 = findBone('neck03');
    this.bClavL = findBone('clavicle.L');
    this.bClavR = findBone('clavicle.R');
    this.bShoulderL = findBone('shoulder01.L');
    this.bShoulderR = findBone('shoulder01.R');
    this.bUpperL = findBone('upperarm01.L');
    this.bUpperR = findBone('upperarm01.R');
    this.bLowerL = findBone('lowerarm01.L');
    this.bLowerR = findBone('lowerarm01.R');
    this.bWristL = findBone('wrist.L');
    this.bWristR = findBone('wrist.R');

    this.initUpperBodyMesh(skMesh.geometry);
    this.updatePoseGeometry();
  }

  private initUpperBodyMesh(geom: THREE.BufferGeometry): void {
    const pos = geom.attributes.position;
    const jnt = geom.attributes.skinIndex;
    const wgt = geom.attributes.skinWeight;
    const idx = geom.index;
    if (!pos || !jnt || !wgt || !idx) return;

    const totalV = pos.count;
    let maxY = 1.56;
    for (let i = 0; i < totalV; i++) {
      const y = pos.getY(i);
      if (y > maxY) maxY = y;
    }
    const minKeepY = maxY * 0.44;
    const maxKeepY = maxY * 0.92;
    const oldToNew = new Int32Array(totalV).fill(-1);
    const keepVerts: number[] = [];

    // Filter to garment-relevant upper-body vertices scaled to avatar stature
    for (let i = 0; i < totalV; i++) {
      const vx = pos.getX(i);
      const vy = pos.getY(i);
      if (vy >= minKeepY && vy <= maxKeepY && Math.abs(vx) <= 0.55) {
        oldToNew[i] = keepVerts.length;
        keepVerts.push(i);
      }
    }

    this.upperVertCount = keepVerts.length;
    this.restPos = new Float32Array(this.upperVertCount * 3);
    this.skinnedPos = new Float32Array(this.upperVertCount * 3);
    this.skinJoints = new Uint16Array(this.upperVertCount * 4);
    this.skinWeights = new Float32Array(this.upperVertCount * 4);

    for (let ni = 0; ni < this.upperVertCount; ni++) {
      const oi = keepVerts[ni];
      this.restPos[ni * 3] = pos.getX(oi);
      this.restPos[ni * 3 + 1] = pos.getY(oi);
      this.restPos[ni * 3 + 2] = pos.getZ(oi);

      this.skinJoints[ni * 4] = jnt.getX(oi);
      this.skinJoints[ni * 4 + 1] = jnt.getY(oi);
      this.skinJoints[ni * 4 + 2] = jnt.getZ(oi);
      this.skinJoints[ni * 4 + 3] = jnt.getW(oi);

      this.skinWeights[ni * 4] = wgt.getX(oi);
      this.skinWeights[ni * 4 + 1] = wgt.getY(oi);
      this.skinWeights[ni * 4 + 2] = wgt.getZ(oi);
      this.skinWeights[ni * 4 + 3] = wgt.getW(oi);
    }

    const tris: number[] = [];
    const arr = idx.array;
    for (let f = 0; f < arr.length; f += 3) {
      const a = oldToNew[arr[f]];
      const b = oldToNew[arr[f + 1]];
      const c = oldToNew[arr[f + 2]];
      if (a >= 0 && b >= 0 && c >= 0) {
        tris.push(a, b, c);
      }
    }

    this.upperTriCount = tris.length / 3;
    this.triIndices = new Uint32Array(tris);
    this.triNormals = new Float32Array(this.upperTriCount * 3);
    this.triMinX = new Float32Array(this.upperTriCount);
    this.triMinY = new Float32Array(this.upperTriCount);
    this.triMinZ = new Float32Array(this.upperTriCount);
    this.triMaxX = new Float32Array(this.upperTriCount);
    this.triMaxY = new Float32Array(this.upperTriCount);
    this.triMaxZ = new Float32Array(this.upperTriCount);
    this.triVisited = new Uint32Array(this.upperTriCount);
  }

  public updatePoseGeometry(): void {
    if (!this.skeleton) return;
    this.skeleton.update();
    this.updateCapsules();
    this.updateSkinnedTrianglesAndHash();
  }

  private updateCapsules(): void {
    const cols: CapsuleCollider[] = [];
    const pushCap = (name: string, b1: THREE.Bone | null, b2: THREE.Bone | null, radius: number, zOff = 0) => {
      if (!b1 || !b2) return;
      const a = new THREE.Vector3();
      const b = new THREE.Vector3();
      b1.getWorldPosition(a);
      b2.getWorldPosition(b);
      if (zOff !== 0) {
        a.z += zOff;
        b.z += zOff;
      }
      cols.push({ name, a, b, radius });
    };

    // Inner anti-tunneling capsule cores (sit ~1.5 cm inside skin; exact surface handled by skinned mesh)
    pushCap('waist_spine', this.bSpine05, this.bSpine03, 0.095, 0.02);
    pushCap('mid_torso', this.bSpine03, this.bSpine01, 0.105, 0.025);
    pushCap('neck', this.bNeck01, this.bNeck03, 0.048, 0.0);

    // Pectoral / upper-chest inner cores
    if (this.bSpine02 && this.bClavL && this.bShoulderL) {
      this.bSpine02.getWorldPosition(this.tmpA);
      this.bShoulderL.getWorldPosition(this.tmpB);
      this.tmpA.x += 0.05;
      this.tmpA.z += 0.03;
      this.tmpB.x -= 0.025;
      this.tmpB.y -= 0.06;
      this.tmpB.z += 0.025;
      cols.push({ name: 'chest_L', a: this.tmpA.clone(), b: this.tmpB.clone(), radius: 0.074 });
    }
    if (this.bSpine02 && this.bClavR && this.bShoulderR) {
      this.bSpine02.getWorldPosition(this.tmpA);
      this.bShoulderR.getWorldPosition(this.tmpB);
      this.tmpA.x -= 0.05;
      this.tmpA.z += 0.03;
      this.tmpB.x += 0.025;
      this.tmpB.y -= 0.06;
      this.tmpB.z += 0.025;
      cols.push({ name: 'chest_R', a: this.tmpA.clone(), b: this.tmpB.clone(), radius: 0.074 });
    }

    // Deltoid / shoulder & arms inner cores
    pushCap('deltoid_L', this.bShoulderL, this.bUpperL, 0.054);
    pushCap('deltoid_R', this.bShoulderR, this.bUpperR, 0.054);
    pushCap('upperarm_L', this.bUpperL, this.bLowerL, 0.046);
    pushCap('upperarm_R', this.bUpperR, this.bLowerR, 0.046);
    pushCap('forearm_L', this.bLowerL, this.bWristL, 0.036);
    pushCap('forearm_R', this.bLowerR, this.bWristR, 0.036);

    this.capsules = cols;
  }

  private updateSkinnedTrianglesAndHash(): void {
    if (!this.skeleton || this.upperVertCount === 0) return;
    const bm = this.skeleton.boneMatrices;
    if (!bm) return;

    // CPU Linear Blend Skinning for upper-body vertices
    for (let i = 0; i < this.upperVertCount; i++) {
      const ix = i * 3;
      const rx = this.restPos[ix];
      const ry = this.restPos[ix + 1];
      const rz = this.restPos[ix + 2];

      let sx = 0;
      let sy = 0;
      let sz = 0;
      const jBase = i * 4;
      for (let k = 0; k < 4; k++) {
        const w = this.skinWeights[jBase + k];
        if (w <= 0) continue;
        const mOff = this.skinJoints[jBase + k] * 16;
        const tx = bm[mOff] * rx + bm[mOff + 4] * ry + bm[mOff + 8] * rz + bm[mOff + 12];
        const ty = bm[mOff + 1] * rx + bm[mOff + 5] * ry + bm[mOff + 9] * rz + bm[mOff + 13];
        const tz = bm[mOff + 2] * rx + bm[mOff + 6] * ry + bm[mOff + 10] * rz + bm[mOff + 14];
        sx += tx * w;
        sy += ty * w;
        sz += tz * w;
      }
      this.skinnedPos[ix] = sx;
      this.skinnedPos[ix + 1] = sy;
      this.skinnedPos[ix + 2] = sz;
    }

    // Build flat spatial hash for upper-body triangles
    this.hashHead.fill(-1);
    this.entryCount = 0;
    const pad = 0.012;

    for (let t = 0; t < this.upperTriCount; t++) {
      const i0 = this.triIndices[t * 3] * 3;
      const i1 = this.triIndices[t * 3 + 1] * 3;
      const i2 = this.triIndices[t * 3 + 2] * 3;

      const ax = this.skinnedPos[i0], ay = this.skinnedPos[i0 + 1], az = this.skinnedPos[i0 + 2];
      const bx = this.skinnedPos[i1], by = this.skinnedPos[i1 + 1], bz = this.skinnedPos[i1 + 2];
      const cx = this.skinnedPos[i2], cy = this.skinnedPos[i2 + 1], cz = this.skinnedPos[i2 + 2];

      const ux = bx - ax, uy = by - ay, uz = bz - az;
      const vx = cx - ax, vy = cy - ay, vz = cz - az;
      let nx = uy * vz - uz * vy;
      let ny = uz * vx - ux * vz;
      let nz = ux * vy - uy * vx;
      const nLen = Math.sqrt(nx * nx + ny * ny + nz * nz);
      if (nLen > 1e-8) {
        nx /= nLen;
        ny /= nLen;
        nz /= nLen;
      }
      this.triNormals[t * 3] = nx;
      this.triNormals[t * 3 + 1] = ny;
      this.triNormals[t * 3 + 2] = nz;

      const minX = Math.min(ax, bx, cx) - pad;
      const minY = Math.min(ay, by, cy) - pad;
      const minZ = Math.min(az, bz, cz) - pad;
      const maxX = Math.max(ax, bx, cx) + pad;
      const maxY = Math.max(ay, by, cy) + pad;
      const maxZ = Math.max(az, bz, cz) + pad;

      this.triMinX[t] = minX; this.triMinY[t] = minY; this.triMinZ[t] = minZ;
      this.triMaxX[t] = maxX; this.triMaxY[t] = maxY; this.triMaxZ[t] = maxZ;

      const x0 = Math.floor(minX / CELL_SIZE), x1 = Math.floor(maxX / CELL_SIZE);
      const y0 = Math.floor(minY / CELL_SIZE), y1 = Math.floor(maxY / CELL_SIZE);
      const z0 = Math.floor(minZ / CELL_SIZE), z1 = Math.floor(maxZ / CELL_SIZE);

      for (let gx = x0; gx <= x1; gx++) {
        for (let gy = y0; gy <= y1; gy++) {
          for (let gz = z0; gz <= z1; gz++) {
            if (this.entryCount >= this.entryTri.length) break;
            const h = ((gx * 73856093) ^ (gy * 19349663) ^ (gz * 83492791)) & (TABLE_SIZE - 1);
            const e = this.entryCount++;
            this.entryTri[e] = t;
            this.entryNext[e] = this.hashHead[h];
            this.hashHead[h] = e;
          }
        }
      }
    }
  }

  private closestPointOnTri(
    px: number, py: number, pz: number,
    ax: number, ay: number, az: number,
    bx: number, by: number, bz: number,
    cx: number, cy: number, cz: number,
    out: THREE.Vector3
  ): void {
    const abx = bx - ax, aby = by - ay, abz = bz - az;
    const acx = cx - ax, acy = cy - ay, acz = cz - az;
    const apx = px - ax, apy = py - ay, apz = pz - az;

    const d1 = abx * apx + aby * apy + abz * apz;
    const d2 = acx * apx + acy * apy + acz * apz;
    if (d1 <= 0 && d2 <= 0) { out.set(ax, ay, az); return; }

    const bpx = px - bx, bpy = py - by, bpz = pz - bz;
    const d3 = abx * bpx + aby * bpy + abz * bpz;
    const d4 = acx * bpx + acy * bpy + acz * bpz;
    if (d3 >= 0 && d4 <= d3) { out.set(bx, by, bz); return; }

    const vc = d1 * d4 - d3 * d2;
    if (vc <= 0 && d1 >= 0 && d3 <= 0) {
      const v = d1 / (d1 - d3);
      out.set(ax + abx * v, ay + aby * v, az + abz * v);
      return;
    }

    const cpx = px - cx, cpy = py - cy, cpz = pz - cz;
    const d5 = abx * cpx + aby * cpy + abz * cpz;
    const d6 = acx * cpx + acy * cpy + acz * cpz;
    if (d6 >= 0 && d5 <= d6) { out.set(cx, cy, cz); return; }

    const vb = d5 * d2 - d1 * d6;
    if (vb <= 0 && d2 >= 0 && d6 <= 0) {
      const w = d2 / (d2 - d6);
      out.set(ax + acx * w, ay + acy * w, az + acz * w);
      return;
    }

    const va = d3 * d6 - d5 * d4;
    if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0) {
      const w = (d4 - d3) / ((d4 - d3) + (d5 - d6));
      out.set(bx + (cx - bx) * w, by + (cy - by) * w, bz + (cz - bz) * w);
      return;
    }

    const denom = 1.0 / (va + vb + vc);
    const v = vb * denom;
    const w = vc * denom;
    out.set(ax + abx * v + acx * w, ay + aby * v + acy * w, az + abz * v + acz * w);
  }

  public resolveCollisions(
    pos: Float32Array,
    invMass: Float32Array,
    particleCount: number,
    thicknessM = 0.004,
    includeMeshNarrowPhase = true,
    prevPos?: Float32Array
  ): CollisionStepStats {
    const t0 = performance.now();
    let capsuleCorrections = 0;
    let meshCorrections = 0;
    let tunnelingIncidents = 0;

    // 1. Broad-phase anatomical capsule projection + swept midpoint CCD
    for (let i = 0; i < particleCount; i++) {
      if (invMass[i] === 0) continue;
      const ix = i * 3;
      let checkMid = false;
      let mx = 0, my = 0, mz = 0;
      if (prevPos) {
        const dx = pos[ix] - prevPos[ix];
        const dy = pos[ix + 1] - prevPos[ix + 1];
        const dz = pos[ix + 2] - prevPos[ix + 2];
        if (dx * dx + dy * dy + dz * dz > 0.0025 * 0.0025) {
          checkMid = true;
          mx = 0.5 * (pos[ix] + prevPos[ix]);
          my = 0.5 * (pos[ix + 1] + prevPos[ix + 1]);
          mz = 0.5 * (pos[ix + 2] + prevPos[ix + 2]);
        }
      }

      for (let k = 0; k < this.capsules.length; k++) {
        const col = this.capsules[k];
        const abx = col.b.x - col.a.x;
        const aby = col.b.y - col.a.y;
        const abz = col.b.z - col.a.z;
        const ab2 = abx * abx + aby * aby + abz * abz;
        if (ab2 < 1e-8) continue;

        // Swept midpoint check to prevent fast-motion tunneling
        if (checkMid) {
          const tm = Math.max(0, Math.min(1, ((mx - col.a.x) * abx + (my - col.a.y) * aby + (mz - col.a.z) * abz) / ab2));
          const rmx = mx - (col.a.x + abx * tm);
          const rmy = my - (col.a.y + aby * tm);
          const rmz = mz - (col.a.z + abz * tm);
          const dm2 = rmx * rmx + rmy * rmy + rmz * rmz;
          if (dm2 < col.radius * col.radius && dm2 > 1e-10) {
            const dm = Math.sqrt(dm2);
            const pushM = (col.radius - dm) / dm;
            pos[ix] = mx + rmx * pushM;
            pos[ix + 1] = my + rmy * pushM;
            pos[ix + 2] = mz + rmz * pushM;
            tunnelingIncidents++;
          }
        }

        const t = Math.max(0, Math.min(1, ((pos[ix] - col.a.x) * abx + (pos[ix + 1] - col.a.y) * aby + (pos[ix + 2] - col.a.z) * abz) / ab2));
        const cx = col.a.x + abx * t;
        const cy = col.a.y + aby * t;
        const cz = col.a.z + abz * t;
        const rx = pos[ix] - cx;
        const ry = pos[ix + 1] - cy;
        const rz = pos[ix + 2] - cz;
        const d2 = rx * rx + ry * ry + rz * rz;
        if (d2 < col.radius * col.radius && d2 > 1e-10) {
          const d = Math.sqrt(d2);
          const push = (col.radius - d) / d;
          pos[ix] += rx * push;
          pos[ix + 1] += ry * push;
          pos[ix + 2] += rz * push;
          capsuleCorrections++;
        }
      }
    }

    // 2. Narrow-phase skinned triangle-mesh collision via spatial hash
    if (includeMeshNarrowPhase && this.upperTriCount > 0) {
      for (let i = 0; i < particleCount; i++) {
        if (invMass[i] === 0) continue;
        const ix = i * 3;
        const px = pos[ix];
        const py = pos[ix + 1];
        const pz = pos[ix + 2];

        const gx = Math.floor(px / CELL_SIZE);
        const gy = Math.floor(py / CELL_SIZE);
        const gz = Math.floor(pz / CELL_SIZE);
        const h = ((gx * 73856093) ^ (gy * 19349663) ^ (gz * 83492791)) & (TABLE_SIZE - 1);

        let e = this.hashHead[h];
        const stamp = ++this.visitStamp;
        if (stamp === 0xffffffff) {
          this.triVisited.fill(0);
          this.visitStamp = 1;
        }

        let bestDepth = 0;
        let bestCx = 0, bestCy = 0, bestCz = 0;
        let bestNx = 0, bestNy = 0, bestNz = 0;

        while (e !== -1) {
          const t = this.entryTri[e];
          e = this.entryNext[e];
          if (this.triVisited[t] === stamp) continue;
          this.triVisited[t] = stamp;

          if (
            px < this.triMinX[t] || px > this.triMaxX[t] ||
            py < this.triMinY[t] || py > this.triMaxY[t] ||
            pz < this.triMinZ[t] || pz > this.triMaxZ[t]
          ) {
            continue;
          }

          const i0 = this.triIndices[t * 3] * 3;
          const i1 = this.triIndices[t * 3 + 1] * 3;
          const i2 = this.triIndices[t * 3 + 2] * 3;
          this.closestPointOnTri(
            px, py, pz,
            this.skinnedPos[i0], this.skinnedPos[i0 + 1], this.skinnedPos[i0 + 2],
            this.skinnedPos[i1], this.skinnedPos[i1 + 1], this.skinnedPos[i1 + 2],
            this.skinnedPos[i2], this.skinnedPos[i2 + 1], this.skinnedPos[i2 + 2],
            this.tmpC
          );

          const dx = px - this.tmpC.x;
          const dy = py - this.tmpC.y;
          const dz = pz - this.tmpC.z;
          const dist2 = dx * dx + dy * dy + dz * dz;
          if (dist2 > 0.025 * 0.025) continue;

          const nx = this.triNormals[t * 3];
          const ny = this.triNormals[t * 3 + 1];
          const nz = this.triNormals[t * 3 + 2];
          const signedDist = dx * nx + dy * ny + dz * nz;

          // Inside surface or closer than thicknessM (band limited to -1.2cm so opposite side doesn't trigger)
          if (signedDist < thicknessM && signedDist > -0.012) {
            const pen = thicknessM - signedDist;
            if (pen > bestDepth) {
              bestDepth = pen;
              bestCx = this.tmpC.x;
              bestCy = this.tmpC.y;
              bestCz = this.tmpC.z;
              bestNx = nx;
              bestNy = ny;
              bestNz = nz;
            }
          }
        }

        if (bestDepth > 0) {
          // Smooth damped push along outward normal prevents jagged triangle-to-triangle snapping
          const push = bestDepth * 0.65;
          pos[ix] += bestNx * push;
          pos[ix + 1] += bestNy * push;
          pos[ix + 2] += bestNz * push;
          void bestCx; void bestCy; void bestCz;
          meshCorrections++;
        }
      }
    }

    return {
      capsuleCorrections,
      meshCorrections,
      tunnelingIncidents,
      collisionTimeMs: performance.now() - t0,
    };
  }

  /**
   * Quantitative signed-distance penetration audit against the live posed Anny upper-body mesh.
   */
  public measurePenetration(pos: Float32Array, particleCount: number): PenetrationReport {
    if (this.upperTriCount === 0) {
      return { totalParticles: particleCount, penetratingCount: 0, maxPenetrationMm: 0, meanPenetrationMm: 0 };
    }

    let penetratingCount = 0;
    let maxPenM = 0;
    let sumPenM = 0;

    for (let i = 0; i < particleCount; i++) {
      const ix = i * 3;
      const px = pos[ix];
      const py = pos[ix + 1];
      const pz = pos[ix + 2];

      const gx = Math.floor(px / CELL_SIZE);
      const gy = Math.floor(py / CELL_SIZE);
      const gz = Math.floor(pz / CELL_SIZE);
      const h = ((gx * 73856093) ^ (gy * 19349663) ^ (gz * 83492791)) & (TABLE_SIZE - 1);

      let e = this.hashHead[h];
      const stamp = ++this.visitStamp;
      if (stamp === 0xffffffff) {
        this.triVisited.fill(0);
        this.visitStamp = 1;
      }

      let worstPen = 0;
      while (e !== -1) {
        const t = this.entryTri[e];
        e = this.entryNext[e];
        if (this.triVisited[t] === stamp) continue;
        this.triVisited[t] = stamp;

        if (
          px < this.triMinX[t] || px > this.triMaxX[t] ||
          py < this.triMinY[t] || py > this.triMaxY[t] ||
          pz < this.triMinZ[t] || pz > this.triMaxZ[t]
        ) {
          continue;
        }

        const i0 = this.triIndices[t * 3] * 3;
        const i1 = this.triIndices[t * 3 + 1] * 3;
        const i2 = this.triIndices[t * 3 + 2] * 3;
        this.closestPointOnTri(
          px, py, pz,
          this.skinnedPos[i0], this.skinnedPos[i0 + 1], this.skinnedPos[i0 + 2],
          this.skinnedPos[i1], this.skinnedPos[i1 + 1], this.skinnedPos[i1 + 2],
          this.skinnedPos[i2], this.skinnedPos[i2 + 1], this.skinnedPos[i2 + 2],
          this.tmpC
        );

        const dx = px - this.tmpC.x;
        const dy = py - this.tmpC.y;
        const dz = pz - this.tmpC.z;
        if (dx * dx + dy * dy + dz * dz > 0.02 * 0.02) continue;

        const nx = this.triNormals[t * 3];
        const ny = this.triNormals[t * 3 + 1];
        const nz = this.triNormals[t * 3 + 2];
        const sd = dx * nx + dy * ny + dz * nz;
        if (sd < 0 && sd > -0.018) {
          const pen = -sd;
          if (pen > worstPen) worstPen = pen;
        }
      }

      if (worstPen > 0.0005) {
        penetratingCount++;
        sumPenM += worstPen;
        if (worstPen > maxPenM) maxPenM = worstPen;
      }
    }

    return {
      totalParticles: particleCount,
      penetratingCount,
      maxPenetrationMm: Number((maxPenM * 1000).toFixed(3)),
      meanPenetrationMm: penetratingCount > 0 ? Number(((sumPenM / penetratingCount) * 1000).toFixed(3)) : 0,
    };
  }

  public getSpineAndNeckTransforms(): { spine01World: THREE.Matrix4 | null; neck01World: THREE.Matrix4 | null } {
    return {
      spine01World: this.bSpine01 ? this.bSpine01.matrixWorld : null,
      neck01World: this.bNeck01 ? this.bNeck01.matrixWorld : null,
    };
  }

  public getCapsuleCount(): number {
    return this.capsules.length;
  }

  public getUpperTriangleCount(): number {
    return this.upperTriCount;
  }
}
