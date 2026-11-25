import json
import os
import struct
import sys
from pathlib import Path
import numpy as np
import pygltflib
import torch
import trimesh

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
sys.path.insert(0, str(REPO / "WEARWISE-BODY-ENGINE"))

from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.services.garment_platform.pattern_garment_builder import PatternGarmentBuilder
from app.services.garment_platform.pattern_engine import STANDARD_BOXY_CREW_MEASUREMENTS

OUT_DIR = REPO / "artifacts" / "phase10_experimental"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PUBLIC_EXP_DIR = REPO / "frontend" / "public" / "experimental_phase10"
PUBLIC_EXP_DIR.mkdir(parents=True, exist_ok=True)

# 1. Export separate experimental T-shirt (does NOT touch TSH-WW-CREW-001 Rev3)
exp_tee_path = PUBLIC_EXP_DIR / "TSH-EXP-PHASE10_M.glb"
PatternGarmentBuilder.build_garment(
    measurements=STANDARD_BOXY_CREW_MEASUREMENTS["M"],
    size_label="M",
    out_glb=str(exp_tee_path),
    sku="TSH-EXP-PHASE10",
)
print("EXPORTED_EXP_TEE:", exp_tee_path, exp_tee_path.stat().st_size)

# 2. Build rigged Anny baseline male GLB matching anny_baseline_male.glb frame
baseline_sc = trimesh.load(str(REPO / "frontend" / "public" / "avatars" / "anny_baseline_male.glb"), force="scene", process=False)
baseline_mesh = list(baseline_sc.geometry.values())[0]
baseline_bounds = baseline_mesh.bounds
baseline_h = float(baseline_bounds[1][1] - baseline_bounds[0][1])
print("BASELINE_ANNY_BOUNDS_Y_UP:", baseline_bounds[0].tolist(), baseline_bounds[1].tolist(), "H:", baseline_h)

adapter = AnnyAdapter()
adapter.initialize()
model = adapter.get_model()

with torch.no_grad():
    out = model(phenotype_kwargs={"gender": torch.tensor([0.0]), "age": torch.tensor([0.5]), "muscle": torch.tensor([0.5]), "weight": torch.tensor([0.5]), "height": torch.tensor([0.5]), "proportions": torch.tensor([0.5])})

verts_zup = out["rest_vertices"][0].detach().cpu().numpy().astype(np.float64)
bone_poses_zup = out["rest_bone_poses"][0].detach().cpu().numpy().astype(np.float64)  # (104, 4, 4)
faces = model.faces.detach().cpu().numpy().astype(np.uint32)
weights_full = model.dense_vertex_bone_weights.detach().cpu().numpy().astype(np.float64)
bones = list(model.bone_labels)
parents = [int(x) for x in model.bone_parents]

# Compute exact scale + Y-shift to match anny_baseline_male.glb in Y-up frame (R_x(-90°))
t_rot = np.array([
    [1.0,  0.0,  0.0, 0.0],
    [0.0,  0.0,  1.0, 0.0],
    [0.0, -1.0,  0.0, 0.0],
    [0.0,  0.0,  0.0, 1.0],
], dtype=np.float64)

# Rotate vertices to Y-up
verts_yup = (t_rot[:3, :3] @ verts_zup.T).T
raw_h = float(verts_yup[:, 1].max() - verts_yup[:, 1].min())
scale_f = baseline_h / raw_h
verts_yup *= scale_f
y_shift = float(baseline_bounds[0][1] - verts_yup[:, 1].min())
z_shift = float(0.5 * (baseline_bounds[0][2] + baseline_bounds[1][2]) - 0.5 * (verts_yup[:, 2].min() + verts_yup[:, 2].max()))
verts_yup[:, 1] += y_shift
verts_yup[:, 2] += z_shift
max_diff = float(np.abs(verts_yup - baseline_mesh.vertices).max())
print("RIGGED_VS_BASELINE_MAX_VERT_DIFF_M:", max_diff)

# Transform bone world matrices into the exact same Y-up scaled + shifted frame
t_world_fix = np.eye(4, dtype=np.float64)
t_world_fix[:3, :3] = t_rot[:3, :3] * scale_f
t_world_fix[1, 3] = y_shift
t_world_fix[2, 3] = z_shift

# Wait: pure rotation R_x(-90) * bone_pose gives scaled position + orthonormal rotation!
# Keep bone local rotation orthonormal (no scale inside rotation columns) so Three.js Skeleton behaves cleanly!
bone_world_mats = np.zeros((len(bones), 4, 4), dtype=np.float64)
for i in range(len(bones)):
    m = t_rot @ bone_poses_zup[i]
    m[:3, 3] = m[:3, 3] * scale_f + np.array([0.0, y_shift, z_shift])
    bone_world_mats[i] = m

# Compute local bone transforms relative to parent
bone_local_mats = np.zeros_like(bone_world_mats)
for i in range(len(bones)):
    p = parents[i]
    if p < 0:
        bone_local_mats[i] = bone_world_mats[i]
    else:
        bone_local_mats[i] = np.linalg.inv(bone_world_mats[p]) @ bone_world_mats[i]

# Inverse bind matrices = inv(bone_world_mats)
inv_bind_mats = np.array([np.linalg.inv(m) for m in bone_world_mats], dtype=np.float32)

# Top-4 joints & normalized weights per vertex
n_verts = len(verts_yup)
top4_idx = np.argsort(-weights_full, axis=1)[:, :4].astype(np.uint16)
top4_w = np.take_along_axis(weights_full, top4_idx, axis=1).astype(np.float32)
w_sum = top4_w.sum(axis=1, keepdims=True)
w_sum[w_sum == 0] = 1.0
top4_w /= w_sum

# Compute smooth vertex normals
tm_tmp = trimesh.Trimesh(vertices=verts_yup, faces=faces, process=False)
normals = np.asarray(tm_tmp.vertex_normals, dtype=np.float32)

# Build glTF 2.0 binary buffer
pos_bytes = verts_yup.astype(np.float32).tobytes()
norm_bytes = normals.astype(np.float32).tobytes()
jnt_bytes = top4_idx.tobytes()
wgt_bytes = top4_w.tobytes()
idx_bytes = faces.astype(np.uint32).tobytes()
# glTF matrices are column-major!
ibm_col_major = np.transpose(inv_bind_mats, (0, 2, 1)).astype(np.float32).tobytes()

def pad4(b: bytes) -> bytes:
    rem = len(b) % 4
    return b + (b"\x00" * (4 - rem) if rem else b"")

chunks = [pos_bytes, norm_bytes, jnt_bytes, wgt_bytes, idx_bytes, ibm_col_major]
offsets = []
cur = 0
blob_parts = []
for ch in chunks:
    p_ch = pad4(ch)
    offsets.append((cur, len(ch)))
    blob_parts.append(p_ch)
    cur += len(p_ch)
blob = b"".join(blob_parts)

# Build nodes: node 0..103 = bones, node 104 = SkinnedMesh, node 105 = ArmatureRoot
nodes = []
children_map = {i: [] for i in range(len(bones))}
root_bones = []
for i, p in enumerate(parents):
    if p < 0:
        root_bones.append(i)
    else:
        children_map[p].append(i)

for i, bname in enumerate(bones):
    lm = bone_local_mats[i]
    # glTF matrix is column-major
    mat_col = [float(x) for x in lm.T.reshape(-1)]
    nodes.append(pygltflib.Node(
        name=bname,
        children=children_map[i],
        matrix=mat_col,
    ))

mesh_node_idx = len(bones)
nodes.append(pygltflib.Node(name="Anny_Skinned_Body", mesh=0, skin=0))
root_node_idx = len(bones) + 1
nodes.append(pygltflib.Node(name="Anny_Rig_Root", children=root_bones + [mesh_node_idx]))

gltf = pygltflib.GLTF2(
    scene=0,
    scenes=[pygltflib.Scene(nodes=[root_node_idx])],
    nodes=nodes,
    skins=[pygltflib.Skin(name="Anny_104_Skeleton", joints=list(range(len(bones))), inverseBindMatrices=5, skeleton=root_bones[0])],
    meshes=[
        pygltflib.Mesh(
            name="Anny_Baseline_Male_Rigged",
            primitives=[
                pygltflib.Primitive(
                    attributes=pygltflib.Attributes(POSITION=0, NORMAL=1, JOINTS_0=2, WEIGHTS_0=3),
                    indices=4,
                    material=0,
                )
            ],
        )
    ],
    materials=[
        pygltflib.Material(
            name="Anny_Matte_Mannequin",
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorFactor=[0.92, 0.92, 0.94, 1.0],
                metallicFactor=0.0,
                roughnessFactor=0.75,
            ),
        )
    ],
    buffers=[pygltflib.Buffer(byteLength=len(blob))],
    bufferViews=[
        pygltflib.BufferView(buffer=0, byteOffset=offsets[0][0], byteLength=offsets[0][1], target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[1][0], byteLength=offsets[1][1], target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[2][0], byteLength=offsets[2][1], target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[3][0], byteLength=offsets[3][1], target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[4][0], byteLength=offsets[4][1], target=pygltflib.ELEMENT_ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[5][0], byteLength=offsets[5][1]),
    ],
    accessors=[
        pygltflib.Accessor(bufferView=0, componentType=pygltflib.FLOAT, count=n_verts, type="VEC3", min=verts_yup.min(axis=0).astype(float).tolist(), max=verts_yup.max(axis=0).astype(float).tolist()),
        pygltflib.Accessor(bufferView=1, componentType=pygltflib.FLOAT, count=n_verts, type="VEC3"),
        pygltflib.Accessor(bufferView=2, componentType=pygltflib.UNSIGNED_SHORT, count=n_verts, type="VEC4"),
        pygltflib.Accessor(bufferView=3, componentType=pygltflib.FLOAT, count=n_verts, type="VEC4"),
        pygltflib.Accessor(bufferView=4, componentType=pygltflib.UNSIGNED_INT, count=int(faces.size), type="SCALAR"),
        pygltflib.Accessor(bufferView=5, componentType=pygltflib.FLOAT, count=len(bones), type="MAT4"),
    ],
)
gltf.set_binary_blob(blob)
out_rigged = PUBLIC_EXP_DIR / "anny_rigged_male_exp.glb"
gltf.save(str(out_rigged))
print("EXPORTED_RIGGED_ANNY:", out_rigged, out_rigged.stat().st_size)
