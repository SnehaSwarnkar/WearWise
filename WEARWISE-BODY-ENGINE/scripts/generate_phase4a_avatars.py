"""
WearWise Phase 4A: Avatar Generation & Export Script
Generates real 3D avatars using AvatarShapeSpec and AnnyAdapter,
exports production GLBs, performs independent re-validation,
and renders multi-angle visual comparison figures.
"""

import json
import os
import sys
import shutil
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from app.avatar_engine.adapters.anny_adapter import AnnyAdapter
from app.domain.entities.avatar import AvatarShapeSpec, RegionalShapeScale
from app.domain.taxonomies.garment import PresentationGender


def main():
    print("=" * 70)
    print("WEARWISE PHASE 4A: FIRST VISIBLE AVATAR GENERATION PIPELINE")
    print("=" * 70)

    # Output paths
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "artifacts" / "phase4a"
    glb_dir = output_dir / "glb"
    img_dir = output_dir / "images"
    glb_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    # Artifact directory for UI presentation
    artifact_brain_dir = Path(r"C:\Users\Lenovo\.gemini\antigravity\brain\c57b9fa6-3e23-4fa2-b534-c1f6bc625ad8\phase4a")
    artifact_brain_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize AnnyAdapter
    t0 = time.perf_counter()
    adapter = AnnyAdapter(device="cpu")
    adapter.initialize()
    init_time_s = time.perf_counter() - t0
    print(f"[1/5] AnnyAdapter initialized in {init_time_s:.4f} s.")

    # 2. Define Avatar Configurations
    avatar_configs = [
        {
            "id": "neutral_masculine",
            "title": "Neutral Masculine Avatar (Baseline)",
            "presentation": PresentationGender.MASCULINE,
            "stature_cm": 178.0,
            "scales": {},
            "description": "Baseline unedited masculine avatar, stature 178.0 cm",
        },
        {
            "id": "neutral_feminine",
            "title": "Neutral Feminine Avatar (Baseline)",
            "presentation": PresentationGender.FEMININE,
            "stature_cm": 165.0,
            "scales": {},
            "description": "Baseline unedited feminine avatar, stature 165.0 cm",
        },
        {
            "id": "control_shoulder_width",
            "title": "Individual Control: Shoulder Width (+0.75)",
            "presentation": PresentationGender.MASCULINE,
            "stature_cm": 178.0,
            "scales": {
                "shoulders": RegionalShapeScale(scale_x=0.75, scale_y=0.0, scale_z=0.0)
            },
            "description": "Single-parameter variation: shoulder breadth scale_x = +0.75",
        },
        {
            "id": "control_belly_fullness",
            "title": "Individual Control: Belly Fullness (+0.70)",
            "presentation": PresentationGender.MASCULINE,
            "stature_cm": 178.0,
            "scales": {
                "waist_abdomen": RegionalShapeScale(scale_x=0.0, scale_y=0.70, scale_z=0.0)
            },
            "description": "Single-parameter variation: belly sagittal protrusion scale_y = +0.70",
        },
        {
            "id": "control_thigh_fullness",
            "title": "Individual Control: Thigh Fullness (+0.50)",
            "presentation": PresentationGender.MASCULINE,
            "stature_cm": 178.0,
            "scales": {
                "thighs": RegionalShapeScale(scale_x=0.50, scale_y=0.0, scale_z=0.0)
            },
            "description": "Single-parameter variation: upper leg girth scale_x = +0.50",
        },
        {
            "id": "combined_athletic_modified",
            "title": "Combined Modified Avatar (Shopper Profile)",
            "presentation": PresentationGender.MASCULINE,
            "stature_cm": 180.0,
            "scales": {
                "shoulders": RegionalShapeScale(scale_x=0.60, scale_y=0.30, scale_z=0.0),
                "torso_chest": RegionalShapeScale(scale_x=0.0, scale_y=0.50, scale_z=0.0),
                "waist_abdomen": RegionalShapeScale(scale_x=-0.40, scale_y=0.15, scale_z=0.0),
                "arms": RegionalShapeScale(scale_x=0.45, scale_y=0.0, scale_z=0.0),
                "hips": RegionalShapeScale(scale_x=0.20, scale_y=0.0, scale_z=0.0),
                "thighs": RegionalShapeScale(scale_x=0.40, scale_y=0.0, scale_z=0.0),
                "calves": RegionalShapeScale(scale_x=0.25, scale_y=0.0, scale_z=0.0),
            },
            "description": "Multi-region customization: broad shoulders, athletic chest, tapered waist, muscular legs",
        },
    ]

    generated_data = {}

    # 3. Generate and Export GLBs
    print("\n[2/5] Generating Avatars and Exporting GLBs...")
    for cfg in avatar_configs:
        cid = cfg["id"]
        t_gen_0 = time.perf_counter()
        spec = AvatarShapeSpec(
            spec_version="1.2.1",
            presentation=cfg["presentation"],
            target_stature_cm=cfg["stature_cm"],
            target_measurements={"stature": cfg["stature_cm"]},
            regional_scales=cfg["scales"],
            semantic_controls={},
        )
        mesh_data = adapter.generate_avatar(spec)
        gen_time_ms = (time.perf_counter() - t_gen_0) * 1000.0

        # Validate mesh
        val_report = adapter.validate_mesh(mesh_data)
        assert val_report.is_valid, f"Validation failed for {cid}: {val_report.error_message}"

        # Export GLB bytes
        t_export_0 = time.perf_counter()
        glb_bytes = adapter.export_glb(mesh_data)
        export_time_ms = (time.perf_counter() - t_export_0) * 1000.0

        # Save to artifacts
        glb_file = glb_dir / f"{cid}.glb"
        with open(glb_file, "wb") as f:
            f.write(glb_bytes)

        # Copy to brain artifact directory for user access
        brain_glb = artifact_brain_dir / f"{cid}.glb"
        shutil.copyfile(glb_file, brain_glb)

        # Independent Reload & Verification
        t_reload_0 = time.perf_counter()
        reloaded = trimesh.load(str(glb_file), file_type="glb")
        reload_time_ms = (time.perf_counter() - t_reload_0) * 1000.0
        loaded_mesh = list(reloaded.geometry.values())[0] if isinstance(reloaded, trimesh.Scene) else reloaded

        assert loaded_mesh.vertices.shape[0] == 13718
        assert loaded_mesh.faces.shape[0] == 27420

        verts = mesh_data.vertices
        achieved_h = float((verts[:, 2].max() - verts[:, 2].min()) * 100.0)

        meta = {
            "id": cid,
            "title": cfg["title"],
            "description": cfg["description"],
            "target_stature_cm": cfg["stature_cm"],
            "achieved_stature_cm": achieved_h,
            "stature_error_mm": abs(achieved_h - cfg["stature_cm"]) * 10.0,
            "vertex_count": int(verts.shape[0]),
            "face_count": int(mesh_data.faces.shape[0]),
            "is_watertight": val_report.is_watertight,
            "glb_size_bytes": len(glb_bytes),
            "glb_path": str(glb_file),
            "brain_glb_path": str(brain_glb),
            "generation_time_ms": gen_time_ms,
            "export_time_ms": export_time_ms,
            "reload_time_ms": reload_time_ms,
            "bbox_min_m": [float(c) for c in verts.min(axis=0)],
            "bbox_max_m": [float(c) for c in verts.max(axis=0)],
        }
        generated_data[cid] = {
            "meta": meta,
            "vertices": verts,
            "faces": mesh_data.faces,
        }
        print(f"  + {cfg['title']:<48} -> {len(glb_bytes)/1024:.1f} KB GLB | Gen: {gen_time_ms:.1f}ms | H: {achieved_h:.2f}cm")

    # 4. Compute Measurable Displacements for Individual Controls
    print("\n[3/5] Quantitative Displacement Analysis...")
    v_neutral = generated_data["neutral_masculine"]["vertices"]

    control_displacements = {}
    for cid in ["control_shoulder_width", "control_belly_fullness", "control_thigh_fullness", "combined_athletic_modified"]:
        v_mod = generated_data[cid]["vertices"]
        diff = np.linalg.norm(v_mod - v_neutral, axis=-1)
        max_d_cm = float(diff.max() * 100.0)
        mean_d_cm = float(diff.mean() * 100.0)
        p95_d_cm = float(np.percentile(diff, 95) * 100.0)
        affected_count = int((diff > 0.001).sum())  # > 1 mm displacement

        peak_idx = int(np.argmax(diff))
        peak_loc = [float(c) for c in v_mod[peak_idx]]

        control_displacements[cid] = {
            "max_displacement_cm": max_d_cm,
            "mean_displacement_cm": mean_d_cm,
            "p95_displacement_cm": p95_d_cm,
            "affected_vertices_count": affected_count,
            "peak_vertex_index": peak_idx,
            "peak_vertex_location_m": peak_loc,
        }
        print(f"  * {cid:<30}: Max Disp = {max_d_cm:.2f} cm | Mean Disp = {mean_d_cm:.3f} cm | Affected Vertices = {affected_count}")

    # 5. Render High-Resolution Visual Comparisons
    print("\n[4/5] Rendering High-Resolution Visual Comparison Figures...")

    def render_comparison_figure(id_ref, id_mod, fig_title, output_filename):
        v1 = generated_data[id_ref]["vertices"]
        v2 = generated_data[id_mod]["vertices"]
        faces = generated_data[id_ref]["faces"]
        diff = np.linalg.norm(v2 - v1, axis=-1) * 100.0  # cm

        fig = plt.figure(figsize=(18, 10), dpi=150)
        fig.suptitle(fig_title, fontsize=16, fontweight="bold", y=0.98)

        # 1. Front view (Coronal X-Z)
        ax1 = fig.add_subplot(1, 3, 1)
        # Subsample points for crisp scatter visualization
        sub_idx = np.arange(0, len(v1), 2)
        ax1.scatter(v1[sub_idx, 0], v1[sub_idx, 2], s=1.0, c="#718096", alpha=0.4, label=f"Baseline ({id_ref})")
        sc1 = ax1.scatter(v2[sub_idx, 0], v2[sub_idx, 2], s=2.0, c=diff[sub_idx], cmap="plasma", alpha=0.85, label=f"Modified ({id_mod})")
        cbar1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
        cbar1.set_label("Displacement Magnitude (cm)", fontsize=10)
        ax1.set_title("Front View (Coronal Projection)", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Lateral Breadth (X) [m]")
        ax1.set_ylabel("Vertical Stature (Z) [m]")
        ax1.set_aspect("equal")
        ax1.grid(True, linestyle="--", alpha=0.3)
        ax1.legend(loc="upper left", markerscale=4)

        # 2. Side view (Sagittal Y-Z)
        ax2 = fig.add_subplot(1, 3, 2)
        ax2.scatter(v1[sub_idx, 1], v1[sub_idx, 2], s=1.0, c="#718096", alpha=0.4, label=f"Baseline ({id_ref})")
        sc2 = ax2.scatter(v2[sub_idx, 1], v2[sub_idx, 2], s=2.0, c=diff[sub_idx], cmap="plasma", alpha=0.85, label=f"Modified ({id_mod})")
        cbar2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
        cbar2.set_label("Displacement Magnitude (cm)", fontsize=10)
        ax2.set_title("Side View (Sagittal Projection)", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Sagittal Depth (Y) [m]")
        ax2.set_ylabel("Vertical Stature (Z) [m]")
        ax2.set_aspect("equal")
        ax2.grid(True, linestyle="--", alpha=0.3)
        ax2.legend(loc="upper left", markerscale=4)

        # 3. 3D Perspective View
        ax3 = fig.add_subplot(1, 3, 3, projection="3d")
        sub_3d = np.arange(0, len(v1), 4)
        sc3 = ax3.scatter(
            v2[sub_3d, 0], v2[sub_3d, 1], v2[sub_3d, 2],
            c=diff[sub_3d], cmap="plasma", s=2.5, alpha=0.9
        )
        cbar3 = plt.colorbar(sc3, ax=ax3, fraction=0.046, pad=0.08)
        cbar3.set_label("Displacement (cm)", fontsize=10)
        ax3.set_title("3D Isometric Perspective", fontsize=12, fontweight="bold")
        ax3.set_xlabel("X (m)")
        ax3.set_ylabel("Y (m)")
        ax3.set_zlabel("Z (m)")
        ax3.view_init(elev=15, azim=-60)

        plt.tight_layout()
        out_path = img_dir / output_filename
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        brain_img = artifact_brain_dir / output_filename
        shutil.copyfile(out_path, brain_img)
        plt.close(fig)
        print(f"  Rendered: {output_filename}")
        return str(out_path)

    # Render comparisons
    img_neutral_vs_combined = render_comparison_figure(
        "neutral_masculine", "combined_athletic_modified",
        "WearWise 3D Avatar: Neutral Baseline vs Combined Customized Shopper Profile",
        "comparison_neutral_vs_combined.png",
    )
    img_shoulder = render_comparison_figure(
        "neutral_masculine", "control_shoulder_width",
        "WearWise 3D Avatar: Shoulder Width Modulation (scale_x = +0.75)",
        "comparison_shoulder_width.png",
    )
    img_belly = render_comparison_figure(
        "neutral_masculine", "control_belly_fullness",
        "WearWise 3D Avatar: Belly Fullness Modulation (scale_y = +0.70)",
        "comparison_belly_fullness.png",
    )
    img_thigh = render_comparison_figure(
        "neutral_masculine", "control_thigh_fullness",
        "WearWise 3D Avatar: Thigh Fullness Modulation (scale_x = +0.50)",
        "comparison_thigh_fullness.png",
    )

    # Comprehensive 4-avatar gallery
    fig_gal = plt.figure(figsize=(20, 10), dpi=150)
    fig_gal.suptitle("WearWise Phase 4A Avatar Gallery: Baseline & Controlled Variations", fontsize=18, fontweight="bold", y=0.98)

    gallery_items = [
        ("neutral_masculine", "1. Neutral Baseline\n(Stature 178 cm)"),
        ("control_shoulder_width", "2. Broad Shoulders\n(scale_x = +0.75)"),
        ("control_belly_fullness", "3. Fuller Abdomen\n(scale_y = +0.70)"),
        ("combined_athletic_modified", "4. Custom Shopper Avatar\n(Multi-Region Mapped)"),
    ]

    for idx, (cid, label) in enumerate(gallery_items, 1):
        ax = fig_gal.add_subplot(1, 4, idx)
        v = generated_data[cid]["vertices"]
        sub = np.arange(0, len(v), 2)
        ax.scatter(v[sub, 0], v[sub, 2], s=1.5, c="#2B6CB0", alpha=0.7)
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_xlabel("X (Lateral) [m]")
        if idx == 1:
            ax.set_ylabel("Z (Vertical Stature) [m]")
        ax.set_aspect("equal")
        ax.set_xlim(-0.6, 0.6)
        ax.set_ylim(-1.0, 1.0)
        ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    gal_path = img_dir / "wearwise_avatar_gallery_4panel.png"
    fig_gal.savefig(gal_path, dpi=150, bbox_inches="tight")
    shutil.copyfile(gal_path, artifact_brain_dir / "wearwise_avatar_gallery_4panel.png")
    plt.close(fig_gal)
    print("  Rendered: wearwise_avatar_gallery_4panel.png")

    # 6. Save Comprehensive Metrics JSON
    results_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": "WearWise Body Intelligence Engine (Phase 4A)",
        "adapter": "AnnyAdapter (NAVER Anny v0.6.2, CPU LBS Skinning)",
        "initialization_time_seconds": init_time_s,
        "avatars_generated": {cid: d["meta"] for cid, d in generated_data.items()},
        "quantitative_displacements": control_displacements,
    }

    json_path = output_dir / "phase4a_metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    shutil.copyfile(json_path, artifact_brain_dir / "phase4a_metrics.json")
    print(f"\n[5/5] Metrics summary saved to {json_path}")
    print("=" * 70)
    print("ALL PHASE 4A AVATARS AND ARTIFACTS GENERATED SUCCESSFULLY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
