import hashlib
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
FRONTEND_DIR = REPO / "frontend"
BE_DIR = REPO / "WEARWISE-BODY-ENGINE"
COMMERCE_DIR = REPO / "backend"
PY_EXE = str(BE_DIR / ".venv-anny" / "Scripts" / "python.exe")

OUT_11_3 = REPO / "artifacts" / "phase11" / "phase11_3"
OUT_11_4 = REPO / "artifacts" / "phase11" / "phase11_4"
for d in (OUT_11_3, OUT_11_4):
    d.mkdir(parents=True, exist_ok=True)

REV3_EXPECTED = {
    "S": (BE_DIR / "artifacts/merchant_patterns/graded_m2rc/S/TSH-WW-CREW-001_S_candidate_rev3.glb", "8f9bd0c79c54d4f40e3354f729c5f236634acec3a06d33a1f0ec771b51e41690"),
    "M": (BE_DIR / "artifacts/merchant_patterns/graded_m2rc/M/TSH-WW-CREW-001_M_candidate_rev3.glb", "9b6212ff218ba6231000cdca1716f808fd501df4e843353655ec7ce4d7389769"),
    "L": (BE_DIR / "artifacts/merchant_patterns/graded_m2rc/L/TSH-WW-CREW-001_L_candidate_rev3.glb", "4bc1a0cbcb0cccbe3b4bd5646b614bc881a06d5db06ec44b0034a577e8101387"),
}


def wait_http(url: str, timeout: int = 25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Service did not start: {url}")


def main():
    env = os.environ.copy()
    env["MONGODB_BODY_ENGINE_DB"] = "wearwise_body_engine_staging"
    env["MONGODB_COMMERCE_DB"] = "wearwise_commerce_staging"
    env["WEARWISE_ENV"] = "development"

    p_be = subprocess.Popen(
        [PY_EXE, "-m", "uvicorn", "app.api.app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BE_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    p_com = subprocess.Popen(
        [PY_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=str(COMMERCE_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    p_fe = subprocess.Popen(
        ["cmd", "/c", "npx vite preview --host 127.0.0.1 --port 4173 --strictPort"],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_http("http://127.0.0.1:8000/health")
        wait_http("http://127.0.0.1:8001/health")
        wait_http("http://127.0.0.1:4173/")

        results = {"desktop_chrome": {}, "mobile_chrome": {}, "desktop_edge": {}, "failure_recovery": {}}

        with sync_playwright() as p:
            # 1. Desktop Chrome (1440x900)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))

            t0 = time.time()
            page.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=1", wait_until="networkidle")
            page.wait_for_timeout(1600)
            load_sec = round(time.time() - t0, 2)

            fit_m = page.get_by_test_id("fit-summary-card").inner_text()
            page.get_by_test_id("toggle-dev-diag").click()
            page.wait_for_timeout(300)
            diag_m = json.loads(page.get_by_test_id("dev-diagnostics").get_attribute("data-metrics") or "{}")
            page.screenshot(path=str(OUT_11_3 / "tryon_desktop_M_P0.png"))

            # Pose P3 + Avatar switch + Size S comparison
            page.get_by_test_id("tryon-pose-P3").click()
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUT_11_3 / "tryon_desktop_M_P3.png"))

            page.get_by_test_id("avatar-select").select_option("PROFILE_D_PETITE_FEMININE")
            page.wait_for_timeout(1200)
            fit_petite_m = page.get_by_test_id("fit-summary-card").inner_text()

            page.get_by_test_id("size-btn-S").click()
            page.wait_for_timeout(1200)
            fit_petite_s = page.get_by_test_id("fit-summary-card").inner_text()
            page.screenshot(path=str(OUT_11_3 / "tryon_desktop_petite_S.png"))

            # Add to cart & verify /cart
            page.get_by_test_id("add-to-cart-btn").click()
            page.wait_for_timeout(800)
            cart_banner = page.get_by_test_id("cart-status-banner").inner_text()
            page.goto("http://127.0.0.1:4173/cart", wait_until="networkidle")
            page.wait_for_timeout(800)
            cart_has_sku = "TSH-WW-PHASE11-ACCEPTANCE-001" in page.locator("body").inner_text()
            page.screenshot(path=str(OUT_11_3 / "staging_cart_with_tryon_sku.png"))

            # Failure & Recovery: stale revision 999 must fail closed
            page.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=999", wait_until="networkidle")
            page.wait_for_timeout(900)
            err_banner = page.get_by_test_id("tryon-error-banner").inner_text()
            page.screenshot(path=str(OUT_11_4 / "fail_closed_stale_revision.png"))

            results["desktop_chrome"] = {
                "load_sec": load_sec,
                "fit_M_athletic": fit_m.splitlines()[1] if len(fit_m.splitlines()) > 1 else fit_m,
                "fit_M_petite": fit_petite_m.splitlines()[1] if len(fit_petite_m.splitlines()) > 1 else fit_petite_m,
                "fit_S_petite": fit_petite_s.splitlines()[1] if len(fit_petite_s.splitlines()) > 1 else fit_petite_s,
                "worker_mode": diag_m.get("workerMode"),
                "fps": diag_m.get("fps"),
                "avg_fps": diag_m.get("avgFps"),
                "cart_banner": cart_banner,
                "cart_has_sku": cart_has_sku,
                "page_errors": errs,
            }
            results["failure_recovery"] = {"stale_rev_999_error": err_banner}
            browser.close()

            # 2. Mobile Chrome Emulation (390x844)
            browser_mob = p.chromium.launch(headless=True)
            ctx_mob = browser_mob.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
            page_mob = ctx_mob.new_page()
            mob_errs = []
            page_mob.on("pageerror", lambda e: mob_errs.append(str(e)))
            page_mob.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=1", wait_until="networkidle")
            page_mob.wait_for_timeout(1500)
            page_mob.get_by_test_id("tryon-pose-P1").click()
            page_mob.wait_for_timeout(900)
            page_mob.screenshot(path=str(OUT_11_4 / "tryon_mobile_chrome.png"))
            results["mobile_chrome"] = {"rendered": page_mob.get_by_test_id("fit-summary-card").is_visible(), "page_errors": mob_errs}
            browser_mob.close()

            # 3. Desktop Edge (channel="msedge")
            try:
                browser_edge = p.chromium.launch(channel="msedge", headless=True)
                page_edge = browser_edge.new_page(viewport={"width": 1280, "height": 800})
                edge_errs = []
                page_edge.on("pageerror", lambda e: edge_errs.append(str(e)))
                page_edge.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=1", wait_until="networkidle")
                page_edge.wait_for_timeout(1500)
                page_edge.screenshot(path=str(OUT_11_4 / "tryon_desktop_edge.png"))
                results["desktop_edge"] = {"available": True, "rendered": page_edge.get_by_test_id("fit-summary-card").is_visible(), "page_errors": edge_errs}
                browser_edge.close()
            except Exception as ex:
                results["desktop_edge"] = {"available": False, "error": str(ex)}

        rev3_intact = {
            sz: hashlib.sha256(fp.read_bytes()).hexdigest() == exp
            for sz, (fp, exp) in REV3_EXPECTED.items()
        }
        results["protected_rev3_intact"] = rev3_intact

        (OUT_11_3 / "tryon_e2e_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        (OUT_11_4 / "cross_device_qa_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print("PHASE11_3_4_E2E_OK:", json.dumps(results, indent=2))
    finally:
        for proc in (p_fe, p_be, p_com):
            try:
                proc.terminate()
            except Exception:
                pass
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
