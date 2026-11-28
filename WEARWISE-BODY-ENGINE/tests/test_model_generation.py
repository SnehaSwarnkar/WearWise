"""
Test Suite: Model Generation
WearWise Phase 0
"""

import pytest
import torch

def test_model_initialization():
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    assert model is not None
    assert hasattr(model, "phenotype_labels")
    assert len(model.phenotype_labels) >= 5

def test_forward_pass_neutral():
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    pose_params = torch.eye(4, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    pheno = {k: 0.5 for k in model.phenotype_labels}
    
    with torch.no_grad():
        out = model(pose_parameters=pose_params, phenotype_kwargs=pheno)
    
    assert out is not None
    # Model returns dictionary with blendshape_coeffs or vertices
    verts = out.get("vertices", out.get("rest_vertices"))
        
    assert verts is not None
    assert verts.shape[-1] == 3  # (X, Y, Z)
    assert verts.shape[-2] > 1000  # Human mesh has thousands of vertices
