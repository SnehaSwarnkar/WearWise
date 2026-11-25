import json
from pathlib import Path
import numpy as np
import pygltflib
import trimesh

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
ANNY_GLB = REPO / "frontend" / "public" / "avatars" / "anny_baseline_male.glb"
GARMENT_GLB = REPO / "WEARWISE-BODY-ENGINE" / "artifacts" / "merchant_patterns" / "graded_m2rc" / "M" / "TSH-WW-CREW-001_M_candidate_rev3.glb"
OUT_PATH = REPO / "artifacts" / "phase10_experimental" / "rig_and_garment_inspection.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def inspect_glb(path: Path, label: str):
    gltf = pygltflib.GLTF2().load(str(path))
    sc = trimesh.load(str(path), force="scene", process=False)

    nodes_info = []
    for idx, n in enumerate(gltf.nodes or []):
        nodes_info.append({
            "index": idx,
            "name": n.name,
            "mesh": n.mesh,
            "skin": n.skin,
            "children": n.children or [],
            "translation": n.translation,
            "rotation": n.rotation,
            "scale": n.scale,
        })

    skins_info = []
    for s_idx, sk in enumerate(gltf.skins or []):
        joint_names = [gltf.nodes[j].name if j < len(gltf.nodes) else f"node_{j}" for j in (sk.joints or [])]
        skins_info.append({
            "index": s_idx,
            "name": sk.name,
            "skeleton": sk.skeleton,
            "joint_count": len(sk.joints or []),
            "joints": joint_names,
        })

    meshes_info = []
    for m_idx, m in enumerate(gltf.meshes or []):
        prim_info = []
        for p in (m.primitives or []):
            attrs = {k: v for k, v in p.attributes.__dict__.items() if v is not None}
            prim_info.append({
                "attributes": list(attrs.keys()),
                "has_joints_0": "JOINTS_0" in attrs,
                "has_weights_0": "WEIGHTS_0" in attrs,
                "targets_count": len(p.targets or []),
            })
        meshes_info.append({"index": m_idx, "name": m.name, "primitives": prim_info})

    geom_stats = {}
    total_v, total_f = 0, 0
    for gname, gmesh in sc.geometry.items():
        v = len(gmesh.vertices)
        f = len(gmesh.faces)
        total_v += v
        total_f += f
        geom_stats[gname] = {
            "vertices": v,
            "faces": f,
            "bounds_min_m": [round(float(x), 4) for x in gmesh.bounds[0]],
            "bounds_max_m": [round(float(x), 4) for x in gmesh.bounds[1]],
            "is_watertight": bool(gmesh.is_watertight),
            "has_vertex_normals": gmesh.vertex_normals is not None and len(gmesh.vertex_normals) == v,
        }

    return {
        "label": label,
        "file": str(path),
        "bytes": path.stat().st_size,
        "node_count": len(gltf.nodes or []),
        "nodes": nodes_info,
        "skin_count": len(gltf.skins or []),
        "skins": skins_info,
        "animation_count": len(gltf.animations or []),
        "mesh_count": len(gltf.meshes or []),
        "meshes": meshes_info,
        "total_vertices": total_v,
        "total_faces": total_f,
        "scene_bounds_min_m": [round(float(x), 4) for x in sc.bounds[0]],
        "scene_bounds_max_m": [round(float(x), 4) for x in sc.bounds[1]],
        "geometries": geom_stats,
    }


out = {
    "anny_baseline_male": inspect_glb(ANNY_GLB, "anny_baseline_male"),
    "garment_m_rev3": inspect_glb(GARMENT_GLB, "garment_m_rev3"),
}
OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
print("WROTE:", OUT_PATH)
print("ANNY skins:", out["anny_baseline_male"]["skin_count"], "nodes:", out["anny_baseline_male"]["node_count"], "verts:", out["anny_baseline_male"]["total_vertices"])
print("GARMENT skins:", out["garment_m_rev3"]["skin_count"], "nodes:", out["garment_m_rev3"]["node_count"], "verts:", out["garment_m_rev3"]["total_vertices"])
