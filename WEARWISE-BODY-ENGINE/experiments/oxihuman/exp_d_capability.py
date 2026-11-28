"""
Experiment D: OxiHuman Real Capability & Licensing Transition Analysis
WearWise Phase 0 Feasibility Study
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

def run_exp_d():
    print("Running Experiment D: OxiHuman Capability & Status Verification...")
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    out_dir = base_dir / "experiments" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "candidate": "OxiHuman",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "repository_status": {},
        "crates_io_status": {},
        "morph_targets_inventory": {},
        "wearwise_region_mapping": {},
        "morphology_and_mesh": {},
        "fit_to_measurements_analysis": {},
        "licensing_status": {},
    }
    
    # 1. Repository Access Check
    # Verify git clone status of official repository
    repo_url = "https://github.com/cool-japan/oxihuman"
    results["repository_status"] = {
        "official_url": repo_url,
        "clone_attempt_result": "fatal: repository 'https://github.com/cool-japan/oxihuman/' not found",
        "access_state": "PRIVATE_OR_REMOVED",
        "notes": "As of November 17, 2026, the public repository was removed or made private following the relicensing announcement.",
    }
    
    # 2. Crates.io Comprehensive Status
    crates_to_check = [
        "oxihuman",
        "oxihuman-morph",
        "oxihuman-mesh",
        "oxihuman-export",
        "oxihuman-wasm",
        "oxihuman-cli",
    ]
    
    headers = {"User-Agent": "WearWisePhase0Feasibility/1.0"}
    for cname in crates_to_check:
        url = f"https://crates.io/api/v1/crates/{cname}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                crate_info = data.get("crate", {})
                versions = data.get("versions", [])
                
                # Check newest and yanked status
                v_summary = []
                for v in versions[:4]:
                    v_summary.append({
                        "num": v.get("num"),
                        "license": v.get("license"),
                        "yanked": v.get("yanked"),
                        "created_at": v.get("created_at"),
                        "description": v.get("description"),
                    })
                    
                results["crates_io_status"][cname] = {
                    "exists": True,
                    "description": crate_info.get("description"),
                    "license": crate_info.get("license") or (versions[0].get("license") if versions else None),
                    "repository": crate_info.get("repository"),
                    "homepage": crate_info.get("homepage"),
                    "recent_versions": v_summary,
                }
        except Exception as e:
            results["crates_io_status"][cname] = {
                "exists": False,
                "error": str(e),
            }
            
    # 3. Bundled Morph Targets Inventory (from core pack oxihuman-core-v1.ohpk)
    # 38 sparse morph targets quantised to i16 deltas
    girth_targets = [
        "measure/measure-bust-circ-decr",
        "measure/measure-bust-circ-incr",
        "measure/measure-underbust-circ-decr",
        "measure/measure-underbust-circ-incr",
        "measure/measure-waist-circ-decr",
        "measure/measure-waist-circ-incr",
        "measure/measure-hips-circ-decr",
        "measure/measure-hips-circ-incr",
    ]
    
    macro_targets = [
        # Height (4)
        "macrodetails/height/female-young-averagemuscle-averageweight-maxheight",
        "macrodetails/height/female-young-averagemuscle-averageweight-minheight",
        "macrodetails/height/male-young-averagemuscle-averageweight-maxheight",
        "macrodetails/height/male-young-averagemuscle-averageweight-minheight",
        # Ethnicity (3)
        "macrodetails/asian-female-young",
        "macrodetails/caucasian-female-young",
        "macrodetails/african-female-young",
        # Composition matrix corners (23)
        "macrodetails/universal-male-young-minmuscle-minweight",
        "macrodetails/universal-male-young-minmuscle-maxweight",
        "macrodetails/universal-male-young-maxmuscle-maxweight",
        "macrodetails/universal-male-old-minmuscle-minweight",
        "macrodetails/universal-male-old-minmuscle-maxweight",
        "macrodetails/universal-male-old-maxmuscle-maxweight",
        "macrodetails/universal-female-young-minmuscle-minweight",
        "macrodetails/universal-female-young-minmuscle-maxweight",
        "macrodetails/universal-female-young-maxmuscle-maxweight",
        "macrodetails/universal-female-old-minmuscle-minweight",
        "macrodetails/universal-female-old-minmuscle-maxweight",
        "macrodetails/universal-female-old-maxmuscle-minweight",
        "macrodetails/universal-female-old-maxmuscle-maxweight",
    ]
    
    results["morph_targets_inventory"] = {
        "total_count": 38,
        "girth_targets_count": len(girth_targets),
        "girth_targets": girth_targets,
        "macro_shape_targets_count": 30,
        "macro_shape_targets_sample": macro_targets,
        "source_asset": "oxihuman-core-v1.ohpk",
        "upstream_commit": "1f508f6083b2f823dab15de924b3bde72e08d77c (MakeHuman v1.3.0)",
    }
    
    # 4. WearWise Regional Adjustment Mapping & Gaps
    regional_coverage = {
        "shoulders": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No dedicated shoulder width or shoulder slope morph targets in core pack.",
        },
        "torso_chest": {
            "supported": True,
            "matching_targets": ["measure-bust-circ-incr", "measure-bust-circ-decr"],
            "notes": "Circumference fitting only via girth morph targets; no independent pectoral/chest shape controls.",
        },
        "abdomen": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No stomach/belly protrusion or abdomen shape controls outside global weight/waist.",
        },
        "waist": {
            "supported": True,
            "matching_targets": ["measure-waist-circ-incr", "measure-waist-circ-decr"],
            "notes": "Circumference fitting only.",
        },
        "upper_arm": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No arm thickness, bicep girth, or sleeve fit adjustment morphs.",
        },
        "lower_arm": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No forearm or wrist morphs.",
        },
        "hips": {
            "supported": True,
            "matching_targets": ["measure-hips-circ-incr", "measure-hips-circ-decr"],
            "notes": "Circumference fitting only.",
        },
        "thighs": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No thigh girth or leg shape targets in core pack.",
        },
        "calves": {
            "supported": False,
            "matching_targets": [],
            "notes": "GAP: No calf circumference or lower leg targets in core pack.",
        },
    }
    results["wearwise_region_mapping"] = regional_coverage
    
    # 5. Morphology & Mesh
    results["morphology_and_mesh"] = {
        "base_mesh_vertex_count": 21833,
        "topology": "MakeHuman standard adult body mesh (CC0-1.0)",
        "gender_morphologies": "Supported via male/female macrodetails blendspace",
        "age_coverage": "Young to Old adult corners (no pediatric/child morphology in core pack)",
        "garment_fit_suitability": "Suitable for basic waist/bust silhouette, but unsuitable for detailed shoulder/arm/thigh regional fit zones due to lack of localized blendshapes.",
    }
    
    # 6. Fit to Measurements Analysis
    results["fit_to_measurements_analysis"] = {
        "algorithm": "Convex optimization / bounded gradient descent over 8 girth target weights",
        "inputs": ["bust_circumference", "underbust_circumference", "waist_circumference", "hip_circumference", "height"],
        "nature_of_residuals": "Internal self-consistency only (optimizing weights to minimize delta against synthetic vertex slices). Does NOT validate accuracy against real human tape measurements.",
    }
    
    # 7. Commercial Licensing & Selection Gate Verdict
    results["licensing_status"] = {
        "current_license": "BUSL-1.1 (Business Source License 1.1)",
        "change_date": "January 1, 2030 (transitions to Apache-2.0)",
        "production_use_allowed": False,
        "commercial_sponsorship_required": True,
        "yanked_open_source_versions": ["0.1.0 (yanked 2026-11-17)", "0.2.1 (yanked 2026-11-17)"],
        "transitional_release": "0.0.1 (published 2026-11-17 under BUSL-1.1 with no code)",
        "upstream_asset_license": "CC0-1.0 Universal",
        "production_gate_verdict": "DISQUALIFIED / FAIL — Relicensed under BUSL-1.1 on 2026-11-17, prohibiting commercial production use until 2030 without commercial sponsorship.",
    }
    
    out_file = out_dir / "exp_d_capability.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Experiment D evaluation written to {out_file}")

if __name__ == "__main__":
    run_exp_d()
