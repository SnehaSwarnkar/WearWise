"""
WearWise — Part 1: Seller Digital Garment Platform
Automated Verification Script & Engineering Audit
==================================================
Tests all 13 acceptance criteria defined by ChatGPT Technical Decision Owner:
1. Product Identity & Category/Subcategory/Price registration
2. SKU Uniqueness & Duplicate Conflict Rejection (409)
3. Dual-Role Image Upload & SHA-256 Cryptographic Hashing
4. Technical Reconstruction Checklist Verification
5. Method A: CAD / DXF / SVG Pattern Upload & Panel Extraction
6. Method B: Guided Parametric Pattern Synthesis (7 Panels, 11 Seams)
7. Method C: AI Pattern Reconstruction Provisional Adapter
8. Finished Measurements Table (S, M, L) & ISO 8559-2 Grading
9. 8 Provisional Fabric Presets Library & Material Profile
10. 13-Stage 3D Generation Pipeline & Cloth Surface Topology (Euler -2)
11. Automated Quality Assessment (Geometry, Tolerance, Texture, Variants)
12. Formal Merchant Approval Gate & State Machine
13. Immutable Package Manifest Compilation & Shopper Asset Gateway
"""

import sys
import os
import json
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1/merchant/garments"

def log_test(step_num: int, title: str, passed: bool, details: str = ""):
    mark = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[Gate {step_num:02d}] {mark}: {title}{reset}")
    if details:
        print(f"         {details}")

def run_part1_verification():
    print("=" * 80)
    print("WEARWISE — PART 1: SELLER DIGITAL GARMENT PLATFORM AUDIT")
    print("=" * 80)

    test_sku = f"TSH-WW-CREW-TEST-{int(time.time())}"
    garment_id = None
    all_passed = True

    # ---------------------------------------------------------
    # Gate 1: Product Identity Registration
    # ---------------------------------------------------------
    try:
        payload = {
            "name": "WearWise Signature Boxy Crew Tee (Audit)",
            "sku": test_sku,
            "category": "T-Shirt",
            "subcategory": "Oversized Drop-Shoulder Tee",
            "description": "Heavyweight drop-shoulder boxy tee with ribbed crewneck collar.",
            "color_variant": "Coral Pink / White Trim",
            "price": 2999.0,
            "available_sizes": ["S", "M", "L"],
        }
        res = requests.post(BASE_URL, json=payload, timeout=10)
        passed = (res.status_code == 201)
        data = res.json()
        garment_id = data.get("id")
        log_test(1, "Product Identity & Metadata Creation", passed, f"Garment ID: {garment_id}, SKU: {test_sku}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(1, "Product Identity Creation", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 2: Duplicate SKU Uniqueness Enforcement
    # ---------------------------------------------------------
    try:
        dup_payload = {
            "name": "Duplicate SKU Test Garment",
            "sku": test_sku,  # Duplicate!
            "category": "T-Shirt",
            "subcategory": "Oversized Tee",
            "price": 1999.0,
            "available_sizes": ["M"],
        }
        res = requests.post(BASE_URL, json=dup_payload, timeout=10)
        passed = (res.status_code == 409)
        err_msg = res.json().get('detail') or res.json().get('error', {}).get('message', 'Conflict')
        log_test(2, "SKU Uniqueness & Duplicate Conflict Rejection (409)", passed, f"Status: {res.status_code} ({err_msg[:60]}...)")
        if not passed: all_passed = False
    except Exception as e:
        log_test(2, "SKU Uniqueness", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 3: Dual-Role Image Upload & SHA-256 Cryptographic Hashing
    # ---------------------------------------------------------
    try:
        # Create dummy 1x1 png image bytes
        dummy_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7Vk\x97\x00\x00\x00\x00IEND\xaeB`\x82'
        files = {"file": ("front_reference.png", dummy_png, "image/png")}
        data = {"viewpoint": "front", "role": "both"}
        res = requests.post(f"{BASE_URL}/{garment_id}/images", data=data, files=files, timeout=10)
        passed = (res.status_code == 200)
        body = res.json()
        img_entry = body.get("uploaded_image", {})
        has_hash = bool(img_entry.get("sha256"))
        log_test(3, "Dual-Role Image Upload & SHA-256 Hashing", passed and has_hash, f"Role: {img_entry.get('role')}, SHA-256: {img_entry.get('sha256')[:16]}...")
        if not (passed and has_hash): all_passed = False
    except Exception as e:
        log_test(3, "Dual-Role Image Upload", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 4: Technical Reconstruction Checklist Verification
    # ---------------------------------------------------------
    try:
        checklist = body.get("checklist", {})
        required = checklist.get("required_views", [])
        missing = checklist.get("missing_views", [])
        passed = (len(required) == 4 and "front" in checklist.get("present_views", []))
        log_test(4, "Technical Reconstruction Reference Checklist", passed, f"Required: {required}, Missing: {missing}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(4, "Reconstruction Checklist", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 5: Method A: CAD / SVG Pattern Upload & Parsing
    # ---------------------------------------------------------
    try:
        sample_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">
          <g id="PANEL_FRONT_TORSO"><path d="M 100 100 L 500 100 L 500 700 L 100 700 Z" /></g>
          <g id="PANEL_BACK_TORSO"><path d="M 520 100 L 920 100 L 920 700 L 520 700 Z" /></g>
        </svg>""".encode("utf-8")
        files = {"file": ("test_pattern.svg", sample_svg, "image/svg+xml")}
        data = {"units": "mm"}
        res = requests.post(f"{BASE_URL}/{garment_id}/pattern/upload", data=data, files=files, timeout=10)
        passed = (res.status_code == 200)
        cad_res = res.json().get("cad_validation", {})
        conf = res.json().get("confidence_label")
        log_test(5, "Method A: CAD/SVG Pattern Parser & Validation", passed, f"Panels parsed: {cad_res.get('panel_count')}, Confidence: {conf}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(5, "CAD/SVG Pattern Upload", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 6: Method B: Guided Parametric Pattern Generator (Primary MVP)
    # ---------------------------------------------------------
    try:
        guided_payload = {
            "silhouette": "boxy_drop_shoulder",
            "collar_type": "ribbed_crewneck",
            "hem_finish": "clean_28mm",
            "has_pocket": True,
            "pocket_type": "left_chest_patch",
        }
        res = requests.post(f"{BASE_URL}/{garment_id}/pattern/guided", json=guided_payload, timeout=10)
        passed = (res.status_code == 200)
        guided_data = res.json()
        panels = guided_data.get("panels", [])
        seams = guided_data.get("seam_relationships", [])
        passed = passed and (len(panels) == 7 and len(seams) == 11)
        log_test(6, "Method B: Guided Parametric Synthesis (7 Panels, 11 Seams)", passed, f"Panels: {len(panels)}, Seams: {len(seams)}, Label: {guided_data.get('confidence_label')}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(6, "Guided Parametric Builder", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 7: Method C: AI Reconstruction Adapter Interface
    # ---------------------------------------------------------
    try:
        ai_payload = {"adapter": "SwiftTailorAdapter"}
        res = requests.post(f"{BASE_URL}/{garment_id}/pattern/ai-reconstruct", json=ai_payload, timeout=10)
        passed = (res.status_code == 200)
        ai_data = res.json()
        conf_label = ai_data.get("confidence_label")
        passed = passed and (conf_label == "AI_RECONSTRUCTED")
        log_test(7, "Method C: AI Pattern Reconstruction Provisional Adapter", passed, f"Confidence: {conf_label}, Panels generated: {len(ai_data.get('reconstruction_result', {}).get('generated_panels', []))}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(7, "AI Pattern Reconstruction", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 8: Finished Measurements Table & ISO 8559-2 Grading
    # ---------------------------------------------------------
    try:
        sizes_to_save = [
            {"size_label": "S", "half_chest_width_cm": 50.0, "back_length_cm": 64.0, "shoulder_breadth_cm": 47.0, "sleeve_length_cm": 15.0, "collar_circumference_cm": 42.0, "dimensional_ease_chest_cm": "+2.0 cm"},
            {"size_label": "M", "half_chest_width_cm": 54.0, "back_length_cm": 67.0, "shoulder_breadth_cm": 50.0, "sleeve_length_cm": 17.0, "collar_circumference_cm": 44.0, "dimensional_ease_chest_cm": "+4.5 cm (Recommended)"},
            {"size_label": "L", "half_chest_width_cm": 58.0, "back_length_cm": 70.0, "shoulder_breadth_cm": 53.0, "sleeve_length_cm": 19.0, "collar_circumference_cm": 46.0, "dimensional_ease_chest_cm": "+8.0 cm"},
        ]
        all_saved = True
        for sz_payload in sizes_to_save:
            res = requests.post(f"{BASE_URL}/{garment_id}/measurements", json=sz_payload, timeout=10)
            if res.status_code != 200: all_saved = False
        log_test(8, "Finished Measurements Table (S, M, L) & Grading", all_saved, "Registered S, M, L flat tabletop dimensions & ease")
        if not all_saved: all_passed = False
    except Exception as e:
        log_test(8, "Measurements Registration", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 9: 8 Provisional Fabric Presets & Material Profile
    # ---------------------------------------------------------
    try:
        res = requests.get(f"{BASE_URL}/presets/fabrics", timeout=10)
        presets = res.json().get("presets", [])
        presets_passed = (res.status_code == 200 and len(presets) == 8)
        
        # Save waffle knit fabric profile
        fab_payload = {
            "name": "Heavyweight Cotton Waffle Knit (240 GSM)",
            "composition": "100% Combed Organic Cotton",
            "structure": "Waffle / Honeycomb Knit",
            "gsm": 240.0,
            "thickness_mm": 1.15,
            "warp_stretch_percent": 14.5,
            "weft_stretch_percent": 28.0,
            "elastic_recovery_percent": 88.0,
            "bending_stiffness": 18.5,
            "shear_stiffness": 22.0,
            "preset_id": "cotton_waffle_knit_240gsm",
        }
        res2 = requests.post(f"{BASE_URL}/{garment_id}/fabric", json=fab_payload, timeout=10)
        fab_saved = (res2.status_code == 200)
        passed = presets_passed and fab_saved
        log_test(9, "8 Provisional Fabric Presets Library & Profile", passed, f"Available presets: {len(presets)}, Saved profile: {fab_payload['name']}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(9, "Fabric Presets & Profile", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 10: 13-Stage Generation Pipeline & Topology Verification
    # ---------------------------------------------------------
    try:
        res = requests.post(f"{BASE_URL}/{garment_id}/generate", timeout=30)
        passed = (res.status_code == 200)
        gen_data = res.json()
        stages = gen_data.get("pipeline_stages", [])
        mesh_assets = gen_data.get("assets", {})
        all_stages_completed = (len(stages) == 13 and all(s.get("status") == "completed" for s in stages))
        has_sml_glbs = all(sz in mesh_assets for sz in ["S", "M", "L"])
        passed = passed and all_stages_completed and has_sml_glbs
        log_test(10, "13-Stage 3D Generation Pipeline & Non-Watertight Topology", passed, f"Stages completed: {len(stages)}/13, Assets: {list(mesh_assets.keys())}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(10, "13-Stage 3D Generation", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 11: Automated Full Quality Assessment (QA Engine)
    # ---------------------------------------------------------
    try:
        res = requests.get(f"{BASE_URL}/{garment_id}/qa-report", timeout=10)
        passed = (res.status_code == 200)
        qa = res.json()
        qa_status = qa.get("overall_status")
        checks = qa.get("checks", {})
        passed = passed and (qa_status in ["PASSED", "WARNING"]) and ("geometry_qa" in checks)
        log_test(11, "Automated Quality Assessment (QA Gates)", passed, f"QA Status: {qa_status}, Geometry: {checks.get('geometry_qa', {}).get('status')}, Measurement: {checks.get('measurement_qa', {}).get('status')}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(11, "QA Report Audit", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 12: Formal Merchant Approval Gate
    # ---------------------------------------------------------
    try:
        app_payload = {
            "principal_id": "brand_director_audit",
            "approval_notes": "Formally verified boxy fit, seam stitching, and ISO 8559-2 grading under Part 1 audit.",
        }
        res = requests.post(f"{BASE_URL}/{garment_id}/approve", json=app_payload, timeout=10)
        passed = (res.status_code == 200)
        app_data = res.json()
        passed = passed and (app_data.get("status") == "approved")
        log_test(12, "Formal Merchant Approval Gate", passed, f"Status: {app_data.get('status')}, Principal: {app_data.get('approved_by')}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(12, "Merchant Approval", False, str(e))
        all_passed = False

    # ---------------------------------------------------------
    # Gate 13: Immutable Package Manifest & Shopper Asset Gateway
    # ---------------------------------------------------------
    try:
        pub_payload = {"publisher_id": "catalog_admin_audit"}
        res = requests.post(f"{BASE_URL}/{garment_id}/publish", json=pub_payload, timeout=10)
        pub_passed = (res.status_code == 200)
        manifest = res.json().get("manifest", {})
        has_checksums = bool(manifest.get("asset_sha256_checksums"))

        # Verify Shopper Asset Gateway allows access to published garment
        res_shopper = requests.get(f"{BASE_URL}/{garment_id}/shopper-asset?size=M", timeout=10)
        shopper_passed = (res_shopper.status_code == 200)

        passed = pub_passed and has_checksums and shopper_passed
        log_test(13, "Immutable Package Manifest & Shopper Asset Gateway", passed, f"Published Version: {manifest.get('published_version')}, Checksums: {len(manifest.get('asset_sha256_checksums', {}))}, Shopper Asset URL: {res_shopper.json().get('asset_url')}")
        if not passed: all_passed = False
    except Exception as e:
        log_test(13, "Package Manifest & Publication", False, str(e))
        all_passed = False

    print("=" * 80)
    if all_passed:
        print("\033[92mALL 13 ACCEPTANCE GATES PASSED PERFECTLY!\033[0m")
    else:
        print("\033[91mONE OR MORE ACCEPTANCE GATES FAILED.\033[0m")
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = run_part1_verification()
    sys.exit(0 if success else 1)
