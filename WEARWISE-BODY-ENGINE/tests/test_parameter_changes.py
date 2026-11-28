"""
Test Suite: Parameter Changes & Controllability
WearWise Phase 0
"""

import pytest
import numpy as np
import torch

def test_single_parameter_displacement():
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    pose_params = torch.eye(4, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    base_pheno = {k: 0.5 for k in model.phenotype_labels}
    base_pheno["gender"] = 1.0
    
    with torch.no_grad():
        out_base = model(pose_parameters=pose_params, phenotype_kwargs=base_pheno)
        v_base = out_base.get("vertices", out_base.get("rest_vertices")).cpu().numpy()
        
    # Test varying height
    tall_pheno = dict(base_pheno)
    tall_pheno["height"] = 0.9
    with torch.no_grad():
        out_tall = model(pose_parameters=pose_params, phenotype_kwargs=tall_pheno)
        v_tall = out_tall.get("vertices", out_tall.get("rest_vertices")).cpu().numpy()
        
    diff = np.abs(v_tall - v_base)
    max_disp = np.max(diff)
    mean_disp = np.mean(diff)
    
    assert max_disp > 0.01, f"Expected significant displacement from height change, got max {max_disp}"
    assert mean_disp > 0.001, f"Expected mean displacement > 0.001, got {mean_disp}"

def test_local_change_moderate():
    import anny
    model = anny.Anny(local_changes="default", skinning_method="lbs")
    pose_params = torch.eye(4, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
    
    base_pheno = {k: 0.5 for k in model.phenotype_labels}
    with torch.no_grad():
        out_base = model(pose_parameters=pose_params, phenotype_kwargs=base_pheno)
        v_base = out_base.get("vertices", out_base.get("rest_vertices")).cpu().numpy()
        
    # Check if stomach or abdomen local change exists
    local_candidates = [lbl for lbl in model.local_change_labels if "stomach" in lbl.lower() or "abdomen" in lbl.lower()]
    if local_candidates:
        test_lbl = local_candidates[0]
        with torch.no_grad():
            out_local = model(pose_parameters=pose_params, phenotype_kwargs=base_pheno, local_changes_kwargs={test_lbl: 0.5})
            v_local = out_local.get("vertices", out_local.get("rest_vertices")).cpu().numpy()
            
        disp = np.linalg.norm(v_local - v_base, axis=-1)
        assert np.max(disp) > 0.001, f"Expected non-zero displacement for {test_lbl}, got {np.max(disp)}"
