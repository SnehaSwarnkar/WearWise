"""
Test Suite: Export & Validation
WearWise Phase 0
"""

import pytest
import os
import numpy as np
import torch
import trimesh

def test_glb_export_and_reimport(tmp_path):
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    pose_params = torch.eye(4, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    pheno = {k: 0.5 for k in model.phenotype_labels}
    with torch.no_grad():
        out = model(pose_parameters=pose_params, phenotype_kwargs=pheno)
        v = out.get("vertices", out.get("rest_vertices"))
        
    v_np = v[0].cpu().numpy() if v.dim() == 3 else v.cpu().numpy()
    faces_np = model.faces.cpu().numpy() if hasattr(model, "faces") else model.get_faces().cpu().numpy()
    
    mesh = trimesh.Trimesh(vertices=v_np, faces=faces_np, process=False)
    glb_file = tmp_path / "test_avatar.glb"
    mesh.export(str(glb_file), file_type="glb")
    
    assert os.path.exists(glb_file)
    assert os.path.getsize(glb_file) > 1000
    
    # Independent reload
    reloaded = trimesh.load(str(glb_file), file_type="glb")
    if isinstance(reloaded, trimesh.Scene):
        loaded_mesh = list(reloaded.geometry.values())[0]
    else:
        loaded_mesh = reloaded
        
    assert loaded_mesh is not None
    # Verify geometry equivalence (bounding box matches within tolerance)
    source_extent = v_np.max(axis=0) - v_np.min(axis=0)
    reloaded_extent = loaded_mesh.vertices.max(axis=0) - loaded_mesh.vertices.min(axis=0)
    max_extent_diff = np.max(np.abs(source_extent - reloaded_extent))
    assert max_extent_diff < 1e-3, f"Bounding box mismatch: source {source_extent} vs reloaded {reloaded_extent}"
