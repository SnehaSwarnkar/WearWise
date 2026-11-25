import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
FRONTEND_DIR = REPO / "frontend"
OUT_DIR = REPO / "artifacts" / "phase10_experimental" / "phase10_9"
OUT_DIR.mkdir(parents=True, exist_ok=True)


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
            page_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto("http://127.0.0.1:4173/experimental-phase10", wait_until="networkidle")
            page.wait_for_timeout(1500)

            init_m = read_metrics(page)
            results = {"init": init_m, "poses": {}, "reset_sync": {}, "page_errors": page_errors}

            for pid in ["P0", "P1", "P2", "P3", "P6", "P8", "P11"]:
                page.get_by_test_id(f"pose-btn-{pid}").click()
                page.wait_for_timeout(1100)
                m = read_metrics(page)
                results["poses"][pid] = m
                if pid in ("P3", "P6", "P8", "P11"):
                    page.screenshot(path=str(OUT_DIR / f"worker_pose_{pid}.png"))

            # Test Reset synchronization from P11 -> Reset P0
            epoch_before = read_metrics(page).get("resetEpoch", 0)
            page.get_by_test_id("reset-pose-btn").click()
            page.wait_for_timeout(350)
            m_reset = read_metrics(page)
            page.screenshot(path=str(OUT_DIR / "worker_after_reset.png"))
            results["reset_sync"] = {
                "epoch_before": epoch_before,
                "epoch_after": m_reset.get("resetEpoch"),
                "simState": m_reset.get("simState"),
                "maxDisplacementCm": m_reset.get("maxDisplacementCm"),
                "penetratingParticles": m_reset.get("penetratingParticles"),
            }

            browser.close()

        (OUT_DIR / "phase10_9_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("WORKER_MODE:", results["init"].get("workerMode"))
        print("RESET_SYNC:", results["reset_sync"])
        for pid in ["P0", "P3", "P6", "P8", "P11"]:
            m = results["poses"][pid]
            print(f"{pid}: fps={m.get('fps')} avgFps={m.get('avgFps')} solve={m.get('lastSolveMs')}ms comm={m.get('workerCommMs')}ms pen={m.get('penetratingParticles')} maxP={m.get('maxPenetrationMm')}mm tunnel={m.get('tunnelingIncidents')}")
    finally:
        p_fe.terminate()
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
