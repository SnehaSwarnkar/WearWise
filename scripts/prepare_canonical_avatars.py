"""
WearWise Canonical Upright Avatar Converter
===========================================
Converts raw Anny baseline meshes to canonical glTF 2.0 Y-up, +Z-forward orientation
with exact standing posture (feet at Y=0, head at +Y, front facing camera).
"""

import os
from pathlib import Path
import numpy as np
import trimesh

REPO_ROOT = Path(__file__).resolve().parent.parent
MALE_IN = REPO_ROOT / "WEARWISE-BODY-ENGINE" / "artifacts" / "glb" / "anny_baseline_male.glb"
FEMALE_IN = REPO_ROOT / "WEARWISE-BODY-ENGINE" / "artifacts" / "glb" / "anny_baseline_female.glb"

PUBLIC_AVATARS = REPO_ROOT / "frontend" / "public" / "avatars"
PUBLIC_AVATARS.mkdir(parents=True, exist_ok=True)

# Canonical R_x(-90°) rotation matrix
# x_gltf = x_anny
# y_gltf = z_anny (Head is +Y)
# z_gltf = -y_anny (Front is +Z, facing viewer)
T_ROT_X_NEG90 = np.array([
    [1.0,  0.0,  0.0, 0.0],
    [0.0,  0.0,  1.0, 0.0],
    [0.0, -1.0,  0.0, 0.0],
    [0.0,  0.0,  0.0, 1.0]
], dtype=np.float64)


def convert_mesh(input_path: Path, output_path: Path, name: str):
    print(f"Loading {name} from {input_path}...")
    mesh = trimesh.load(str(input_path), force="mesh")

    # Apply pure R_x(-90°) rotation
    mesh.apply_transform(T_ROT_X_NEG90)

    # Center horizontally on X, and shift Y so lowest vertex rests at Y = 0.0
    min_b = mesh.bounds[0]
    max_b = mesh.bounds[1]
    center_x = (min_b[0] + max_b[0]) / 2.0
    center_z = (min_b[2] + max_b[2]) / 2.0
    min_y = min_b[1]

    t_shift = np.eye(4)
    t_shift[0, 3] = -center_x
    t_shift[1, 3] = -min_y
    t_shift[2, 3] = -center_z
    mesh.apply_transform(t_shift)

    # Recompute vertex normals for smooth shading
    mesh.fix_normals()

    # Apply pearl-white mannequin PBR material
    mesh.visual.material = trimesh.visual.material.PBRMaterial(
        name="PearlWhiteMannequin",
        baseColorFactor=[0.96, 0.96, 0.97, 1.0],
        metallicFactor=0.04,
        roughnessFactor=0.28,
    )

    glb_data = trimesh.exchange.gltf.export_glb(mesh)
    with open(output_path, "wb") as f:
        f.write(glb_data)

    print(f"Exported canonical upright {name} to {output_path} ({len(glb_data)} bytes)")
    print(f"  Bounds: X=[{mesh.bounds[0][0]:.3f}, {mesh.bounds[1][0]:.3f}] "
          f"Y=[{mesh.bounds[0][1]:.3f}, {mesh.bounds[1][1]:.3f}] "
          f"Z=[{mesh.bounds[0][2]:.3f}, {mesh.bounds[1][2]:.3f}]")


def main():
    convert_mesh(MALE_IN, PUBLIC_AVATARS / "anny_baseline_male.glb", "Masculine Mannequin")
    convert_mesh(FEMALE_IN, PUBLIC_AVATARS / "anny_baseline_female.glb", "Feminine Mannequin")
    print("All baseline mannequins successfully aligned to canonical upright stature.")


if __name__ == "__main__":
    main()
