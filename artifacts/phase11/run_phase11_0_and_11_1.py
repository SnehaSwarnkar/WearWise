import hashlib
import json
import os
import struct
import sys
import uuid
from pathlib import Path

os.environ["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
os.environ["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
os.environ["WEARWISE_ENV"] = "development"
os.environ["DATABASE_URL"] = r"sqlite:///c:/Users/Lenovo/Documents/Major Project/WearWise/WEARWISE-BODY-ENGINE/data/wearwise_staging.db"

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
BE_DIR = REPO / "WEARWISE-BODY-ENGINE"
sys.path.insert(0, str(BE_DIR))

OUT_11_0 = REPO / "artifacts" / "phase11" / "phase11_0"
OUT_11_1 = REPO / "artifacts" / "phase11" / "phase11_1"
AVATAR_OUT = OUT_11_1 / "avatars"
PUB_11 = REPO / "frontend" / "public" / "experimental_phase11"
for d in (OUT_11_0, OUT_11_1, AVATAR_OUT, PUB_11):
    d.mkdir(parents=True, exist_ok=True)

import trimesh
from app.db.session import SessionFactory, init_db
from app.services.profile_service import ProfileService
from app.services.avatar_service import AvatarOrchestrationService
from app.services.errors import ForbiddenError


def inspect_glb_rig(glb_bytes: bytes) -> dict:
    _, _, _ = struct.unpack("<III", glb_bytes[:12])
    chunk_len, _ = struct.unpack("<II", glb_bytes[12:20])
    gltf = json.loads(glb_bytes[20 : 20 + chunk_len].decode("utf-8"))
    skins = gltf.get("skins", [])
    joints = len(skins[0]["joints"]) if skins else 0
    attrs = gltf["meshes"][0]["primitives"][0]["attributes"] if gltf.get("meshes") else {}
    return {
        "bytes": len(glb_bytes),
        "skins": len(skins),
        "bones": joints,
        "has_joints_0": "JOINTS_0" in attrs,
        "has_weights_0": "WEIGHTS_0" in attrs,
        "verts": gltf["accessors"][attrs["POSITION"]]["count"] if "POSITION" in attrs else 0,
    }


def classify_fit(chest_ease_cm: float, waist_ease_cm: float, shoulder_ease_cm: float) -> str:
    if chest_ease_cm < 0.0 or shoulder_ease_cm < -1.5:
        return "Too tight"
    if chest_ease_cm < 5.0:
        return "Close fit"
    if chest_ease_cm <= 12.0:
        return "Regular fit"
    if chest_ease_cm <= 20.0:
        return "Relaxed fit"
    return "Too loose"


# Read-only reference specs for protected TSH-WW-CREW-001 Rev3 S / M / L (from M2R-C pattern specs)
GARMENT_SIZES = {
    "S": {"chest_cm": 96.0, "waist_cm": 92.0, "shoulder_cm": 43.0, "sleeve_cm": 21.0, "length_cm": 68.0},
    "M": {"chest_cm": 104.0, "waist_cm": 100.0, "shoulder_cm": 46.0, "sleeve_cm": 22.5, "length_cm": 71.0},
    "L": {"chest_cm": 112.0, "waist_cm": 108.0, "shoulder_cm": 49.0, "sleeve_cm": 24.0, "length_cm": 74.0},
}

TEST_PROFILES = [
    {
        "id": "PROFILE_A_SLIM_MALE",
        "gender": "masculine",
        "stature_cm": 172.0,
        "weight_kg": 63.0,
        "target_chest_cm": 92.0,
        "target_waist_cm": 76.0,
        "controls": {"shoulder_width": 0.42, "chest_fullness": 0.35, "belly_fullness": 0.30, "waist_definition": 0.70, "arm_fullness": 0.38, "hip_fullness": 0.40, "thigh_fullness": 0.40, "calf_fullness": 0.40},
    },
    {
        "id": "PROFILE_B_ATHLETIC_MALE",
        "gender": "masculine",
        "stature_cm": 178.5,
        "weight_kg": 76.0,
        "target_chest_cm": 100.0,
        "target_waist_cm": 82.0,
        "controls": {"shoulder_width": 0.62, "chest_fullness": 0.58, "belly_fullness": 0.40, "waist_definition": 0.65, "arm_fullness": 0.58, "hip_fullness": 0.48, "thigh_fullness": 0.55, "calf_fullness": 0.52},
    },
    {
        "id": "PROFILE_C_BROAD_MALE",
        "gender": "masculine",
        "stature_cm": 184.0,
        "weight_kg": 92.0,
        "target_chest_cm": 110.0,
        "target_waist_cm": 94.0,
        "controls": {"shoulder_width": 0.78, "chest_fullness": 0.78, "belly_fullness": 0.68, "waist_definition": 0.40, "arm_fullness": 0.72, "hip_fullness": 0.68, "thigh_fullness": 0.68, "calf_fullness": 0.62},
    },
    {
        "id": "PROFILE_D_PETITE_FEMININE",
        "gender": "feminine",
        "stature_cm": 161.0,
        "weight_kg": 54.0,
        "target_chest_cm": 86.0,
        "target_waist_cm": 68.0,
        "controls": {"shoulder_width": 0.38, "chest_fullness": 0.45, "belly_fullness": 0.32, "waist_definition": 0.72, "arm_fullness": 0.36, "hip_fullness": 0.55, "thigh_fullness": 0.46, "calf_fullness": 0.42},
    },
    {
        "id": "PROFILE_E_TALL_NEUTRAL",
        "gender": "neutral",
        "stature_cm": 180.0,
        "weight_kg": 72.0,
        "target_chest_cm": 96.0,
        "target_waist_cm": 80.0,
        "controls": {"shoulder_width": 0.52, "chest_fullness": 0.48, "belly_fullness": 0.42, "waist_definition": 0.55, "arm_fullness": 0.46, "hip_fullness": 0.50, "thigh_fullness": 0.48, "calf_fullness": 0.48},
    },
]


def main():
    init_db()
    db = SessionFactory()
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    try:
        prof_srv = ProfileService(db)
        av_srv = AvatarOrchestrationService(db)

        calibration_records = []
        fit_matrix = []

        for spec in TEST_PROFILES:
            p = prof_srv.create_profile(
                requesting_user_id=owner_id,
                presentation_gender=spec["gender"],
                stature_cm=spec["stature_cm"],
                reported_weight_kg=spec["weight_kg"],
                initial_controls=spec["controls"],
            )
            db.commit()

            gen = av_srv.generate_avatar_for_profile(
                profile_id=p.id,
                requesting_user_id=owner_id,
                rigged=True,
            )
            db.commit()

            asset_id = uuid.UUID(gen["avatar_id"])
            asset_model, glb_bytes = av_srv.get_avatar_asset(asset_id=asset_id, requesting_user_id=owner_id)
            rig_info = inspect_glb_rig(glb_bytes)

            # Save test fixture GLBs for Phase 11.1 & 11.3
            (AVATAR_OUT / f"{spec['id']}.glb").write_bytes(glb_bytes)
            (PUB_11 / f"{spec['id']}.glb").write_bytes(glb_bytes)

            ext = gen["extracted_measurements"]
            stature_ext = ext.get("stature", {}).get("value_cm", spec["stature_cm"])
            chest_ext = ext.get("chest_circumference", {}).get("value_cm")
            waist_ext = ext.get("waist_planar_circumference", {}).get("value_cm")
            hip_ext = ext.get("hip_circumference", {}).get("value_cm")
            shoulder_ext = ext.get("shoulder_biacromial_breadth", {}).get("value_cm")

            calibration_records.append({
                "test_profile": spec["id"],
                "profile_id": str(p.id),
                "avatar_id": str(asset_id),
                "sha256": gen["sha256_checksum"],
                "rig": rig_info,
                "target_stature_cm": spec["stature_cm"],
                "extracted_stature_cm": stature_ext,
                "stature_error_cm": round(abs(stature_ext - spec["stature_cm"]), 2) if stature_ext else None,
                "target_chest_cm": spec["target_chest_cm"],
                "extracted_chest_cm": chest_ext,
                "chest_diff_cm": round(chest_ext - spec["target_chest_cm"], 2) if chest_ext else None,
                "target_waist_cm": spec["target_waist_cm"],
                "extracted_waist_cm": waist_ext,
                "waist_diff_cm": round(waist_ext - spec["target_waist_cm"], 2) if waist_ext else None,
                "extracted_hip_cm": hip_ext,
                "extracted_shoulder_cm": shoulder_ext,
            })

            # Evaluate S / M / L fit on this avatar
            size_evals = {}
            for sz, gdim in GARMENT_SIZES.items():
                if chest_ext is None or waist_ext is None or shoulder_ext is None:
                    size_evals[sz] = {"classification": "Insufficient data"}
                else:
                    c_ease = round(gdim["chest_cm"] - chest_ext, 2)
                    w_ease = round(gdim["waist_cm"] - waist_ext, 2)
                    s_ease = round(gdim["shoulder_cm"] - shoulder_ext, 2)
                    size_evals[sz] = {
                        "chest_ease_cm": c_ease,
                        "waist_ease_cm": w_ease,
                        "shoulder_ease_cm": s_ease,
                        "classification": classify_fit(c_ease, w_ease, s_ease),
                    }
            fit_matrix.append({"test_profile": spec["id"], "gender": spec["gender"], "sizes": size_evals})

        # Ownership & privacy check (Phase 11.0.5 / 11.0.7)
        ownership_blocked = False
        try:
            av_srv.get_avatar_asset(asset_id=uuid.UUID(calibration_records[0]["avatar_id"]), requesting_user_id=other_user_id)
        except ForbiddenError as fe:
            ownership_blocked = fe.code == "OWNERSHIP_VIOLATION"

        out_11_0 = {
            "active_body_engine_db": os.environ["MONGODB_BODY_ENGINE_DB"],
            "ownership_isolation_enforced": ownership_blocked,
            "avatars_generated": len(calibration_records),
            "calibration_records": calibration_records,
        }
        (OUT_11_0 / "avatar_calibration_results.json").write_text(json.dumps(out_11_0, indent=2), encoding="utf-8")

        out_11_1 = {
            "profiles_tested": len(fit_matrix),
            "sizes_tested": ["S", "M", "L"],
            "fit_matrix": fit_matrix,
        }
        (OUT_11_1 / "body_shape_fit_matrix.json").write_text(json.dumps(out_11_1, indent=2), encoding="utf-8")

        print("OWNERSHIP_BLOCKED:", ownership_blocked)
        for rec in calibration_records:
            print(rec["test_profile"], "rig:", rec["rig"]["bones"], "bones, stature:", rec["extracted_stature_cm"], "chest:", rec["extracted_chest_cm"], "waist:", rec["extracted_waist_cm"], "shoulder:", rec["extracted_shoulder_cm"])
        for fm in fit_matrix:
            print(fm["test_profile"], {k: v["classification"] for k, v in fm["sizes"].items()})
    finally:
        db.close()


if __name__ == "__main__":
    main()
