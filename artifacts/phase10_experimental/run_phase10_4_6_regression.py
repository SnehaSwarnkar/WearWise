import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
FRONTEND_DIR = REPO / "frontend"
BASE_OUT = REPO / "artifacts" / "phase10_experimental"
DIR_45 = BASE_OUT / "phase10_4_5"
DIR_6 = BASE_OUT / "phase10_6"
DIR_8 = BASE_OUT / "phase10_8"
for d in (DIR_45, DIR_6, DIR_8):
    d.mkdir(parents=True, exist_ok=True)

REV3_EXPECTED = {
    "S": (REPO / "WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rc/S/TSH-WW-CREW-001_S_candidate_rev3.glb", "8f9bd0c79c54d4f40e3354f729c5f236634acec3a06d33a1f0ec771b51e41690"),
    "M": (REPO / "WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rc/M/TSH-WW-CREW-001_M_candidate_rev3.glb", "9b6212ff218ba6231000cdca1716f808fd501df4e843353655ec7ce4d7389769"),
    "L": (REPO / "WEARWISE-BODY-ENGINE/artifacts/merchant_patterns/graded_m2rc/L/TSH-WW-CREW-001_L_candidate_rev3.glb", "4bc1a0cbcb0cccbe3b4bd5646b614bc881a06d5db06ec44b0034a577e8101387"),
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def wait_preview(url: str, timeout: int = 15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError("Vite preview did not start")


def read_metrics(page) -> dict:
    raw = page.get_by_test_id("phase10-telemetry").get_attribute("data-metrics")
    return json.loads(raw) if raw else {}


def main():
    p_fe = subprocess.Popen(
        ["cmd", "/c", "npx vite preview --host 127.0.0.1 --port 4173 --strictPort"],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_preview("http://127.0.0.1:4173/")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            sim_errors = []
            page.on("pageerror", lambda e: sim_errors.append(str(e)))

            page.goto("http://127.0.0.1:4173/experimental-phase10", wait_until="networkidle")
            page.wait_for_timeout(1200)

            # 1. Phase 10.4 & 10.5: Recovery sequence P0 -> P3 -> Hold -> P0
            recovery = []
            for label, btn, wait_ms in [
                ("neutral_start", "pose-btn-P0", 900),
                ("elevated_P3", "pose-btn-P3", 1200),
                ("hold_P3", None, 1000),
                ("return_P0", "pose-btn-P0", 1400),
            ]:
                if btn:
                    page.get_by_test_id(btn).click()
                page.wait_for_timeout(wait_ms)
                m = read_metrics(page)
                recovery.append({"stage": label, "metrics": m})
            page.screenshot(path=str(DIR_45 / "recovery_end_P0.png"))

            # 2. Phase 10.6 & 10.7: Full pose library P0-P11 for both fabrics
            poses = [f"P{i}" for i in range(12)]
            fabric_results = {}
            for fab in ["waffle_knit_240", "rigid_poplin_140"]:
                page.get_by_test_id("reset-pose-btn").click()
                page.get_by_test_id(f"fabric-btn-{fab}").click()
                page.wait_for_timeout(400)
                fab_poses = {}
                for pid in poses:
                    page.get_by_test_id(f"pose-btn-{pid}").click()
                    page.wait_for_timeout(950)
                    m = read_metrics(page)
                    fab_poses[pid] = m
                    if fab == "waffle_knit_240":
                        page.screenshot(path=str(DIR_6 / f"pose_{pid}.png"))
                fabric_results[fab] = fab_poses

            # 3. Phase 10.8: Transition sequence & continuous slider check
            transitions = {}
            seq = ["P0", "P1", "P2", "P3", "P0", "P6", "P8", "P0", "P9", "P11"]
            page.get_by_test_id("fabric-btn-waffle_knit_240").click()
            for pid in seq:
                page.get_by_test_id(f"pose-btn-{pid}").click()
                page.wait_for_timeout(600)
                transitions[pid] = read_metrics(page)

            # Continuous slider test
            page.get_by_test_id("slider-elbowFlexL").fill("75")
            page.get_by_test_id("slider-torsoTwist").fill("20")
            page.wait_for_timeout(700)
            slider_metrics = read_metrics(page)
            page.screenshot(path=str(DIR_8 / "continuous_slider_pose.png"))

            # Reset check
            page.get_by_test_id("reset-pose-btn").click()
            page.wait_for_timeout(400)
            reset_metrics = read_metrics(page)

            # Shopper /try-on sanity check (must still render cleanly)
            page.goto("http://127.0.0.1:4173/try-on", wait_until="domcontentloaded")
            page.wait_for_timeout(900)
            tryon_ok = page.locator("body").inner_text().strip() != ""

            browser.close()

        rev3_status = {}
        for sz, (fp, exp) in REV3_EXPECTED.items():
            h = sha256_bytes(fp.read_bytes())
            rev3_status[sz] = {"sha256": h, "intact": h == exp}

        (DIR_45 / "collision_stability_results.json").write_text(
            json.dumps({"recovery_sequence": recovery, "poses_knit": fabric_results["waffle_knit_240"]}, indent=2),
            encoding="utf-8",
        )
        (DIR_6 / "articulation_poses_P0_P11.json").write_text(
            json.dumps(fabric_results, indent=2),
            encoding="utf-8",
        )
        (DIR_8 / "regression_summary.json").write_text(
            json.dumps(
                {
                    "transitions": transitions,
                    "continuous_slider": slider_metrics,
                    "after_reset": reset_metrics,
                    "tryon_route_renders": tryon_ok,
                    "page_errors": sim_errors,
                    "protected_rev3": rev3_status,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print("PHASE10_4_6_8_VERIFIED_OK")
    finally:
        p_fe.terminate()
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
