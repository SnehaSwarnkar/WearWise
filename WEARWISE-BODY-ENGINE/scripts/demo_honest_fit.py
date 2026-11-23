"""
WearWise Phase 5A Honest Fit Demonstration Script
Demonstrates end-to-end Honest Fit evaluation using real NAVER Anny v0.6.2 extracted measurements,
physical garment dimensions (T-shirt and casual shirt), 6-tier classification,
effective weighting, evidence coverage gating, and transparent human-readable explanations.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.entities.body import BodyMeasurement
from app.domain.taxonomies.measurement import (
    MeasurementAcquisitionMethod,
    MeasurementValidationState,
    MeasurementLifecycleStatus,
    MeasurementAssessmentState,
)
from app.domain.taxonomies.garment import (
    RegionalFitClassification,
    FabricStretchDirection,
)
from app.domain.entities.garment import FabricProperties
from app.fit.rulebook import (
    PROVISIONAL_EASE_INTERVALS,
    MINIMUM_WEARABLE_EASE,
    BASELINE_REGIONAL_WEIGHTS,
    DEFAULT_BETA_COEFFICIENTS,
    RULEBOOK_VERSION,
)
from app.fit.registry import MeasurementCompatibilityRegistry
from app.fit.models import GarmentInputSpec, FitEvaluationReport
from app.fit.engine import HonestFitEngine
from app.fit.port import HonestFitEvaluationPort


def build_measurement(code: str, val_cm: float, assessment=MeasurementAssessmentState.ELIGIBLE) -> BodyMeasurement:
    return BodyMeasurement(
        measurement_code=code,
        value_cm=Decimal(f"{val_cm:.2f}"),
        unit="cm",
        acquisition_method=MeasurementAcquisitionMethod.GEOMETRY_EXTRACTED,
        validation_state=MeasurementValidationState.INTERNALLY_CONSISTENT,
        lifecycle_status=MeasurementLifecycleStatus.ACTIVE,
        assessment_state=assessment,
    )


def load_neutral_masculine_measurements() -> dict:
    """Loads extracted measurements from Phase 4B neutral masculine avatar."""
    diag_path = Path(__file__).resolve().parent.parent / "artifacts" / "phase4b" / "phase4b_diagnostics.json"
    if diag_path.exists():
        with open(diag_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            meas_dict = data.get("avatars", {}).get("neutral_masculine", {}).get("measurements", {})
            if meas_dict:
                measurements = {}
                for code, m_data in meas_dict.items():
                    m_rec = m_data.get("measurement")
                    if m_rec:
                        val = float(m_rec["value_cm"])
                        state_str = m_rec.get("assessment_state", "eligible")
                        state = (
                            MeasurementAssessmentState.PROVISIONAL
                            if state_str == "provisional"
                            else MeasurementAssessmentState.ELIGIBLE
                        )
                        measurements[code] = build_measurement(code, val, state)
                print(f"[OK] Loaded {len(measurements)} extracted measurements from {diag_path.name}")
                return measurements

    # Fallback to canonical Phase 4B baseline values
    print("[INFO] Using canonical Phase 4B baseline extracted measurements")
    return {
        "stature": build_measurement("stature", 156.83, MeasurementAssessmentState.ELIGIBLE),
        "shoulder_biacromial_breadth": build_measurement("shoulder_biacromial_breadth", 37.20, MeasurementAssessmentState.ELIGIBLE),
        "chest_circumference": build_measurement("chest_circumference", 77.85, MeasurementAssessmentState.ELIGIBLE),
        "waist_planar_circumference": build_measurement("waist_planar_circumference", 65.96, MeasurementAssessmentState.ELIGIBLE),
        "hip_circumference": build_measurement("hip_circumference", 91.62, MeasurementAssessmentState.PROVISIONAL),
    }


def run_demo():
    print("=" * 80)
    print("  WearWise — Phase 5A Honest Fit Demonstration")
    print(f"  Provisional Rulebook: Rev {RULEBOOK_VERSION}")
    print("=" * 80)

    # 1. Load neutral masculine avatar body measurements
    body_measurements = load_neutral_masculine_measurements()
    print("\n--- Active User Body Measurements (Neutral Masculine Avatar) ---")
    for k, m in body_measurements.items():
        print(f"  - {k:30s}: {m.value_cm:6.2f} cm | {m.assessment_state.value.upper():12s}")

    # 2. Fabric definition: 100% rigid cotton jersey
    rigid_cotton = FabricProperties(
        fibre_composition={"cotton": 1.0},
        mechanical_stretch_pct=0.015,  # 1.5% stretch under 15N load
        stretch_recovery_pct=0.90,
        stretch_direction=FabricStretchDirection.RIGID_ZERO,
    )

    port = HonestFitEvaluationPort()

    # -------------------------------------------------------------------------
    # Scenario 1: Heavyweight Crewneck T-Shirt (Sizes XS, S, M, L)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SCENARIO 1: Heavyweight Crewneck Cotton T-Shirt (Real Measured Finished Dimensions)")
    print("=" * 80)

    # Real manually measured finished garment dimensions (laid flat, pit-to-pit doubled)
    tshirt_sizes = [
        GarmentInputSpec(
            title="Everyday Heavyweight Crewneck Tee",
            category="t_shirt",
            size_label="XS",
            dimensions_cm={
                "garment_half_chest_width": 41.5,       # 83.0 cm full circ (ease +5.15 cm => FITTED)
                "garment_shoulder_seam_width": 37.5,    # ease +0.30 cm => FITTED
                "garment_back_length": 64.0,
            },
            fabric_properties=rigid_cotton,
        ),
        GarmentInputSpec(
            title="Everyday Heavyweight Crewneck Tee",
            category="t_shirt",
            size_label="S",
            dimensions_cm={
                "garment_half_chest_width": 44.0,       # 88.0 cm full circ (ease +10.15 cm => REGULAR)
                "garment_shoulder_seam_width": 39.0,    # ease +1.80 cm => REGULAR
                "garment_back_length": 66.5,
            },
            fabric_properties=rigid_cotton,
        ),
        GarmentInputSpec(
            title="Everyday Heavyweight Crewneck Tee",
            category="t_shirt",
            size_label="M",
            dimensions_cm={
                "garment_half_chest_width": 47.0,       # 94.0 cm full circ (ease +16.15 cm => RELAXED)
                "garment_shoulder_seam_width": 41.5,    # ease +4.30 cm => RELAXED
                "garment_back_length": 69.0,
            },
            fabric_properties=rigid_cotton,
        ),
        GarmentInputSpec(
            title="Everyday Heavyweight Crewneck Tee",
            category="t_shirt",
            size_label="L",
            dimensions_cm={
                "garment_half_chest_width": 50.5,       # 101.0 cm full circ (ease +23.15 cm => OVERSIZED)
                "garment_shoulder_seam_width": 44.0,    # ease +6.80 cm => OVERSIZED
                "garment_back_length": 72.0,
            },
            fabric_properties=rigid_cotton,
        ),
    ]

    print("\n[Evaluating T-Shirt Sizes for User Preference: 'REGULAR']")
    tshirt_reports = port.evaluate_multi_size_garment(
        body_measurements, tshirt_sizes, user_preference="regular"
    )

    for r in tshirt_reports:
        print(f"\nSize {r.size_label:2s} -> Score: {r.composite_score:5.1f} / 100 | Status: {r.status.upper():16s} | Coverage: {r.coverage_ratio*100:.1f}%")
        print(f"  Summary: {r.summary_explanation}")
        for reg, res in r.regional_results.items():
            print(f"    - {reg:28s}: Garment {res.garment_dimension_cm:5.1f} cm | Body {res.body_measurement_cm:5.1f} cm | Ease {res.ease_cm:+6.2f} cm | {res.classification.value:10s} (Penalty: {res.penalty:5.1f})")
            print(f"      Explanation: {res.explanation}")

    best_tee = port.recommend_best_size(body_measurements, tshirt_sizes, user_preference="regular")
    print(f"\n>>> Recommended Size for 'regular' fit: Size {best_tee.size_label} (Score: {best_tee.composite_score:.1f}/100)")

    # -------------------------------------------------------------------------
    # Scenario 2: Casual Button-Down Shirt (with Waist Circumference Supplied)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SCENARIO 2: Classic Oxford Casual Shirt (Chest, Waist & Shoulders Supplied)")
    print("=" * 80)

    shirt_sizes = [
        GarmentInputSpec(
            title="Classic Oxford Button-Down Shirt",
            category="casual_shirt",
            size_label="S",
            dimensions_cm={
                "garment_chest_circumference": 88.0,    # ease +10.15 cm => REGULAR
                "garment_waist_circumference": 74.0,    # ease +8.04 cm => REGULAR
                "garment_shoulder_seam_width": 39.5,   # ease +2.30 cm => REGULAR
                "garment_back_length": 71.0,
            },
            fabric_properties=rigid_cotton,
        ),
        GarmentInputSpec(
            title="Classic Oxford Button-Down Shirt",
            category="casual_shirt",
            size_label="M",
            dimensions_cm={
                "garment_chest_circumference": 94.0,    # ease +16.15 cm => RELAXED
                "garment_waist_circumference": 80.0,    # ease +14.04 cm => RELAXED
                "garment_shoulder_seam_width": 42.0,   # ease +4.80 cm => RELAXED
                "garment_back_length": 74.0,
            },
            fabric_properties=rigid_cotton,
        ),
        GarmentInputSpec(
            title="Classic Oxford Button-Down Shirt",
            category="casual_shirt",
            size_label="L",
            dimensions_cm={
                "garment_chest_circumference": 102.0,   # ease +24.15 cm => TOO_LARGE
                "garment_waist_circumference": 88.0,    # ease +22.04 cm => OVERSIZED
                "garment_shoulder_seam_width": 45.0,   # ease +7.80 cm => OVERSIZED
                "garment_back_length": 77.0,
            },
            fabric_properties=rigid_cotton,
        ),
    ]

    print("\n[Evaluating Casual Shirt Sizes for User Preference: 'REGULAR']")
    shirt_reports = port.evaluate_multi_size_garment(
        body_measurements, shirt_sizes, user_preference="regular"
    )

    for r in shirt_reports:
        print(f"\nSize {r.size_label:2s} -> Score: {r.composite_score:5.1f} / 100 | Status: {r.status.upper():16s} | Coverage: {r.coverage_ratio*100:.1f}%")
        print(f"  Summary: {r.summary_explanation}")
        for reg, res in r.regional_results.items():
            print(f"    - {reg:28s}: Garment {res.garment_dimension_cm:5.1f} cm | Body {res.body_measurement_cm:5.1f} cm | Ease {res.ease_cm:+6.2f} cm | {res.classification.value:10s} (Penalty: {res.penalty:5.1f})")
            print(f"      Explanation: {res.explanation}")

    best_shirt = port.recommend_best_size(body_measurements, shirt_sizes, user_preference="regular")
    print(f"\n>>> Recommended Casual Shirt Size for 'regular' fit: Size {best_shirt.size_label} (Score: {best_shirt.composite_score:.1f}/100)")

    # -------------------------------------------------------------------------
    # Scenario 3: Missing Evidence / Coverage Gate Test (< 70%)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SCENARIO 3: Evidence Coverage Gate Failure (< 70% Coverage)")
    print("=" * 80)
    sparse_body = {
        "shoulder_biacromial_breadth": body_measurements["shoulder_biacromial_breadth"],
    }
    sparse_report = port.evaluate_garment_size(sparse_body, tshirt_sizes[1], user_preference="regular")
    print(f"Evaluated with missing chest circumference:")
    print(f"  Coverage Ratio  : {sparse_report.coverage_ratio * 100:.1f}% (Required: 70.0%)")
    print(f"  Status          : {sparse_report.status}")
    print(f"  Composite Score : {sparse_report.composite_score}")
    print(f"  Missing Fields  : {sparse_report.missing_required_dimensions}")
    print(f"  Actionable Msg  : {sparse_report.summary_explanation}")

    # -------------------------------------------------------------------------
    # Scenario 4: Rigid Unwearable Tight Size Rejection
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("SCENARIO 4: Rigid Unwearable Tight Size Rejection")
    print("=" * 80)
    tight_tshirt = GarmentInputSpec(
        title="Skin-tight Shrink-fit Tee",
        category="t_shirt",
        size_label="XXS",
        dimensions_cm={
            "garment_chest_circumference": 78.5,  # ease +0.65 cm (< +2.0 cm min wearable)
            "garment_shoulder_seam_width": 35.0,  # ease -2.20 cm (< -1.0 cm min wearable)
        },
        fabric_properties=rigid_cotton,
    )
    tight_report = port.evaluate_garment_size(body_measurements, tight_tshirt, user_preference="regular")
    print(f"Evaluated constricting rigid garment:")
    print(f"  Status          : {tight_report.status}")
    print(f"  Chest Penalty   : {tight_report.regional_results['chest_circumference'].penalty}")
    print(f"  Actionable Msg  : {tight_report.summary_explanation}")

    # -------------------------------------------------------------------------
    # 5. Export JSON Reports
    # -------------------------------------------------------------------------
    art_dir = Path(__file__).resolve().parent.parent / "artifacts" / "phase5a"
    art_dir.mkdir(parents=True, exist_ok=True)
    brain_dir = Path(r"C:\Users\Lenovo\.gemini\antigravity\brain\c57b9fa6-3e23-4fa2-b534-c1f6bc625ad8\phase5a")
    brain_dir.mkdir(parents=True, exist_ok=True)

    tshirt_json_path = art_dir / "phase5a_tshirt_fit_report.json"
    shirt_json_path = art_dir / "phase5a_casual_shirt_fit_report.json"

    tshirt_full_report = {
        "milestone": "Phase 5A Honest Fit Demonstration",
        "avatar_id": "neutral_masculine",
        "garment_type": "t_shirt",
        "recommended_size": best_tee.size_label,
        "evaluations": [r.to_dict() for r in tshirt_reports],
    }

    shirt_full_report = {
        "milestone": "Phase 5A Honest Fit Demonstration",
        "avatar_id": "neutral_masculine",
        "garment_type": "casual_shirt",
        "recommended_size": best_shirt.size_label,
        "evaluations": [r.to_dict() for r in shirt_reports],
    }

    with open(tshirt_json_path, "w", encoding="utf-8") as f:
        json.dump(tshirt_full_report, f, indent=2)
    with open(shirt_json_path, "w", encoding="utf-8") as f:
        json.dump(shirt_full_report, f, indent=2)

    shutil.copyfile(tshirt_json_path, brain_dir / "phase5a_tshirt_fit_report.json")
    shutil.copyfile(shirt_json_path, brain_dir / "phase5a_casual_shirt_fit_report.json")

    print("\n" + "=" * 80)
    print(f"[OK] Exported T-Shirt JSON report to: {tshirt_json_path}")
    print(f"[OK] Exported Casual Shirt JSON report to: {shirt_json_path}")
    print(f"[OK] Copied reports to brain artifacts directory: {brain_dir}")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
