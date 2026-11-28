/**
 * WearWise Phase 10.6 — Full Upper-Body Articulated Pose Library
 * ===============================================================
 * Distinguishes anatomical joint rotations (degrees) from overall arm elevation.
 * All bounds represent anatomically plausible ranges for upper-body try-on testing.
 */

export interface ArticulationState {
  /** Coronal arm abduction/elevation from neutral A-pose (0°..90°) */
  shoulderElevL: number;
  shoulderElevR: number;
  /** Sagittal arm forward flexion (0°..80°) */
  armForwardL: number;
  armForwardR: number;
  /** Clavicle upward shrug (0°..20°) */
  clavicleLift: number;
  /** Elbow flexion (0°..110°) */
  elbowFlexL: number;
  elbowFlexR: number;
  /** Forearm pronation/supination twist (-45°..45°) */
  forearmTwist: number;
  /** Wrist flexion/extension (-25°..25°) */
  wristFlex: number;
  /** Spine forward/backward lean (-15°..30°) */
  torsoForwardLean: number;
  /** Spine lateral lean (-20°..20°) */
  torsoLateralLean: number;
  /** Spine axial twist (-30°..30°) */
  torsoTwist: number;
}

export const NEUTRAL_POSE: ArticulationState = {
  shoulderElevL: 0,
  shoulderElevR: 0,
  armForwardL: 0,
  armForwardR: 0,
  clavicleLift: 0,
  elbowFlexL: 0,
  elbowFlexR: 0,
  forearmTwist: 0,
  wristFlex: 0,
  torsoForwardLean: 0,
  torsoLateralLean: 0,
  torsoTwist: 0,
};

export interface PosePreset {
  id: string;
  label: string;
  description: string;
  state: ArticulationState;
}

export const ARTICULATED_POSES: PosePreset[] = [
  {
    id: 'P0',
    label: 'P0: Neutral A-Pose',
    description: 'Neutral A-pose (all joint angles 0°)',
    state: { ...NEUTRAL_POSE },
  },
  {
    id: 'P1',
    label: 'P1: Both Arms 30°',
    description: 'Bilateral shoulder elevation 30° + 4° clavicle lift',
    state: { ...NEUTRAL_POSE, shoulderElevL: 30, shoulderElevR: 30, clavicleLift: 4 },
  },
  {
    id: 'P2',
    label: 'P2: Both Arms 45°',
    description: 'Bilateral shoulder elevation 45° (T-pose) + 7° clavicle lift',
    state: { ...NEUTRAL_POSE, shoulderElevL: 45, shoulderElevR: 45, clavicleLift: 7 },
  },
  {
    id: 'P3',
    label: 'P3: Both Arms 90°',
    description: 'Bilateral shoulder elevation 90° (overhead V-pose) + 14° clavicle lift',
    state: { ...NEUTRAL_POSE, shoulderElevL: 90, shoulderElevR: 90, clavicleLift: 14 },
  },
  {
    id: 'P4',
    label: 'P4: Left Arm Raised',
    description: 'Asymmetric: left shoulder 75° + clavicle 10°, right neutral',
    state: { ...NEUTRAL_POSE, shoulderElevL: 75, clavicleLift: 10 },
  },
  {
    id: 'P5',
    label: 'P5: Right Arm Raised',
    description: 'Asymmetric: right shoulder 75° + clavicle 10°, left neutral',
    state: { ...NEUTRAL_POSE, shoulderElevR: 75, clavicleLift: 10 },
  },
  {
    id: 'P6',
    label: 'P6: Elbows Flexed',
    description: 'Bilateral elbow flexion 60° + 20° forearm twist + 15° wrist flex',
    state: { ...NEUTRAL_POSE, elbowFlexL: 60, elbowFlexR: 60, forearmTwist: 20, wristFlex: 15 },
  },
  {
    id: 'P7',
    label: 'P7: Arms Forward',
    description: 'Bilateral forward shoulder flexion 50° + 20° elbow flexion',
    state: { ...NEUTRAL_POSE, armForwardL: 50, armForwardR: 50, elbowFlexL: 20, elbowFlexR: 20 },
  },
  {
    id: 'P8',
    label: 'P8: Overhead + Elbows',
    description: 'Bilateral shoulder 85° + clavicle 12° + elbow flexion 45°',
    state: { ...NEUTRAL_POSE, shoulderElevL: 85, shoulderElevR: 85, clavicleLift: 12, elbowFlexL: 45, elbowFlexR: 45 },
  },
  {
    id: 'P9',
    label: 'P9: Torso Forward Lean',
    description: 'Spine forward lean 22° + natural 15° elbow bend',
    state: { ...NEUTRAL_POSE, torsoForwardLean: 22, elbowFlexL: 15, elbowFlexR: 15 },
  },
  {
    id: 'P10',
    label: 'P10: Torso Lateral Lean',
    description: 'Spine lateral lean 16° + 10° shoulder counterbalance',
    state: { ...NEUTRAL_POSE, torsoLateralLean: 16, shoulderElevL: 10 },
  },
  {
    id: 'P11',
    label: 'P11: Combined Movement',
    description: 'Spine twist 18° + lateral lean 8° + forward lean 10° + L arm 65°/elbow 45° + R forward 35°',
    state: {
      ...NEUTRAL_POSE,
      torsoTwist: 18,
      torsoLateralLean: 8,
      torsoForwardLean: 10,
      clavicleLift: 8,
      shoulderElevL: 65,
      elbowFlexL: 45,
      armForwardR: 35,
      elbowFlexR: 30,
      forearmTwist: 15,
    },
  },
];
