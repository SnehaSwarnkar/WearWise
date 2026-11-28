"""
Test Suite: Mesh Validity
WearWise Phase 0
"""

import pytest
import numpy as np
import torch

def test_mesh_validity_baseline():
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    pose_params = torch.eye(4, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    # Test both male and female
    for gender in [0.0, 1.0]:
        pheno = {k: 0.5 for k in model.phenotype_labels}
        pheno["gender"] = gender
        with torch.no_grad():
            out = model(pose_parameters=pose_params, phenotype_kwargs=pheno)
            v_tensor = out.get("vertices", out.get("rest_vertices"))
            
        v_np = v_tensor[0].cpu().numpy() if v_tensor.dim() == 3 else v_tensor.cpu().numpy()
        faces_np = model.faces.cpu().numpy() if hasattr(model, "faces") else model.get_faces().cpu().numpy()
        
        # 1. Non-empty
        assert len(v_np) > 5000, f"Expected >5000 vertices, got {len(v_np)}"
        assert len(faces_np) > 5000, f"Expected >5000 faces, got {len(faces_np)}"
        
        # 2. No NaN or Inf
        assert not np.isnan(v_np).any(), f"NaN found in vertices for gender={gender}"
        assert not np.isinf(v_np).any(), f"Inf found in vertices for gender={gender}"
        
        # 3. Valid bounding box (extent > 0 in all 3 dims)
        extent = v_np.max(axis=0) - v_np.min(axis=0)
        assert np.all(extent > 0.05), f"Degenerate bounding box extent: {extent}"
