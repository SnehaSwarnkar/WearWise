import json
import sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, r"c:\Users\Lenovo\Documents\Major Project\WearWise\WEARWISE-BODY-ENGINE")
from app.avatar_engine.adapters.anny_adapter import AnnyAdapter

adapter = AnnyAdapter()
adapter.initialize()
model = adapter.get_model()

bones = list(model.bone_labels)
weights = model.dense_vertex_bone_weights.detach().cpu().numpy()
v_tmpl = model.template_vertices.detach().cpu().numpy()

print("BONE_COUNT:", len(bones))
print("BONES:", bones)
print("WEIGHTS_SHAPE:", weights.shape, "ROW_SUM_MIN_MAX:", float(weights.sum(axis=1).min()), float(weights.sum(axis=1).max()))
print("TEMPLATE_BOUNDS_Z_UP:", v_tmpl.min(axis=0).tolist(), v_tmpl.max(axis=0).tolist())
print("HAS_BONE_PARENTS:", hasattr(model, "bone_parents"), getattr(model, "bone_parents", None))
print("FORWARD_SIG_VARS:", model.forward.__code__.co_varnames[:model.forward.__code__.co_argcount])

# Check bone poses / rest_bone_poses
for attr in ["bone_poses", "rest_bone_poses", "default_bone_poses", "phenotype_labels", "local_change_labels"]:
    if hasattr(model, attr):
        val = getattr(model, attr)
        if isinstance(val, torch.Tensor):
            print(attr, "shape:", tuple(val.shape))
        else:
            print(attr, ":", val)

# Test forwarding with neutral vs raised arm pose!
out_rest = model()
print("OUT_KEYS:", list(out_rest.keys()))
if "bone_poses" in out_rest:
    print("OUT_bone_poses shape:", tuple(out_rest["bone_poses"].shape))
if "bone_heads" in out_rest:
    print("OUT_bone_heads shape:", tuple(out_rest["bone_heads"].shape))
if "bone_tails" in out_rest:
    print("OUT_bone_tails shape:", tuple(out_rest["bone_tails"].shape))

info = {
    "bone_count": len(bones),
    "bones": bones,
    "bone_parents": [int(x) for x in model.bone_parents] if hasattr(model, "bone_parents") else None,
    "weights_shape": list(weights.shape),
    "template_bounds_z_up": [v_tmpl.min(axis=0).tolist(), v_tmpl.max(axis=0).tolist()],
    "phenotype_labels": list(getattr(model, "phenotype_labels", [])),
    "local_change_labels": list(getattr(model, "local_change_labels", [])),
    "out_keys": list(out_rest.keys()),
}
out_file = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise\artifacts\phase10_experimental\anny_model_rig_details.json")
out_file.write_text(json.dumps(info, indent=2), encoding="utf-8")
print("WROTE:", out_file)
