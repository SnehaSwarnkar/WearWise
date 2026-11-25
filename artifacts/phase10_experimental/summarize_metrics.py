import json
from pathlib import Path

base = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise\artifacts\phase10_experimental")
d = json.loads((base / "phase10_6/articulation_poses_P0_P11.json").read_text())
for i in range(12):
    pid = f"P{i}"
    k = d["waffle_knit_240"][pid]
    p = d["rigid_poplin_140"][pid]
    print(
        f"{pid:3s} | KNIT disp={k['maxDisplacementCm']:5.2f} str={k['maxStretchRatio']:.3f} meanStr={k['meanStretchRatio']:.4f} "
        f"comp={k['maxCompressionRatio']:.3f} bend={k['meanBendDeviation']:.4f} res={k['constraintResidual']:.3f} "
        f"pen={k['penetratingParticles']:3d} maxP={k['maxPenetrationMm']:5.2f} meanP={k['meanPenetrationMm']:4.2f} solve={k['lastSolveMs']:4.1f} fps={k['fps']}"
    )
    print(
        f"    | POPL disp={p['maxDisplacementCm']:5.2f} str={p['maxStretchRatio']:.3f} meanStr={p['meanStretchRatio']:.4f} "
        f"comp={p['maxCompressionRatio']:.3f} bend={p['meanBendDeviation']:.4f} res={p['constraintResidual']:.3f} "
        f"pen={p['penetratingParticles']:3d} maxP={p['maxPenetrationMm']:5.2f} meanP={p['meanPenetrationMm']:4.2f} solve={p['lastSolveMs']:4.1f} fps={p['fps']}"
    )

r = json.loads((base / "phase10_8/regression_summary.json").read_text())
print("SLIDER:", r["continuous_slider"]["maxDisplacementCm"], "cm, pen:", r["continuous_slider"]["penetratingParticles"], "seamSep:", r["continuous_slider"]["seamSeparationMm"])
print("RESET:", r["after_reset"]["maxDisplacementCm"], "cm, pen:", r["after_reset"]["penetratingParticles"])
print("TRYON_OK:", r["tryon_route_renders"], "PAGE_ERRORS:", len(r["page_errors"]))
print("REV3:", {k: v["intact"] for k, v in r["protected_rev3"].items()})
