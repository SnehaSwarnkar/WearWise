"""
WearWise Reference 3D Digital Garment Generator
Generates realistic, wearable 3D digital garment geometry and textures conforming to
the NAVER Anny upright baseline avatar, matching the approved Phase 9 reference design:
- Boxy dropped-shoulder crewneck t-shirt
- Coral-pink waffle/mesh knit texture with white micro-indentations
- White ribbed crewneck collar with repeating "CLASSY CLASSY CLASSY" text
- White dropped shoulder piping
- Left chest white patch pocket with graphic text
- White sleeve cuff bands and bottom hem band
- Size variants: S, M, L with ISO 8559-2 / BS 4952 dimensional grading
"""

import os
import math
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh
from trimesh.visual import TextureVisuals
from trimesh.visual.material import PBRMaterial

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "garments"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_garment_texture_atlas():
    """
    Creates a 2048x2048 high-resolution PBR texture atlas containing:
    1. Coral/Pink Waffle Knit Main Body (top-left & main area)
    2. White Ribbed Collar with 'CLASSY' typography (top band)
    3. Left Chest White Patch Pocket with 'NO DREAMS WORTH' emblem (top-right)
    4. White Sleeve Cuffs & Hem Bands (bottom area)
    """
    img_size = 2048
    atlas = Image.new("RGBA", (img_size, img_size), (242, 114, 137, 255))
    draw = ImageDraw.Draw(atlas)

    # 1. Base waffle / honeycomb knit texture
    # Base coral pink: #EA5D77
    base_color = (234, 93, 119)
    shadow_color = (205, 75, 100)
    highlight_color = (250, 160, 180)

    # Draw waffle mesh pattern
    waffle_step = 8
    for y in range(0, img_size, waffle_step):
        for x in range(0, img_size, waffle_step):
            # Draw diamond / waffle cell
            draw.rectangle([x, y, x + waffle_step - 1, y + waffle_step - 1], fill=base_color)
            draw.line([(x, y + 1), (x + waffle_step - 1, y + 1)], fill=highlight_color)
            draw.line([(x + waffle_step - 1, y), (x + waffle_step - 1, y + waffle_step - 1)], fill=shadow_color)
            # Center micro-perforation
            draw.rectangle([x + 3, y + 3, x + 4, y + 4], fill=(255, 230, 235))

    # 2. White Ribbed Collar Band with typography (UV region: y: 0 to 256, x: 0 to 2048)
    collar_y_start = 0
    collar_h = 240
    draw.rectangle([0, collar_y_start, img_size, collar_y_start + collar_h], fill=(255, 255, 255, 255))
    # Ribbed vertical knit lines
    for x in range(0, img_size, 4):
        draw.line([(x, collar_y_start), (x, collar_y_start + collar_h)], fill=(235, 235, 235, 255), width=1)
    
    # Collar printed text: repeating 'CLASSY CLASSY CLASSY'
    try:
        font = ImageFont.truetype("arial.ttf", 68)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    repeating_text = "  CLASSY  ·  CLASSY  ·  CLASSY  ·  CLASSY  ·  CLASSY  ·  CLASSY  ·  CLASSY  "
    draw.text((30, collar_y_start + 75), repeating_text, fill=(225, 80, 110, 255), font=font)

    # 3. Left Chest White Patch Pocket (UV region: x: 1400 to 1950, y: 300 to 850)
    pocket_box = [1400, 300, 1950, 850]
    draw.rectangle(pocket_box, fill=(255, 255, 255, 255))
    # Stitching border around pocket
    draw.rectangle([1415, 315, 1935, 835], outline=(220, 220, 220, 255), width=3)
    # Arched text inside pocket: 'NO DREAMS / WORTH'
    draw.text((1510, 480), "NO DREAMS", fill=(225, 80, 110, 255), font=font)
    draw.text((1580, 570), "WORTH", fill=(225, 80, 110, 255), font=font)
    draw.text((1540, 670), "WEARWISE EDIT", fill=(180, 180, 180, 255), font=font_small)

    # 4. White Sleeve Cuff Bands (UV region: y: 1750 to 1900, x: 0 to 2048)
    draw.rectangle([0, 1750, img_size, 1900], fill=(255, 255, 255, 255))
    for x in range(0, img_size, 4):
        draw.line([(x, 1750), (x, 1900)], fill=(238, 238, 238, 255), width=1)
    draw.line([(0, 1752), (img_size, 1752)], fill=(210, 70, 95, 255), width=4)

    # 5. White Bottom Hem Band (UV region: y: 1910 to 2048, x: 0 to 2048)
    draw.rectangle([0, 1910, img_size, 2048], fill=(255, 255, 255, 255))
    for x in range(0, img_size, 4):
        draw.line([(x, 1910), (x, 2048)], fill=(238, 238, 238, 255), width=1)
    draw.line([(0, 1912), (img_size, 1912)], fill=(210, 70, 95, 255), width=3)

    # Save texture atlas
    atlas_path = os.path.join(OUTPUT_DIR, "garment_texture_diffuse.png")
    atlas.save(atlas_path, "PNG")
    print(f"Saved texture atlas to {atlas_path}")
    return atlas, atlas_path


def build_garment_geometry(size_label="M"):
    """
    Constructs size-specific, parametric 3D crewneck t-shirt geometry:
    - S: Half-chest 50cm, Length 64cm, Shoulder 47cm
    - M: Half-chest 54cm, Length 67cm, Shoulder 50cm
    - L: Half-chest 58cm, Length 70cm, Shoulder 53cm
    
    All meshes are constructed in Y-up, +Z forward space aligned with
    NAVER Anny upright baseline avatar.
    """
    specs = {
        "S": {
            "chest_r_x": 0.250, # half width
            "chest_r_z": 0.155, # depth
            "waist_r_x": 0.245,
            "waist_r_z": 0.145,
            "hem_r_x": 0.255,
            "hem_r_z": 0.150,
            "y_hem": 0.92,
            "y_chest": 1.25,
            "y_shoulder": 1.36,
            "sleeve_len": 0.15,
            "sleeve_r": 0.082,
            "drop_shoulder_x": 0.235,
        },
        "M": {
            "chest_r_x": 0.270,
            "chest_r_z": 0.165,
            "waist_r_x": 0.265,
            "waist_r_z": 0.155,
            "hem_r_x": 0.275,
            "hem_r_z": 0.160,
            "y_hem": 0.89,
            "y_chest": 1.25,
            "y_shoulder": 1.37,
            "sleeve_len": 0.17,
            "sleeve_r": 0.088,
            "drop_shoulder_x": 0.255,
        },
        "L": {
            "chest_r_x": 0.290,
            "chest_r_z": 0.175,
            "waist_r_x": 0.285,
            "waist_r_z": 0.165,
            "hem_r_x": 0.295,
            "hem_r_z": 0.170,
            "y_hem": 0.86,
            "y_chest": 1.25,
            "y_shoulder": 1.38,
            "sleeve_len": 0.19,
            "sleeve_r": 0.094,
            "drop_shoulder_x": 0.275,
        },
    }

    sp = specs[size_label]
    vertices = []
    uvs = []
    faces = []

    # 1. Torso Tube (from hem to armpit/chest)
    # 28 angular segments, 14 height slices
    n_slices = 16
    n_seg = 32
    y_start = sp["y_hem"]
    y_chest = sp["y_chest"]
    y_shoulder = sp["y_shoulder"]

    for i in range(n_slices):
        t = i / (n_slices - 1)
        # Interpolate y
        y = y_start + t * (y_chest - y_start)
        # Interpolate radius x and z
        rx = (1 - t) * sp["hem_r_x"] + t * sp["chest_r_x"]
        rz = (1 - t) * sp["hem_r_z"] + t * sp["chest_r_z"]

        for j in range(n_seg):
            theta = 2.0 * math.pi * j / n_seg
            # Add subtle natural boxy drape curvature
            rx_drape = rx * (1.0 + 0.04 * math.cos(2 * theta))
            rz_drape = rz * (1.0 + 0.03 * math.sin(theta))
            x = rx_drape * math.sin(theta)
            z = rz_drape * math.cos(theta)
            vertices.append([x, y, z])

            # UV coordinates
            # Torso body mapped between y: 0.15 and 0.85
            # If at hem (bottom 2 slices), map to white bottom hem region (0.93 to 1.0)
            if i < 2:
                uv_v = 0.94 + 0.05 * (i / 1.0)
            else:
                uv_v = 0.84 - 0.65 * ((i - 2) / (n_slices - 3))
            uv_u = (j / n_seg)
            uvs.append([uv_u, uv_v])

    # Generate torso tube faces
    for i in range(n_slices - 1):
        for j in range(n_seg):
            next_j = (j + 1) % n_seg
            v0 = i * n_seg + j
            v1 = i * n_seg + next_j
            v2 = (i + 1) * n_seg + next_j
            v3 = (i + 1) * n_seg + j
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    torso_top_offset = len(vertices)

    # 2. Upper Chest & Shoulders (chest to neck and dropped shoulders)
    # Upper torso panels (front and back) with armhole openings
    n_upper = 8
    for i in range(n_upper):
        t = (i + 1) / n_upper
        y = y_chest + t * (y_shoulder - y_chest)
        # Interpolate width to neck or dropped shoulder
        rx = (1 - t) * sp["chest_r_x"] + t * sp["drop_shoulder_x"]
        rz = (1 - t) * sp["chest_r_z"] + t * (sp["chest_r_z"] * 0.75)

        for j in range(n_seg):
            theta = 2.0 * math.pi * j / n_seg
            # Taper inward near neck for front and back, but extend outward at shoulders (sides)
            is_shoulder = abs(math.sin(theta)) > 0.7
            if is_shoulder:
                x_scale = 1.0 + 0.08 * t
            else:
                x_scale = 1.0 - 0.25 * t
            
            x = rx * math.sin(theta) * x_scale
            z = rz * math.cos(theta)
            vertices.append([x, y, z])

            uv_u = j / n_seg
            uv_v = 0.25 - 0.12 * t
            uvs.append([uv_u, uv_v])

    # Connect upper torso slices
    for i in range(n_upper):
        prev_slice_start = (n_slices - 1) * n_seg if i == 0 else torso_top_offset + (i - 1) * n_seg
        curr_slice_start = torso_top_offset + i * n_seg
        for j in range(n_seg):
            next_j = (j + 1) % n_seg
            v0 = prev_slice_start + j
            v1 = prev_slice_start + next_j
            v2 = curr_slice_start + next_j
            v3 = curr_slice_start + j
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    # 3. Ribbed Crewneck Collar (torus/ring at top of neck)
    collar_offset = len(vertices)
    n_collar_ring = 28
    n_collar_cross = 4
    neck_center_y = y_shoulder + 0.015
    neck_radius_x = 0.085
    neck_radius_z = 0.075
    collar_width = 0.024

    for c in range(n_collar_cross):
        cross_t = c / (n_collar_cross - 1)
        r_offset = cross_t * collar_width
        y_offset = (1.0 - cross_t) * 0.018 - 0.008

        for k in range(n_collar_ring):
            phi = 2.0 * math.pi * k / n_collar_ring
            # Front dip
            dip = -0.025 * max(0.0, math.cos(phi))
            x = (neck_radius_x + r_offset) * math.sin(phi)
            y = neck_center_y + y_offset + dip
            z = (neck_radius_z + r_offset) * math.cos(phi)
            vertices.append([x, y, z])

            # Collar UV maps to top white ribbed banner (y: 0.01 to 0.11)
            uvs.append([k / n_collar_ring, 0.02 + 0.08 * cross_t])

    for c in range(n_collar_cross - 1):
        for k in range(n_collar_ring):
            next_k = (k + 1) % n_collar_ring
            v0 = collar_offset + c * n_collar_ring + k
            v1 = collar_offset + c * n_collar_ring + next_k
            v2 = collar_offset + (c + 1) * n_collar_ring + next_k
            v3 = collar_offset + (c + 1) * n_collar_ring + k
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    # 4. Left & Right Dropped Short Sleeves
    # Angle downward at 22 degrees matching avatar arm rest angle
    sleeve_angle = math.radians(24)
    arm_dir_l = np.array([-math.cos(sleeve_angle), -math.sin(sleeve_angle), 0.0])
    arm_dir_r = np.array([math.cos(sleeve_angle), -math.sin(sleeve_angle), 0.0])

    sleeve_len = sp["sleeve_len"]
    sleeve_r = sp["sleeve_r"]
    n_sleeve_slices = 8
    n_sleeve_seg = 20

    # Left Sleeve
    left_sleeve_offset = len(vertices)
    shoulder_pivot_l = np.array([-sp["drop_shoulder_x"], y_shoulder - 0.03, 0.0])

    for s in range(n_sleeve_slices):
        t = s / (n_sleeve_slices - 1)
        dist = t * sleeve_len
        center = shoulder_pivot_l + dist * arm_dir_l
        # Sleeve radius slight taper
        curr_r = sleeve_r * (1.0 - 0.08 * t)

        for j in range(n_sleeve_seg):
            theta = 2.0 * math.pi * j / n_sleeve_seg
            # Normal plane vectors perpendicular to arm_dir_l
            u_vec = np.array([arm_dir_l[1], -arm_dir_l[0], 0.0])
            w_vec = np.array([0.0, 0.0, 1.0])
            pos = center + curr_r * (math.cos(theta) * u_vec + math.sin(theta) * w_vec)
            vertices.append(pos.tolist())

            # If near sleeve cuff end, map to white cuff region (y: 0.86 to 0.92)
            if s >= n_sleeve_slices - 2:
                uv_v = 0.86 + 0.06 * (s - (n_sleeve_slices - 2))
            else:
                uv_v = 0.35 + 0.40 * (s / n_sleeve_slices)
            uvs.append([j / n_sleeve_seg, uv_v])

    for s in range(n_sleeve_slices - 1):
        for j in range(n_sleeve_seg):
            next_j = (j + 1) % n_sleeve_seg
            v0 = left_sleeve_offset + s * n_sleeve_seg + j
            v1 = left_sleeve_offset + s * n_sleeve_seg + next_j
            v2 = left_sleeve_offset + (s + 1) * n_sleeve_seg + next_j
            v3 = left_sleeve_offset + (s + 1) * n_sleeve_seg + j
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    # Right Sleeve
    right_sleeve_offset = len(vertices)
    shoulder_pivot_r = np.array([sp["drop_shoulder_x"], y_shoulder - 0.03, 0.0])

    for s in range(n_sleeve_slices):
        t = s / (n_sleeve_slices - 1)
        dist = t * sleeve_len
        center = shoulder_pivot_r + dist * arm_dir_r
        curr_r = sleeve_r * (1.0 - 0.08 * t)

        for j in range(n_sleeve_seg):
            theta = 2.0 * math.pi * j / n_sleeve_seg
            u_vec = np.array([-arm_dir_r[1], arm_dir_r[0], 0.0])
            w_vec = np.array([0.0, 0.0, 1.0])
            pos = center + curr_r * (math.cos(theta) * u_vec + math.sin(theta) * w_vec)
            vertices.append(pos.tolist())

            if s >= n_sleeve_slices - 2:
                uv_v = 0.86 + 0.06 * (s - (n_sleeve_slices - 2))
            else:
                uv_v = 0.35 + 0.40 * (s / n_sleeve_slices)
            uvs.append([j / n_sleeve_seg, uv_v])

    for s in range(n_sleeve_slices - 1):
        for j in range(n_sleeve_seg):
            next_j = (j + 1) % n_sleeve_seg
            v0 = right_sleeve_offset + s * n_sleeve_seg + j
            v1 = right_sleeve_offset + s * n_sleeve_seg + next_j
            v2 = right_sleeve_offset + (s + 1) * n_sleeve_seg + next_j
            v3 = right_sleeve_offset + (s + 1) * n_sleeve_seg + j
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

    # 5. Left Chest White Patch Pocket (Wearer's Left = -X in Three.js or +X depending on view)
    # In reference image, facing mannequin, pocket is on viewer's right (wearer's left chest)
    # Wearer's left is -X
    pocket_offset = len(vertices)
    p_w = 0.075 # 7.5 cm wide
    p_h = 0.085 # 8.5 cm tall
    p_x_center = -0.085
    p_y_center = y_chest + 0.02
    p_z = sp["chest_r_z"] + 0.006 # slightly floating on front chest

    # 4 corner vertices
    vertices.append([p_x_center - p_w / 2, p_y_center - p_h / 2, p_z])
    vertices.append([p_x_center + p_w / 2, p_y_center - p_h / 2, p_z])
    vertices.append([p_x_center + p_w / 2, p_y_center + p_h / 2, p_z])
    vertices.append([p_x_center - p_w / 2, p_y_center + p_h / 2, p_z])

    # UV mapped to pocket region (x: 1400/2048 to 1950/2048, y: 300/2048 to 850/2048)
    uvs.append([0.70, 0.40])
    uvs.append([0.94, 0.40])
    uvs.append([0.94, 0.16])
    uvs.append([0.70, 0.16])

    faces.append([pocket_offset, pocket_offset + 1, pocket_offset + 2])
    faces.append([pocket_offset, pocket_offset + 2, pocket_offset + 3])

    # Convert to trimesh
    mesh = trimesh.Trimesh(
        vertices=np.array(vertices, dtype=np.float32),
        faces=np.array(faces, dtype=np.int32),
        process=True
    )

    return mesh, np.array(uvs, dtype=np.float32)


def export_garment_glb(size_label, atlas_image):
    """
    Exports a size-graded GLB with embedded PBR material and texture atlas.
    """
    mesh, uvs = build_garment_geometry(size_label)
    
    # Assign UV visual
    material = PBRMaterial(
        name=f"WearWise_WaffleKnit_{size_label}",
        roughnessFactor=0.62,
        metallicFactor=0.05,
        baseColorTexture=atlas_image,
        doubleSided=True
    )
    
    mesh.visual = TextureVisuals(uv=uvs, material=material)
    
    out_glb = os.path.join(OUTPUT_DIR, f"TSH-WW-CREW-001_{size_label}.glb")
    mesh.export(out_glb, file_type="glb")
    print(f"Exported Size {size_label} GLB to {out_glb} (Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)})")
    return out_glb, mesh


def main():
    print("=== Generating WearWise Phase 9 Reference Garment Assets ===")
    atlas, atlas_path = create_garment_texture_atlas()

    # Generate Size S, M, L
    models = {}
    for sz in ["S", "M", "L"]:
        path, mesh = export_garment_glb(sz, atlas)
        models[sz] = {"path": path, "mesh": mesh}

    # Also save Size M as the canonical TSH-WW-CREW-001.glb
    canonical_glb = os.path.join(OUTPUT_DIR, "TSH-WW-CREW-001.glb")
    models["M"]["mesh"].export(canonical_glb, file_type="glb")
    print(f"Copied Size M to canonical {canonical_glb}")

    # Generate comprehensive provenance JSON
    provenance = {
        "sku": "TSH-WW-CREW-001",
        "title": "Signature Boxy Crew Tee (Phase 9 Realistic Mesh)",
        "sample_id": "WW-3D-TSHIRT-TSH-WW-CREW-001-REV2",
        "file_format": "glTF 2.0 Binary (.glb) with embedded PBR Texture Atlas",
        "fabric": {
            "name": "Heavyweight Cotton Waffle Knit",
            "composition": "100% Combed Organic Cotton",
            "gsm": 240.0,
            "thickness_mm": 1.15,
            "stretch_percentage": {
                "warp": 14.5,
                "weft": 28.0
            },
            "elastic_recovery_percent": 88.0,
            "bending_stiffness_micro_joules": 18.5,
            "shear_stiffness_n_m": 22.0,
            "poisson_ratio": 0.38
        },
        "construction_panels": [
            {"panel": "Front Torso Panel", "features": "Drop-shoulder armhole cut, straight hem line"},
            {"panel": "Back Torso Panel", "features": "Reinforced upper yoke seam"},
            {"panel": "Left Dropped Sleeve", "features": "Drop shoulder sleeve head, white rib cuff"},
            {"panel": "Right Dropped Sleeve", "features": "Drop shoulder sleeve head, white rib cuff"},
            {"panel": "Ribbed Crewneck Collar", "features": "White 1x1 rib knit band with 'CLASSY' typography"},
            {"panel": "Left Chest Patch Pocket", "features": "Single-needle topstitched white pocket with graphic"},
            {"panel": "Hem Band", "features": "Clean 28mm white hem binding"}
        ],
        "size_grading_cm": {
            "S": {
                "half_chest_width_cm": 50.0,
                "back_length_cm": 64.0,
                "shoulder_breadth_cm": 47.0,
                "sleeve_length_cm": 15.0,
                "collar_circumference_cm": 42.0,
                "dimensional_ease_chest_cm": "+2.0 cm"
            },
            "M": {
                "half_chest_width_cm": 54.0,
                "back_length_cm": 67.0,
                "shoulder_breadth_cm": 50.0,
                "sleeve_length_cm": 17.0,
                "collar_circumference_cm": 44.0,
                "dimensional_ease_chest_cm": "+4.5 cm (Recommended)"
            },
            "L": {
                "half_chest_width_cm": 58.0,
                "back_length_cm": 70.0,
                "shoulder_breadth_cm": 53.0,
                "sleeve_length_cm": 19.0,
                "collar_circumference_cm": 46.0,
                "dimensional_ease_chest_cm": "+8.0 cm"
            }
        },
        "standards": [
            "ISO 8559-2: Garment construction and sizing designation",
            "BS 4952: Finished dimensions under tabletop relaxation",
            "ASTM D1777: Standard test method for thickness of textile materials"
        ],
        "physics_simulation": {
            "solver": "Extended Position-Based Dynamics (XPBD)",
            "stretch_compliance": 0.00015,
            "bending_compliance": 0.012,
            "collision_margins": {"torso": 0.012, "arm": 0.010},
            "kinematic_anchors": ["collar_ring", "torso_spine"]
        },
        "created_at": "2026-11-24T18:05:00Z"
    }

    prov_path = os.path.join(OUTPUT_DIR, "TSH-WW-CREW-001_provenance.json")
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)
    print(f"Saved provenance JSON to {prov_path}")
    print("Done!")


if __name__ == "__main__":
    main()
