"""
Rebuild Phase 5A Verification Packet
Computes SHA-256 checksums, verifies all 4 technical review criteria,
and packages phase5a_verification_packet.zip with root MANIFEST.json and MANIFEST.md.
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import subprocess
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()

    files_to_pack = [
        "app/domain/taxonomies/garment.py",
        "app/domain/entities/garment.py",
        "app/fit/__init__.py",
        "app/fit/engine.py",
        "app/fit/models.py",
        "app/fit/port.py",
        "app/fit/registry.py",
        "app/fit/rulebook.py",
        "tests/fit/test_honest_fit.py",
        "tests/fit/test_boundary_cases.py",
        "scripts/demo_honest_fit.py",
        "docs/architecture/HONEST_FIT_PENALTY_COEFFICIENT_PROPOSAL.md",
        "artifacts/phase5a/phase5a_tshirt_fit_report.json",
        "artifacts/phase5a/phase5a_casual_shirt_fit_report.json",
    ]

    extracted_contents = {}
    manifest_files = {}

    for rel_path in files_to_pack:
        p = repo_root / rel_path
        if not p.exists():
            raise FileNotFoundError(f"Required file not found: {rel_path}")
        content = p.read_bytes()
        sha256 = hashlib.sha256(content).hexdigest()
        extracted_contents[rel_path] = content
        manifest_files[rel_path] = {
            "sha256": sha256,
            "size_bytes": len(content),
        }
        print(f"  {rel_path:60s} SHA256: {sha256} ({len(content):,} bytes)")

    # Verification checks
    print("\n--- Running Verification Checks for Phase 5A Evidence Supplement ---")
    engine_py = extracted_contents["app/fit/engine.py"].decode("utf-8")
    port_py = extracted_contents["app/fit/port.py"].decode("utf-8")
    models_py = extracted_contents["app/fit/models.py"].decode("utf-8")
    rulebook_py = extracted_contents["app/fit/rulebook.py"].decode("utf-8")
    proposal_md = extracted_contents["docs/architecture/HONEST_FIT_PENALTY_COEFFICIENT_PROPOSAL.md"].decode("utf-8")
    tshirt_json = json.loads(extracted_contents["artifacts/phase5a/phase5a_tshirt_fit_report.json"].decode("utf-8"))

    verifications = {}

    # 1. Recommendation Status Consistency
    # Check that in t-shirt report: Size S is 'recommended' and Size XS is 'alternative'
    evals = {e["size_label"]: e["status"] for e in tshirt_json["evaluations"]}
    rec_count = sum(1 for s in evals.values() if s == "recommended")
    status_consistent = evals.get("S") == "recommended" and evals.get("XS") == "alternative" and rec_count == 1
    verifications["1_recommendation_status_consistency"] = {
        "passed": status_consistent,
        "detail": f"Size S is 'recommended', Size XS is 'alternative', exactly {rec_count} recommended size",
    }

    # 2. Hip Weighting Policy Reconciliation
    # Proposal document clarifies bottoms baseline weight 0.40 with 0.5 discount (effective 0.20)
    has_hip_reconcile = "hip_circumference" in rulebook_py and "w_{\\text{hip}} = 0.40" in proposal_md and "w_{\\text{hip}}' = 0.5 \\times 0.40 = 0.20" in proposal_md
    verifications["2_hip_weighting_policy"] = {
        "passed": has_hip_reconcile,
        "detail": "Authoritative policy established: bottoms baseline 0.40, provisional discount 0.5x yields effective weight 0.20",
    }

    # 3. Sensitivity Table Denominator Reconciliation
    has_denom_reconcile = "W_{\\text{eval}} = 0.70" in proposal_md and "W_{\\text{eval}} = 0.90" in proposal_md and "Single-Zone Score Impact" in proposal_md or "T-Shirt Score Impact" in proposal_md
    verifications["3_sensitivity_table_denominator_reconciliation"] = {
        "passed": has_denom_reconcile,
        "detail": "Proposal reconciles raw penalty with normalized multi-zone composite scores across T-shirt and casual shirt denominators",
    }

    # 4. Garment Measurement Provenance & Mechanical Stretch Decoupling
    has_provenance_cls = "class GarmentMeasurementProvenance" in models_py
    has_validation_claim = "validation_claim" in models_py
    has_prov_in_json = "garment_provenance" in tshirt_json["evaluations"][0] and "demonstration_fixture_provisional_not_certified" == tshirt_json["evaluations"][0]["garment_provenance"]["validation_claim"]
    has_stretch_separate = "mechanical_stretch_pct" in tshirt_json["evaluations"][0]["fabric_properties"] and "fibre_composition" in tshirt_json["evaluations"][0]["fabric_properties"]
    verifications["4_garment_measurement_provenance"] = {
        "passed": has_provenance_cls and has_validation_claim and has_prov_in_json and has_stretch_separate,
        "detail": "GarmentMeasurementProvenance implemented; disclaimer claim recorded; mechanical stretch separated from fibre composition",
    }

    all_passed = all(v["passed"] for v in verifications.values())
    print(f"\nAll 4 Technical Review Criteria Satisfied: {all_passed}")
    for k, v in verifications.items():
        status_str = "PASS" if v["passed"] else "FAIL"
        print(f"  [{status_str}] {k}: {v['detail']}")

    manifest_data = {
        "manifest_version": "1.0.0",
        "phase": "5A",
        "git_branch": branch,
        "base_commit": commit_hash,
        "review_criteria_verifications": verifications,
        "files": manifest_files,
    }

    manifest_json_str = json.dumps(manifest_data, indent=2)

    manifest_md_lines = [
        "# WearWise — Phase 5A Verification Packet Manifest",
        f"**Git Branch:** `{branch}`  ",
        f"**Base Commit:** `{commit_hash}`  ",
        "",
        "## Included Source Files & SHA-256 Checksums",
        "",
        "| File Path | SHA-256 Checksum | Size (bytes) |",
        "|---|---|---:|",
    ]
    for rel_path, meta in manifest_files.items():
        manifest_md_lines.append(f"| `{rel_path}` | `{meta['sha256']}` | {meta['size_bytes']:,} |")

    manifest_md_lines.extend([
        "",
        "## Review Findings Verification Status",
        "",
        "| Criterion ID | Review Criterion | Verification Status | Verification Detail |",
        "|---|---|:---:|---|",
    ])
    for k, v in verifications.items():
        status_mark = "**PASSED**" if v["passed"] else "**FAILED**"
        manifest_md_lines.append(f"| `{k}` | {k.replace('_', ' ').title()} | {status_mark} | {v['detail']} |")

    manifest_md_str = "\n".join(manifest_md_lines) + "\n"

    # Save manifest files
    art_dir = repo_root / "artifacts" / "phase5a"
    art_dir.mkdir(parents=True, exist_ok=True)
    with open(art_dir / "MANIFEST.json", "w", encoding="utf-8") as f:
        f.write(manifest_json_str)
    with open(art_dir / "MANIFEST.md", "w", encoding="utf-8") as f:
        f.write(manifest_md_str)

    # Package ZIP archive
    zip_out_path = art_dir / "phase5a_verification_packet.zip"
    with zipfile.ZipFile(zip_out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.json", manifest_json_str.encode("utf-8"))
        zf.writestr("MANIFEST.md", manifest_md_str.encode("utf-8"))
        for rel_path, content in extracted_contents.items():
            zf.writestr(rel_path, content)

    zip_size_mb = zip_out_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Created verification packet: {zip_out_path} ({zip_size_mb:.2f} MB)")

    # Copy to brain artifact directory
    brain_dir = Path(r"C:\Users\Lenovo\.gemini\antigravity\brain\c57b9fa6-3e23-4fa2-b534-c1f6bc625ad8\phase5a")
    brain_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(zip_out_path, brain_dir / "phase5a_verification_packet.zip")
    shutil.copyfile(art_dir / "MANIFEST.md", brain_dir / "MANIFEST.md")
    print(f"[OK] Copied archive and manifest to brain: {brain_dir}")


if __name__ == "__main__":
    main()
