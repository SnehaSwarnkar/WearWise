import sys
import torch
import trimesh
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise\WEARWISE-BODY-ENGINE")))
from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.anthropometry.engine import AnthropometryEngine
from app.domain.entities.avatar import MeshData

ad = AnnyAdapter()
ad.initialize()
m = ad.get_model()
eng = AnthropometryEngine()

for w_val, mus_val, bust_lc, waist_lc in [
    (0.5, 0.5, 0.0, 0.0),
    (0.75, 0.65, 0.4, 0.2),
    (0.95, 0.75, 0.8, 0.5),
    (1.0, 0.85, 1.0, 1.0),
    (0.3, 0.35, -0.3, -0.3),
]:
    with torch.no_grad():
        out = m(
            pose_parameters=ad._pose_params,
            phenotype_kwargs={
                "gender": -0.5,
                "age": 0.5,
                "muscle": mus_val,
                "weight": w_val,
                "height": 0.72,
                "proportions": 0.5,
            },
            local_changes_kwargs={
                "measure-bust-circ-incr": bust_lc,
                "measure-waist-circ-incr": waist_lc,
                "torso-scale-horiz-incr": bust_lc * 0.4,
                "torso-scale-depth-incr": bust_lc * 0.4,
            },
        )
    v = out["vertices"][0].cpu().numpy().astype(np.float32)
    v *= 1.785 / float(v[:, 2].max() - v[:, 2].min())
    tm = trimesh.Trimesh(vertices=v, faces=ad._faces, process=False)
    md = MeshData(vertices=v, faces=ad._faces, normals=np.asarray(tm.vertex_normals, dtype=np.float32), metadata={})
    res = eng.extract_all(
        md,
        ad.get_landmark_provider(md),
        "test",
        ("chest_circumference", "waist_planar_circumference", "shoulder_biacromial_breadth"),
    )
    c = float(res.records["chest_circumference"].measurement.value_cm)
    wa = float(res.records["waist_planar_circumference"].measurement.value_cm)
    sh = float(res.records["shoulder_biacromial_breadth"].measurement.value_cm)
    print(f"w={w_val} mus={mus_val} bust={bust_lc} waist={waist_lc} -> chest={c:.2f} cm, waist={wa:.2f} cm, sh={sh:.2f} cm")
