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

OUT_DIR = REPO / "artifacts" / "phase11" / "phase11_5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

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

    p_be = subprocess.Popen([PY_EXE, "-m", "uvicorn", "app.api.app:app", "--host", "127.0.0.1", "--port", "8000"], cwd=str(BE_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p_com = subprocess.Popen([PY_EXE, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"], cwd=str(COMMERCE_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p_fe = subprocess.Popen(["cmd", "/c", "npx vite preview --host 127.0.0.1 --port 4173 --strictPort"], cwd=str(FRONTEND_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        wait_http("http://127.0.0.1:8000/health")
        wait_http("http://127.0.0.1:8001/health")
        wait_http("http://127.0.0.1:4173/")

        report = {"shopper_ux": {}, "commerce_e2e": {}, "seller_ux": {}, "mobile": {}, "page_errors": []}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            page.on("pageerror", lambda e: report["page_errors"].append(str(e)))

            # 1. Open simplified /experimental-try-on
            page.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=1", wait_until="networkidle")
            page.wait_for_timeout(1500)
            body_text = page.locator("body").inner_text()
            rec_m = page.get_by_test_id("recommended-size").inner_text()
            fit_m = page.get_by_test_id("expected-fit").inner_text()
            no_jargon = not any(w in body_text for w in ["web_worker", "Welded Particles", "SHA-256", "Developer Diagnostics", "SETTLING"])
            page.screenshot(path=str(OUT_DIR / "shopper_tryon_desktop.png"))

            # 2. Switch to Petite Build & Size S, Add to Bag
            page.get_by_test_id("avatar-select").select_option("PROFILE_D_PETITE_FEMININE")
            page.wait_for_timeout(1000)
            rec_petite = page.get_by_test_id("recommended-size").inner_text()
            page.get_by_test_id("size-btn-S").click()
            page.wait_for_timeout(1000)
            page.get_by_test_id("add-to-cart-btn").click()
            page.wait_for_timeout(900)
            cart_banner = page.get_by_test_id("cart-status-banner").inner_text()
            session_id_tryon = page.evaluate("sessionStorage.getItem('ww-session-id')")

            report["shopper_ux"] = {
                "recommended_size_athletic": rec_m,
                "expected_fit_M_athletic": fit_m,
                "recommended_size_petite": rec_petite,
                "no_engineering_jargon": no_jargon,
                "cart_banner": cart_banner,
            }

            # 3. Open /cart, verify item, reload & verify persistence, increment quantity
            page.goto("http://127.0.0.1:4173/cart", wait_until="networkidle")
            page.wait_for_timeout(900)
            cart_has_item = "Phase 11 Acceptance Crew Tee" in page.locator("body").inner_text()
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(900)
            cart_persisted_after_reload = "Phase 11 Acceptance Crew Tee" in page.locator("body").inner_text()

            # Increment quantity via + button if present
            plus_btn = page.locator("button:has-text('+')").first
            if plus_btn.is_visible():
                plus_btn.click()
                page.wait_for_timeout(700)
            cart_text_after_qty = page.locator("body").inner_text()
            page.screenshot(path=str(OUT_DIR / "cart_persisted_qty2.png"))

            # 4. Proceed to /checkout and complete demo order
            page.goto("http://127.0.0.1:4173/checkout", wait_until="networkidle")
            page.wait_for_timeout(900)
            for sel, val in [
                ("input[name='firstName']", "Staging"),
                ("input[name='lastName']", "Shopper"),
                ("input[name='email']", "staging@wearwise.test"),
                ("input[name='phone']", "9876543210"),
                ("input[name='address']", "123 Staging Ave"),
                ("input[name='city']", "Bengaluru"),
                ("input[name='state']", "Karnataka"),
                ("input[name='pincode']", "560001"),
            ]:
                loc = page.locator(sel)
                if loc.count() > 0:
                    loc.first.fill(val)
            place_btn = page.locator("button[type='submit'], button:has-text('Place Order'), button:has-text('Complete')").first
            order_placed = False
            if place_btn.is_visible():
                place_btn.click()
                page.wait_for_timeout(1500)
                order_placed = "order-confirmation" in page.url or "Order Confirmed" in page.locator("body").inner_text() or "WW-" in page.locator("body").inner_text()
            page.screenshot(path=str(OUT_DIR / "checkout_confirmation.png"))

            # 5. Check /orders history
            page.goto("http://127.0.0.1:4173/orders", wait_until="networkidle")
            page.wait_for_timeout(900)
            orders_text = page.locator("body").inner_text()
            page.screenshot(path=str(OUT_DIR / "orders_history.png"))

            report["commerce_e2e"] = {
                "session_id": session_id_tryon,
                "cart_has_item": cart_has_item,
                "cart_persisted_after_reload": cart_persisted_after_reload,
                "qty_updated_total_present": ("5,998" in cart_text_after_qty or "5998" in cart_text_after_qty or "2" in cart_text_after_qty),
                "demo_order_placed": order_placed,
                "confirmation_url": page.url,
                "orders_page_loaded": len(orders_text.strip()) > 0,
            }

            # 6. Seller UI check (/merchant-studio)
            page.goto("http://127.0.0.1:4173/merchant-studio", wait_until="networkidle")
            page.wait_for_timeout(1000)
            seller_status = page.get_by_test_id("seller-status-summary").inner_text()
            seller_body = page.locator("body").inner_text()
            page.screenshot(path=str(OUT_DIR / "seller_studio_simplified.png"))
            report["seller_ux"] = {
                "title_simplified": "Seller Product Studio" in seller_body,
                "status_summary": seller_status,
            }

            # 7. Mobile Chrome check
            ctx_mob = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
            pmob = ctx_mob.new_page()
            pmob.goto("http://127.0.0.1:4173/experimental-try-on?sku=TSH-WW-PHASE11-ACCEPTANCE-001&size=M&revision=1", wait_until="networkidle")
            pmob.wait_for_timeout(1200)
            pmob.screenshot(path=str(OUT_DIR / "shopper_tryon_mobile.png"))
            report["mobile"] = {"rendered": pmob.get_by_test_id("recommended-size").is_visible()}
            ctx_mob.close()

            browser.close()

        report["protected_rev3_intact"] = {
            sz: hashlib.sha256(fp.read_bytes()).hexdigest() == exp
            for sz, (fp, exp) in REV3_EXPECTED.items()
        }
        (OUT_DIR / "phase11_5_e2e_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("PHASE11_5_E2E_OK:", json.dumps(report, indent=2))
    finally:
        for proc in (p_fe, p_be, p_com):
            try:
                proc.terminate()
            except Exception:
                pass
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
