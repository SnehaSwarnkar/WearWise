import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
FRONTEND_DIR = REPO / "frontend"
OUT_DIR = REPO / "artifacts" / "phase10_experimental"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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


def main():
    p_fe = subprocess.Popen(
        ["cmd", "/c", "npx vite preview --host 127.0.0.1 --port 4173 --strictPort"],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    results = {"poses": {}, "console_errors": [], "network_failures": []}
    try:
        wait_preview("http://127.0.0.1:4173/")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("console", lambda m: results["console_errors"].append(m.text) if m.type == "error" else None)
            page.on("requestfailed", lambda r: results["network_failures"].append({"url": r.url, "failure": r.failure}))

            page.goto("http://127.0.0.1:4173/experimental-phase10", wait_until="networkidle")
            page.wait_for_timeout(1500)

            for pid in ["P0", "P1", "P2", "P3"]:
                page.get_by_test_id(f"pose-btn-{pid}").click()
                page.wait_for_timeout(1400)
                tel = page.get_by_test_id("phase10-telemetry").inner_text()
                shot = OUT_DIR / f"phase10_pose_{pid}.png"
                page.screenshot(path=str(shot))
                results["poses"][pid] = {"telemetry": tel, "screenshot": str(shot)}

            browser.close()

        for sz, (fp, exp) in REV3_EXPECTED.items():
            assert sha256_bytes(fp.read_bytes()) == exp
        results["protected_rev3_intact"] = True

        out_json = OUT_DIR / "phase10_pose_results.json"
        out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("PHASE10_PROTOTYPE_VERIFIED:", out_json)
    finally:
        p_fe.terminate()
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
