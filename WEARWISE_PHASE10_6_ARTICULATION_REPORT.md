# WEARWISE — PHASE 10.6 FULL ARTICULATED BODY MOVEMENT REPORT

**Phase:** 10.6 — Full Articulated Body Movement  
**Pose Library & Controls:** [ArticulatedPoseLibrary.ts](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/ArticulatedPoseLibrary.ts), [Phase10SimPage.tsx](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/frontend/src/experimental_phase10/Phase10SimPage.tsx)  
**Machine-Readable Results:** [articulation_poses_P0_P11.json](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/articulation_poses_P0_P11.json)

---

## 1. Anny 104-Bone Upper-Body Hierarchy & Angle Conventions

From `anny_rigged_male_exp.glb`, upper-body articulation uses parent-child world-axis-mapped quaternion deltas around rest poses (`restQuats`), distributing spinal motion smoothly across `spine04 → spine03 → spine02 → spine01`:
- **Torso (`spine04..spine01`):** Forward lean (`-15°..30°`, world `+X`), lateral lean (`-20°..20°`, world `-Z`), axial twist (`-30°..30°`, world `+Y`). Garment rest guidance blends continuously by height between `spine03` (waist/hem) and `spine01` (chest/collar).
- **Clavicles (`clavicle.L/R`):** Upward shrug (`0°..20°`, world `+Z` / `-Z`).
- **Shoulders (`upperarm01.L/R`):** Coronal elevation/abduction (`0°..90°`, world `+Z` / `-Z`) and sagittal forward flexion (`0°..80°`, world `-X`).
- **Elbows (`lowerarm01.L/R`):** Flexion (`0°..110°`, world `-X`).
- **Forearms & Wrists (`lowerarm02.L/R`, `wrist.L/R`):** Axial forearm pronation/supination (`-45°..45°`, local `Y`) and wrist flexion (`-25°..25°`, local `X`).

---

## 2. Predefined Pose Library (`P0`–`P11`) — Measured Results (`waffle_knit_240`)

| Pose | Description | Max Disp | Mean Stretch | Mean Bend Dev | Penetrating Particles | Max Pen | Seam Sep | Solve Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P0** | Neutral A-pose (`0°`) | `3.22 cm` | `1.0063` | `0.0092` | `4` | `1.94 mm` | `0.000 mm` | `7.4 ms` |
| **P1** | Both arms elevated `30°` + `4°` clavicle | `16.89 cm` | `1.0201` | `0.0355` | `35` | `6.27 mm` | `0.000 mm` | `7.7 ms` |
| **P2** | Both arms elevated `45°` + `7°` clavicle | `25.47 cm` | `1.0350` | `0.0579` | `56` | `14.00 mm` | `0.000 mm` | `7.3 ms` |
| **P3** | Both arms elevated `90°` + `14°` clavicle | `45.13 cm` | `1.0676` | `0.1083` | `136` | `12.08 mm` | `0.000 mm` | `7.6 ms` |
| **P4** | Left arm raised `75°`, right neutral | `38.51 cm` | `1.0351` | `0.0577` | `69` | `11.09 mm` | `0.000 mm` | `7.5 ms` |
| **P5** | Right arm raised `75°`, left neutral | `38.09 cm` | `1.0293` | `0.0499` | `58` | `8.56 mm` | `0.000 mm` | `7.3 ms` |
| **P6** | Elbows flexed `60°` + forearm `20°` + wrist `15°` | `3.61 cm` | `1.0062` | `0.0103` | `57` | `17.05 mm` | `0.000 mm` | `8.2 ms` |
| **P7** | Arms forward `50°` + elbows `20°` | `16.73 cm` | `1.0182` | `0.0394` | `48` | `9.94 mm` | `0.000 mm` | `7.8 ms` |
| **P8** | Arms overhead `85°` + elbows `45°` | `42.51 cm` | `1.0561` | `0.0932` | `126` | `14.16 mm` | `0.000 mm` | `7.3 ms` |
| **P9** | Torso forward lean `22°` + elbows `15°` | `14.06 cm` | `1.0066` | `0.0187` | `15` | `3.45 mm` | `0.000 mm` | `7.5 ms` |
| **P10** | Torso lateral lean `16°` + L shoulder `10°` | `10.77 cm` | `1.0094` | `0.0201` | `19` | `4.27 mm` | `0.000 mm` | `7.6 ms` |
| **P11** | Combined twist `18°` + leans + L `65°`/R `35°` | `30.00 cm` | `1.0313` | `0.0618` | `48` | `15.32 mm` | `0.000 mm` | `7.5 ms` |

### Visual Evidence (`phase10_6/`)
- [pose_P0.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P0.png), [pose_P3.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P3.png), [pose_P4.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P4.png), [pose_P6.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P6.png), [pose_P7.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P7.png), [pose_P8.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P8.png), [pose_P9.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P9.png), [pose_P10.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P10.png), [pose_P11.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_6/pose_P11.png).
- **Continuous Slider Check:** [continuous_slider_pose.png](file:///c:/Users/Lenovo/Documents/Major%20Project/WearWise/artifacts/phase10_experimental/phase10_8/continuous_slider_pose.png) (`elbowFlexL=75°`, `torsoTwist=20°` → `29.97 cm` max disp, `56` penetrating particles, `0.000 mm` seam separation).

## 3. Known Articulation Limitations
- External/internal upper-arm axial humeral rotation is not exposed separately from coronal abduction + sagittal flexion.
- Lower-body pelvis/hip/knee joints remain in neutral stance because the experimental garment is an upper-body crew-neck T-shirt.
