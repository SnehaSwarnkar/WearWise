# WearWise — Phase 5A Verification Packet Manifest
**Git Branch:** `noTouch`  
**Base Commit:** `d3f3619ff53d3f61fa9c34bf00284e74eff4c4ed`  

## Included Source Files & SHA-256 Checksums

| File Path | SHA-256 Checksum | Size (bytes) |
|---|---|---:|
| `app/domain/taxonomies/garment.py` | `15e6afdf8bd2b725945d2e7613334958c6a88e194f41e9af7b20797d2b4f515a` | 1,195 |
| `app/domain/entities/garment.py` | `74aa0e8ea99141248cb4175716b86d07c9e6241b0474a5ea1cdda7c69ae941cf` | 6,551 |
| `app/fit/__init__.py` | `a0db3f53a856bfd1365472b0d872b605a356f2a25edce739c5e72052552dcf24` | 984 |
| `app/fit/engine.py` | `438d2be1a7ab40929b597bb603c051fe6767db33d3e89a394df2c3937a7ae783` | 20,896 |
| `app/fit/models.py` | `1bc76240675ec3b32c33ec3f54937cdcb3388db6f78b272e7667de73ae71e212` | 6,426 |
| `app/fit/port.py` | `771d6e9f596a45aee6bcad18703005fc00b937cf338534d3d54d61448635b8cf` | 6,812 |
| `app/fit/registry.py` | `7f98979cb4433204a7eca31e7a0f9a4caa76b40893a37fa9663bc2b55cbc5f3b` | 8,891 |
| `app/fit/rulebook.py` | `a763a9cb11fdcec7ea0a79682e3601b9ebd26e9eeb8b303c7befe59a2f68d7db` | 4,649 |
| `tests/fit/test_honest_fit.py` | `a4294db06c113adc2e452506fa2dd90023e4d140243451dcd4c4215bf37fc9c3` | 18,786 |
| `tests/fit/test_boundary_cases.py` | `21d2f5398ae67d42c1a61b92ea548f97474adc55fdc47f2f467b369a05202bd3` | 8,393 |
| `scripts/demo_honest_fit.py` | `75f5680a45110f5fa92105890c1d8d56afde3d58b6c331bc6970c861b26edb68` | 16,445 |
| `docs/architecture/HONEST_FIT_PENALTY_COEFFICIENT_PROPOSAL.md` | `74311faccae73c5ca4f743305765fb755d54533e7376bfcfa7fe2ba1e189c6fd` | 14,917 |
| `artifacts/phase5a/phase5a_tshirt_fit_report.json` | `eda0b278764d03f31ddf163cad85ba1602f6d4034f4dee4304a99ae3624889fb` | 13,630 |
| `artifacts/phase5a/phase5a_casual_shirt_fit_report.json` | `702fc21aaada9fa4b925235d4a8f4de4b5b53bf68bc20f6dab11fcaf9f79a5d3` | 12,238 |

## Review Findings Verification Status

| Criterion ID | Review Criterion | Verification Status | Verification Detail |
|---|---|:---:|---|
| `1_recommendation_status_consistency` | 1 Recommendation Status Consistency | **PASSED** | Size S is 'recommended', Size XS is 'alternative', exactly 1 recommended size |
| `2_hip_weighting_policy` | 2 Hip Weighting Policy | **PASSED** | Authoritative policy established: bottoms baseline 0.40, provisional discount 0.5x yields effective weight 0.20 |
| `3_sensitivity_table_denominator_reconciliation` | 3 Sensitivity Table Denominator Reconciliation | **PASSED** | Proposal reconciles raw penalty with normalized multi-zone composite scores across T-shirt and casual shirt denominators |
| `4_garment_measurement_provenance` | 4 Garment Measurement Provenance | **PASSED** | GarmentMeasurementProvenance implemented; disclaimer claim recorded; mechanical stretch separated from fibre composition |
