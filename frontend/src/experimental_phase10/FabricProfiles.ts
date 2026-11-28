/**
 * WearWise Phase 10.7 — Structured Fabric Mechanical Profiles
 * ============================================================
 * Provisional engineering parameters calibrated for XPBD cloth simulation.
 * Note: GSM and thickness reflect nominal garment spec; compliances, damping,
 * friction, and recovery are provisional simulation constants pending physical
 * Kawabata/KES-F lab measurement.
 */

export interface SimFabricProfile {
  id: string;
  name: string;
  arealDensityGsm: number;
  thicknessMm: number;
  /** Base XPBD structural distance compliance (m/N equivalent in XPBD) */
  stretchCompliance: number;
  /** Warp (vertical/Y-aligned) relative stiffness multiplier (>= 1.0 = stiffer) */
  warpResistance: number;
  /** Weft (horizontal/X-aligned) relative stiffness multiplier */
  weftResistance: number;
  /** Diagonal/shear compliance multiplier */
  shearCompliance: number;
  /** 2-hop bending compliance */
  bendCompliance: number;
  /** Per-substep velocity damping factor */
  damping: number;
  /** Body-cloth tangential friction coefficient (0..1) */
  friction: number;
  /** Elastic equilibrium recovery pull factor */
  recoveryStiffness: number;
  /** Gravity scale factor reflecting areal weight */
  gravityScale: number;
  provenance: 'provisional_calibrated';
}

export const SIM_FABRICS: Record<string, SimFabricProfile> = {
  waffle_knit_240: {
    id: 'waffle_knit_240',
    name: 'Cotton Waffle Knit (240 GSM)',
    arealDensityGsm: 240,
    thicknessMm: 1.4,
    stretchCompliance: 0.0000045,
    warpResistance: 1.15,
    weftResistance: 0.82, // Knit has higher horizontal/weft give
    shearCompliance: 0.000009,
    bendCompliance: 0.00055, // Softer, more substantial drape
    damping: 0.955,
    friction: 0.42,
    recoveryStiffness: 0.05,
    gravityScale: 1.18, // Heavier 240 GSM drape
    provenance: 'provisional_calibrated',
  },
  rigid_poplin_140: {
    id: 'rigid_poplin_140',
    name: 'Structured Poplin (140 GSM)',
    arealDensityGsm: 140,
    thicknessMm: 0.65,
    stretchCompliance: 0.0000005, // Woven poplin is ~9x stiffer in stretch
    warpResistance: 1.45,
    weftResistance: 1.35,
    shearCompliance: 0.0000015,
    bendCompliance: 0.000045, // Crisp, structured fold behavior
    damping: 0.935,
    friction: 0.28,
    recoveryStiffness: 0.09,
    gravityScale: 0.82, // Lighter 140 GSM response
    provenance: 'provisional_calibrated',
  },
};
