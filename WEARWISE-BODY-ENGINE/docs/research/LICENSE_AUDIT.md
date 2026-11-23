# Comprehensive Licensing & Asset Provenance Audit (Reconciled)

**Audit Date:** 2026-11-23  
**Auditor:** Antigravity (Implementation Executor)  
**Standard:** WearWise Technical Decision Owner Mandatory Commercial Gate  
**Status:** ✅ Verified Source Fact / 🧪 Actual Experiment Result  

---

## 1. Executive Summary

Commercial licensing eligibility is a **mandatory production-selection gate**, not merely a weighted score. A candidate failing this gate cannot be adopted for WearWise production regardless of technical capabilities.

### Gate Verdict:
- **NAVER Anny (v0.6.2):** **PASS — CLEARED FOR WEARWISE PRODUCTION**  
  Source code is licensed under Apache-2.0; underlying mesh and morphological blendshapes are CC0-1.0 (MakeHuman); all 34 transitive dependencies carry permissive open-source licenses (Apache, MIT, BSD); restricted SMPL/SMPL-X assets are verified absent.
- **OxiHuman:** **REJECTED / UNRESOLVED LICENSING STATUS**  
  On November 17, 2026, crates.io published version `0.0.1` under `BUSL-1.1` stating that OxiHuman comes under Business Source License 1.1 from its next release; prior open-source releases (`0.1.0`, `0.2.1`) were yanked; the official GitHub repository returns `HTTP 404 Not Found`. Whether an older historical commit could be hosted under Apache-2.0 is an unresolved legal question. However, OxiHuman is rejected primarily on engineering grounds because its 38-target core pack lacks essential regional controls.

---

## 2. Reconciled Audit Table

| Component | Candidate A: NAVER Anny | Evidence / Pinned Source | Candidate B: OxiHuman | Evidence / Pinned Source |
|---|---|---|---|---|
| **Pinned Version / Commit** | `0.6.2` (PyPI release 2026-10-26) | `pyproject.toml`, PyPI API | `0.0.1` (Crates.io release 2026-11-17) | `Cargo.toml`, Crates.io API |
| **Repository URL** | https://github.com/naver/anny | Official NAVER LABS Europe | https://github.com/cool-japan/oxihuman | Returns `HTTP 404 Not Found` |
| **Source Code License** | **Apache-2.0** | `LICENSE` file in package | **BUSL-1.1** (0.0.1) / Apache-2.0 (Historical, yanked) | Crates.io API metadata |
| **Base Mesh License** | **CC0-1.0** (Public Domain) | MakeHuman CC0 data origin | **CC0-1.0** (Public Domain) | `PROVENANCE.md` (MakeHuman v1.3.0) |
| **Morph Targets License** | **CC0-1.0** (Public Domain) | MakeHuman CC0 data origin | **CC0-1.0** (Public Domain) | `PROVENANCE.md` (MakeHuman v1.3.0) |
| **Pretrained Weights / Blendshapes** | Open data (WHO demographic curves) | Documented in paper & package | Procedural blendshapes (38 targets) | `oxihuman-core-v1.ohpk` |
| **Restricted SMPL / SMPL-X Assets** | **STRICTLY EXCLUDED / ABSENT** | Package inspected; `smplx` not installed | **N/A** (MakeHuman topology only) | `PROVENANCE.md` |
| **Commercial SaaS Use Allowed?** | **YES** | Apache-2.0 §3 | **UNRESOLVED / RESTRICTED** | BUSL-1.1 prohibits without sponsorship |
| **Redistribution Allowed?** | **YES** (with NOTICE/attribution) | Apache-2.0 §4 | **UNRESOLVED / RESTRICTED** | BUSL-1.1 blocks production redistribution |
| **Zero-Budget (₹0) Compatibility** | **YES** | Free open source | **NO** (Commercial license requires fee) | COOLJAPAN OU sponsorship terms |
| **Commercial Selection Gate Verdict** | **PASS — APPROVED** | Legal Gate Cleared | **NON-SELECTED / DISQUALIFIED** | Disqualified on licensing & regional gaps |

---

## 3. Transitive Dependency Audit (Anny Environment)

Using `pip-licenses`, we audited every installed package in the Anny virtual environment (`.venv-anny`):

| Package Name | Version | License | Status | Notes |
|---|---|---|---|---|
| `anny` | 0.6.2 | Apache-2.0 | **PASS** | Permissive |
| `torch` | 2.14.1+cu130 | BSD-3-Clause | **PASS** | Permissive (PyTorch foundation) |
| `numpy` | 2.5.5 | BSD-3-Clause | **PASS** | Permissive |
| `scipy` | 1.18.1 | BSD-3-Clause | **PASS** | Permissive |
| `trimesh` | 5.2.2 | MIT | **PASS** | Permissive |
| `pygltflib` | 1.16.5 | MIT | **PASS** | Permissive |
| `roma` | 1.8.0 | Apache-2.0 | **PASS** | Permissive (Rotation mathematics) |
| `safetensors` | 0.8.0 | Apache-2.0 | **PASS** | Permissive (Hugging Face) |
| `pyyaml` | 6.0.4 | MIT | **PASS** | Permissive |
| `pillow` | 13.0.0 | HPND | **PASS** | Permissive (BSD-like) |
| `requests` | 2.34.2 | Apache-2.0 | **PASS** | Permissive |
| `psutil` | 7.2.2 | BSD-3-Clause | **PASS** | Permissive |
| `warp-lang` | 1.19.0 | Apache-2.0 | **PASS** | Permissive (NVIDIA) |
| `smplx` | **NOT INSTALLED** | N/A | **PASS** | Excluded |
| `chumpy` | **NOT INSTALLED** | N/A | **PASS** | Excluded |

**Finding:** Out of 34 total packages in the virtual environment, zero packages carry copyleft (AGPL, GPL) or non-commercial research licenses. All transitive dependencies are under standard permissive licenses (MIT, BSD, Apache).

---

## 4. Production Attribution Obligations

When deploying Anny in the WearWise production backend:
1. Retain NAVER LABS Europe copyright notice:
   ```text
   Copyright (c) 2025-2026 NAVER LABS Europe.
   Licensed under the Apache License, Version 2.0.
   ```
2. Credit the MakeHuman Community for the underlying CC0 3D mesh and morphological blendshape targets:
   ```text
   3D body mesh topology and base blendshapes derived from MakeHuman (CC0 1.0 Universal).
   ```
3. Include standard `NOTICE` and `LICENSE` files in the repository root.
