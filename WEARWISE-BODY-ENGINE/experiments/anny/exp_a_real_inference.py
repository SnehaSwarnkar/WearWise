"""
Experiment A: Anny Real Inference & Geometry Verification
WearWise Phase 0 Feasibility Study
"""

import json
import os
import sys
import time
from pathlib import Path
import numpy as np

def run_exp_a():
    results = {
        "candidate": "Anny",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "initialization": {},
        "labels": {},
        "baselines": {},
        "variations": {},
        "glb_validation": {},
    }
    
    # 1. Imports and version checks
    import torch
    import anny
    import trimesh
    
    results["versions"] = {
        "anny": getattr(anny, "__version__", "unknown"),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "trimesh": trimesh.__version__,
    }
    print(f"Loaded Anny {results['versions']['anny']}, PyTorch {results['versions']['torch']}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    results["device_used"] = device
    
    # 2. Model Initialization
    t0 = time.perf_counter()
    # Pinned to native Anny topology with default local changes
    model = anny.Anny(local_changes="default", skinning_method="lbs").to(device=device, dtype=torch.float32)
    init_time = time.perf_counter() - t0
    results["initialization"]["init_time_seconds"] = init_time
    print(f"Model initialized in {init_time:.4f} s on {device}")
    
    # 3. Parameter labels inventory
    pheno_labels = list(model.phenotype_labels)
    local_labels = list(model.local_change_labels)
    bone_labels = list(model.bone_labels) if hasattr(model, "bone_labels") else []
    facial_labels = list(model.facial_action_labels) if hasattr(model, "facial_action_labels") else []
    
    results["labels"] = {
        "phenotype_labels": pheno_labels,
        "phenotype_count": len(pheno_labels),
        "local_change_labels": local_labels,
        "local_change_count": len(local_labels),
        "bone_labels": bone_labels,
        "bone_count": len(bone_labels),
        "facial_action_labels": facial_labels,
        "facial_action_count": len(facial_labels),
    }
    print(f"Discovered: {len(pheno_labels)} phenotype labels, {len(local_labels)} local change labels, {len(bone_labels)} bones")
    
    # 4. Identity pose parameters
    # bone_count: 104 bones in Anny rig
    pose_params = torch.eye(4, device=device, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    # Output directories
    base_dir = Path(__file__).resolve().parent.parent.parent
    mesh_dir = base_dir / "artifacts" / "meshes"
    glb_dir = base_dir / "artifacts" / "glb"
    out_dir = base_dir / "experiments" / "outputs"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    glb_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_mesh(name, phenotype_dict, local_dict=None):
        if local_dict is None:
            local_dict = {}
        
        # Ensure all phenotype parameters exist
        full_pheno = {k: 0.5 for k in pheno_labels}
        full_pheno.update(phenotype_dict)
        
        t_infer_0 = time.perf_counter()
        with torch.no_grad():
            out = model(
                pose_parameters=pose_params,
                phenotype_kwargs=full_pheno,
                local_changes_kwargs=local_dict,
            )
            # Retrieve rest vertices or deformed vertices
            if "vertices" in out:
                verts_tensor = out["vertices"]
            elif "rest_vertices" in out:
                verts_tensor = out["rest_vertices"]
            else:
                rest_model = model.get_rest_model(out["blendshape_coeffs"])
                verts_tensor = rest_model["rest_vertices"]
                
        infer_time = time.perf_counter() - t_infer_0
        
        # Squeeze batch dimension if present
        if verts_tensor.dim() == 3:
            verts_np = verts_tensor[0].detach().cpu().numpy()
        else:
            verts_np = verts_tensor.detach().cpu().numpy()
            
        faces_np = model.faces.detach().cpu().numpy() if hasattr(model, "faces") else model.get_faces().cpu().numpy()
        
        # Compute bounding box and orientation
        min_bound = verts_np.min(axis=0).tolist()
        max_bound = verts_np.max(axis=0).tolist()
        extent = (verts_np.max(axis=0) - verts_np.min(axis=0)).tolist()
        center = verts_np.mean(axis=0).tolist()
        
        # Identify axes: largest extent is usually vertical
        largest_dim = int(np.argmax(extent))
        axis_names = ["X", "Y", "Z"]
        vertical_axis = axis_names[largest_dim]
        
        mesh_meta = {
            "name": name,
            "phenotype_params": full_pheno,
            "local_changes": local_dict,
            "inference_time_seconds": infer_time,
            "vertex_count": int(verts_np.shape[0]),
            "face_count": int(faces_np.shape[0]),
            "bbox_min": min_bound,
            "bbox_max": max_bound,
            "extent": extent,
            "center": center,
            "vertical_axis": vertical_axis,
            "height_coordinate_span": extent[largest_dim],
        }
        
        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=verts_np, faces=faces_np, process=False)
        
        # Save OBJ
        obj_path = mesh_dir / f"{name}.obj"
        mesh.export(str(obj_path))
        mesh_meta["obj_path"] = str(obj_path)
        mesh_meta["obj_size_bytes"] = os.path.getsize(obj_path)
        
        # Save GLB
        glb_path = glb_dir / f"{name}.glb"
        mesh.export(str(glb_path), file_type="glb")
        mesh_meta["glb_path"] = str(glb_path)
        mesh_meta["glb_size_bytes"] = os.path.getsize(glb_path)
        
        # Independent validation by re-loading GLB
        t_val_0 = time.perf_counter()
        reloaded = trimesh.load(str(glb_path), file_type="glb")
        val_time = time.perf_counter() - t_val_0
        
        # A glb scene or geometry might be returned
        if isinstance(reloaded, trimesh.Scene):
            geoms = list(reloaded.geometry.values())
            loaded_mesh = geoms[0] if len(geoms) > 0 else None
        else:
            loaded_mesh = reloaded
            
        if loaded_mesh is not None:
            reloaded_extent = (loaded_mesh.vertices.max(axis=0) - loaded_mesh.vertices.min(axis=0)).tolist()
            extent_diff = np.max(np.abs(np.array(extent) - np.array(reloaded_extent)))
            valid_geom = bool(extent_diff < 1e-3)
            
            validation_info = {
                "validated": True,
                "reloaded_vertex_count": int(loaded_mesh.vertices.shape[0]),
                "reloaded_face_count": int(loaded_mesh.faces.shape[0]),
                "reloaded_extent": reloaded_extent,
                "max_extent_diff": float(extent_diff),
                "geometry_equivalent": valid_geom,
                "validation_time_seconds": val_time,
                "has_degenerate_faces": bool(np.any(loaded_mesh.area_faces <= 0)),
                "has_nan": bool(np.isnan(loaded_mesh.vertices).any()),
                "has_inf": bool(np.isinf(loaded_mesh.vertices).any()),
            }
        else:
            validation_info = {"validated": False, "error": "No mesh found in reloaded scene"}
            
        mesh_meta["validation"] = validation_info
        return mesh_meta, verts_np, faces_np
        
    # 5. Generate Reference Baselines
    print("\n--- Generating Baselines ---")
    male_base_meta, male_v, faces = generate_mesh(
        "anny_baseline_male",
        {"gender": 1.0, "age": 0.5, "height": 0.5, "weight": 0.5, "muscle": 0.5, "proportions": 0.5}
    )
    female_base_meta, female_v, _ = generate_mesh(
        "anny_baseline_female",
        {"gender": 0.0, "age": 0.5, "height": 0.5, "weight": 0.5, "muscle": 0.5, "proportions": 0.5}
    )
    results["baselines"]["male"] = male_base_meta
    results["baselines"]["female"] = female_base_meta
    print(f"Male baseline: {male_base_meta['vertex_count']} verts, {male_base_meta['face_count']} faces, span: {male_base_meta['height_coordinate_span']:.4f}")
    print(f"Female baseline: {female_base_meta['vertex_count']} verts, {female_base_meta['face_count']} faces, span: {female_base_meta['height_coordinate_span']:.4f}")

    # 6. Generate 5 Distinct Variations
    print("\n--- Generating Variations ---")
    var_specs = [
        ("anny_var1_tall_lean_male", {"gender": 1.0, "height": 0.9, "weight": 0.2, "muscle": 0.3, "age": 0.5, "proportions": 0.5}),
        ("anny_var2_athletic_female", {"gender": 0.0, "height": 0.6, "weight": 0.5, "muscle": 0.85, "age": 0.5, "proportions": 0.5}),
        ("anny_var3_short_heavy_male", {"gender": 1.0, "height": 0.2, "weight": 0.85, "muscle": 0.3, "age": 0.5, "proportions": 0.5}),
        ("anny_var4_elderly_female", {"gender": 0.0, "age": 0.9, "height": 0.45, "weight": 0.6, "muscle": 0.2, "proportions": 0.5}),
        ("anny_var5_exaggerated_proportions_male", {"gender": 1.0, "proportions": 0.9, "height": 0.75, "weight": 0.4, "muscle": 0.5, "age": 0.5}),
    ]
    
    for vname, vparams in var_specs:
        vmeta, _, _ = generate_mesh(vname, vparams)
        results["variations"][vname] = vmeta
        print(f"Generated {vname}: span={vmeta['height_coordinate_span']:.4f}, GLB size={vmeta['glb_size_bytes']} bytes")
        
    # Save results
    out_file = out_dir / "exp_a_real_inference.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nExperiment A completed successfully! Results written to {out_file}")

if __name__ == "__main__":
    run_exp_a()
