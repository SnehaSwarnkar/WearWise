"""
Experiment B: Anny Parameter Behaviour & Spillover Analysis
WearWise Phase 0 Feasibility Study
"""

import json
import os
import sys
import time
from pathlib import Path
import numpy as np

def run_exp_b():
    import torch
    import anny
    import trimesh
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running Experiment B on {device}...")
    
    # 1. Initialize Anny
    model = anny.Anny(local_changes="default", skinning_method="lbs").to(device=device, dtype=torch.float32)
    pose_params = torch.eye(4, device=device, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    pheno_labels = list(model.phenotype_labels)
    local_labels = list(model.local_change_labels)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    mesh_dir = base_dir / "artifacts" / "meshes"
    glb_dir = base_dir / "artifacts" / "glb"
    out_dir = base_dir / "experiments" / "outputs"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    glb_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Helper to run forward pass and get vertices
    def get_vertices(pheno_kwargs, local_kwargs):
        full_pheno = {k: 0.5 for k in pheno_labels}
        full_pheno.update(pheno_kwargs)
        with torch.no_grad():
            out = model(
                pose_parameters=pose_params,
                phenotype_kwargs=full_pheno,
                local_changes_kwargs=local_kwargs,
            )
            if "vertices" in out:
                v = out["vertices"]
            elif "rest_vertices" in out:
                v = out["rest_vertices"]
            else:
                rest_m = model.get_rest_model(out["blendshape_coeffs"])
                v = rest_m["rest_vertices"]
        if v.dim() == 3:
            v_np = v[0].detach().cpu().numpy()
        else:
            v_np = v.detach().cpu().numpy()
        return v_np

    # 3. Establish Baseline
    # Documented baseline: Male gender=1.0, age=0.5, height=0.5, weight=0.5, muscle=0.5, proportions=0.5
    baseline_pheno = {"gender": 1.0, "age": 0.5, "height": 0.5, "weight": 0.5, "muscle": 0.5, "proportions": 0.5}
    baseline_local = {}
    base_verts = get_vertices(baseline_pheno, baseline_local)
    faces_np = model.faces.detach().cpu().numpy() if hasattr(model, "faces") else model.get_faces().cpu().numpy()
    
    # 4. Determine Coordinate Orientation & Regional Segmentation
    # Measure extents
    min_b = base_verts.min(axis=0)
    max_b = base_verts.max(axis=0)
    extent = max_b - min_b
    vert_axis = int(np.argmax(extent))  # 0=X, 1=Y, 2=Z
    axis_names = ["X", "Y", "Z"]
    print(f"Determined vertical axis: {axis_names[vert_axis]} (extent: {extent[vert_axis]:.4f})")
    
    # Anatomical height segmentation along vertical axis
    # Height goes from min_b[vert_axis] (feet) to max_b[vert_axis] (top of head)
    h_min = min_b[vert_axis]
    h_max = max_b[vert_axis]
    h_total = h_max - h_min
    
    # Relative height zones:
    # 0.00 - 0.15 : feet & ankles
    # 0.15 - 0.32 : calves & lower legs
    # 0.32 - 0.52 : thighs & knees
    # 0.52 - 0.62 : hips & pelvis
    # 0.62 - 0.72 : abdomen / waist
    # 0.72 - 0.85 : torso / chest / shoulders
    # 0.85 - 1.00 : neck & head
    v_norm = (base_verts[:, vert_axis] - h_min) / h_total
    
    # Also define lateral distance from center line for arms vs torso
    # Center along lateral axis (usually axis 0 = X)
    lat_axis = 0 if vert_axis != 0 else 1
    lat_center = (min_b[lat_axis] + max_b[lat_axis]) / 2.0
    lat_dist = np.abs(base_verts[:, lat_axis] - lat_center)
    lat_max = extent[lat_axis] / 2.0
    
    region_masks = {
        "calves": (v_norm >= 0.12) & (v_norm < 0.32),
        "thighs": (v_norm >= 0.32) & (v_norm < 0.52),
        "hips": (v_norm >= 0.52) & (v_norm < 0.62),
        "waist_abdomen": (v_norm >= 0.62) & (v_norm < 0.72),
        "torso_chest": (v_norm >= 0.72) & (v_norm < 0.86) & (lat_dist < 0.45 * lat_max),
        "shoulders": (v_norm >= 0.78) & (v_norm < 0.87) & (lat_dist >= 0.35 * lat_max),
        "arms": (v_norm >= 0.45) & (v_norm < 0.80) & (lat_dist >= 0.45 * lat_max),
        "head_neck": (v_norm >= 0.86),
    }
    
    print("Region vertex counts:")
    for rname, rmask in region_masks.items():
        print(f"  {rname}: {np.sum(rmask)} vertices")
        
    # 5. Identify matching parameters for each WearWise editing group
    # We will search the discovered local_labels for key patterns
    test_plan = []
    
    # A. Phenotype parameters (sweep: 0.0, 0.25, 0.75, 1.0 against 0.5 baseline)
    pheno_sweep = [0.0, 0.25, 0.75, 1.0]
    for p in ["height", "weight", "muscle", "proportions"]:
        if p in pheno_labels:
            test_plan.append({
                "name": p,
                "type": "phenotype",
                "category": p,
                "target_region": "global" if p != "proportions" else "torso_limbs",
                "sweep": pheno_sweep,
                "range": [0.0, 1.0],
                "default": 0.5,
            })
            
    # B. Local changes: identify candidate keys
    # Search local labels for relevant substrings
    keywords = {
        "shoulders": ["shoulder"],
        "torso_chest": ["torso", "chest", "breast", "pectoral"],
        "waist_abdomen": ["stomach", "abdomen", "waist", "belly"],
        "upper_arm": ["upperarm", "arm"],
        "lower_arm": ["forearm", "lowerarm", "wrist"],
        "hips": ["hip", "buttock", "pelvis"],
        "thighs": ["thigh", "upperleg"],
        "calves": ["calf", "lowerleg"],
    }
    
    selected_locals = {}
    for region, kw_list in keywords.items():
        matches = [lbl for lbl in local_labels if any(k in lbl.lower() for k in kw_list)]
        selected_locals[region] = matches
        print(f"Found {len(matches)} local changes for {region}: {matches[:4]}")
        
    # Pick representative parameters for each region to test rigorously
    # Per directive: sweep [-0.5, +0.5] first, then [-1.0, +1.0] only if moderate passes
    local_sweep_moderate = [-0.5, 0.5]
    local_sweep_extreme = [-1.0, 1.0]
    
    for region, matches in selected_locals.items():
        # Pick up to 2 distinct controls per region, including L/R if available
        for lbl in matches[:2]:
            test_plan.append({
                "name": lbl,
                "type": "local_change",
                "category": region,
                "target_region": region,
                "sweep_moderate": local_sweep_moderate,
                "sweep_extreme": local_sweep_extreme,
                "range": [-1.0, 1.0],
                "default": 0.0,
            })
            
    matrix = []
    
    # 6. Execute parameter tests
    print(f"\n--- Testing {len(test_plan)} parameters systematically ---")
    for item in test_plan:
        pname = item["name"]
        ptype = item["type"]
        target_r = item["target_region"]
        
        row = {
            "parameter_name": pname,
            "type": ptype,
            "category": item["category"],
            "target_region": target_r,
            "range": item["range"],
            "sweeps_evaluated": [],
            "max_target_displacement": 0.0,
            "max_spillover_displacement": 0.0,
            "spillover_ratio": 0.0,
            "lr_independent": bool("l-" in pname or "r-" in pname or "-l" in pname or "-r" in pname),
            "valid_geometry": True,
            "plausibility_notes": "",
        }
        
        if ptype == "phenotype":
            sweep_vals = item["sweep"]
        else:
            sweep_vals = item["sweep_moderate"]
            
        for val in sweep_vals:
            if ptype == "phenotype":
                test_p = {pname: val}
                test_l = {}
            else:
                test_p = {}
                test_l = {pname: val}
                
            v_test = get_vertices(test_p, test_l)
            
            # Compute displacement vector and norm per vertex
            disp_vectors = v_test - base_verts
            disp_norms = np.linalg.norm(disp_vectors, axis=1)  # shape (N,)
            
            mean_disp = float(np.mean(disp_norms))
            max_disp = float(np.max(disp_norms))
            
            # Regional displacement breakdown
            regional_means = {}
            for rname, rmask in region_masks.items():
                if np.sum(rmask) > 0:
                    regional_means[rname] = float(np.mean(disp_norms[rmask]))
                else:
                    regional_means[rname] = 0.0
                    
            # Check validity
            has_nan = bool(np.isnan(v_test).any())
            has_inf = bool(np.isinf(v_test).any())
            is_valid = not (has_nan or has_inf)
            
            # Export a sample GLB for moderate positive change
            sample_glb_path = None
            if (ptype == "phenotype" and val == 0.75) or (ptype == "local_change" and val == 0.5):
                safe_name = pname.replace("/", "_").replace(":", "_")
                sample_mesh = trimesh.Trimesh(vertices=v_test, faces=faces_np, process=False)
                sample_path = glb_dir / f"anny_param_{safe_name}.glb"
                sample_mesh.export(str(sample_path), file_type="glb")
                sample_glb_path = str(sample_path)
                
            sweep_result = {
                "val": val,
                "mean_displacement": mean_disp,
                "max_displacement": max_disp,
                "regional_means": regional_means,
                "is_valid": is_valid,
                "sample_glb": sample_glb_path,
            }
            row["sweeps_evaluated"].append(sweep_result)
            
            if max_disp > row["max_target_displacement"]:
                row["max_target_displacement"] = max_disp
                
        # If moderate local-change sweep passed without NaN/Inf, test extreme values
        if ptype == "local_change" and row["valid_geometry"]:
            for val in item["sweep_extreme"]:
                test_p = {}
                test_l = {pname: val}
                v_test = get_vertices(test_p, test_l)
                disp_vectors = v_test - base_verts
                disp_norms = np.linalg.norm(disp_vectors, axis=1)
                is_valid = not (bool(np.isnan(v_test).any()) or bool(np.isinf(v_test).any()))
                row["sweeps_evaluated"].append({
                    "val": val,
                    "mean_displacement": float(np.mean(disp_norms)),
                    "max_displacement": float(np.max(disp_norms)),
                    "is_valid": is_valid,
                    "is_extreme": True,
                })
                
        # Compute spillover ratio (spillover displacement outside target vs inside target)
        if target_r in region_masks:
            t_mask = region_masks[target_r]
            non_t_mask = ~t_mask
            # Take displacement at moderate val
            mod_res = row["sweeps_evaluated"][1] if len(row["sweeps_evaluated"]) > 1 else row["sweeps_evaluated"][0]
            # Use regional means
            t_disp = mod_res["regional_means"].get(target_r, 0.0)
            other_disps = [v for k, v in mod_res["regional_means"].items() if k != target_r]
            max_other = max(other_disps) if other_disps else 0.0
            row["max_spillover_displacement"] = max_other
            row["spillover_ratio"] = float(max_other / (t_disp + 1e-8))
            row["plausibility_notes"] = f"Target disp: {t_disp:.4f}, max non-target: {max_other:.4f} (ratio: {row['spillover_ratio']:.2f})"
        else:
            row["plausibility_notes"] = "Global phenotypic parameter"
            
        matrix.append(row)
        print(f"Tested {pname} ({ptype}): max disp={row['max_target_displacement']:.4f}, {row['plausibility_notes']}")
        
    out_file = out_dir / "exp_b_parameter_behaviour.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)
    print(f"\nExperiment B completed! Matrix written to {out_file}")

if __name__ == "__main__":
    run_exp_b()
