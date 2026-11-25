import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from pymongo import MongoClient

REPO_ROOT = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
BODY_ENGINE_DIR = REPO_ROOT / "WEARWISE-BODY-ENGINE"
COMMERCE_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
VENV_PY = BODY_ENGINE_DIR / ".venv-anny" / "Scripts" / "python.exe"
OUT_DIR = REPO_ROOT / "artifacts" / "m5_ab_closure"
OUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(REPO_ROOT / ".env")
MONGODB_URI = os.getenv("MONGODB_URI", "")
STAGING_BODY_DB = "wearwise_body_engine_staging"
STAGING_COMM_DB = "wearwise_commerce_staging"
TEST_SKU = "TSH-WW-ACCEPTANCE-001"

REV3_EXPECTED = {
    "S": (BODY_ENGINE_DIR / "artifacts/merchant_patterns/graded_m2rc/S/TSH-WW-CREW-001_S_candidate_rev3.glb", "8f9bd0c79c54d4f40e3354f729c5f236634acec3a06d33a1f0ec771b51e41690"),
    "M": (BODY_ENGINE_DIR / "artifacts/merchant_patterns/graded_m2rc/M/TSH-WW-CREW-001_M_candidate_rev3.glb", "9b6212ff218ba6231000cdca1716f808fd501df4e843353655ec7ce4d7389769"),
    "L": (BODY_ENGINE_DIR / "artifacts/merchant_patterns/graded_m2rc/L/TSH-WW-CREW-001_L_candidate_rev3.glb", "4bc1a0cbcb0cccbe3b4bd5646b614bc881a06d5db06ec44b0034a577e8101387"),
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def http_req(url: str, method: str = "GET", body=None, headers=None, timeout: int = 10):
    hdrs = dict(headers or {})
    data = json.dumps(body).encode("utf-8") if body is not None else None
    if body is not None:
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def wait_health(url: str, timeout: int = 15, expect_json: bool = True):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            st, _, raw = http_req(url, timeout=3)
            if st == 200:
                return json.loads(raw.decode("utf-8")) if expect_json else {"ok": True}
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError(f"Service did not become healthy at {url}")


def main():
    env = os.environ.copy()
    env["MONGODB_BODY_ENGINE_DB"] = STAGING_BODY_DB
    env["MONGODB_COMMERCE_DB"] = STAGING_COMM_DB
    env["PYTHONIOENCODING"] = "utf-8"

    procs = []
    evidence = {
        "staging_dbs": {"body_engine": STAGING_BODY_DB, "commerce": STAGING_COMM_DB},
        "routes_visited": [],
        "api_calls": [],
        "console_errors": [],
        "network_failures": [],
        "screenshots": {},
    }
    try:
        procs.append(subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.api.app:app", "--host", "127.0.0.1", "--port", "8000"], cwd=str(BODY_ENGINE_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        procs.append(subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"], cwd=str(COMMERCE_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        procs.append(subprocess.Popen(["cmd", "/c", "npx vite preview --host 127.0.0.1 --port 4173 --strictPort"], cwd=str(FRONTEND_DIR), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))

        h_be = wait_health("http://127.0.0.1:8000/health")
        h_cm = wait_health("http://127.0.0.1:8001/health")
        wait_health("http://127.0.0.1:4173/", expect_json=False)
        assert h_be["mongodb"]["database"] == STAGING_BODY_DB
        assert h_cm["database"]["database"] == STAGING_COMM_DB

        # Create/login staging shopper user via Commerce API
        shopper_email = f"m5a.shopper.{uuid.uuid4().hex[:6]}@wearwise.test"
        st_su, _, raw_su = http_req(
            "http://127.0.0.1:8001/api/auth/signup",
            method="POST",
            body={"name": "M5A Staging Shopper", "email": shopper_email, "password": "StagingPass123!"},
        )
        assert st_su in (200, 201), (st_su, raw_su)
        auth_data = json.loads(raw_su)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            def on_console(msg):
                if msg.type == "error":
                    evidence["console_errors"].append(msg.text)

            def on_req_failed(req):
                evidence["network_failures"].append({"url": req.url, "failure": req.failure})

            def on_resp(resp):
                if any(k in resp.url for k in ["/api/products/", "/api/cart", "/api/orders"]):
                    evidence["api_calls"].append({"url": resp.url, "status": resp.status, "method": resp.request.method})

            page.on("console", on_console)
            page.on("requestfailed", on_req_failed)
            page.on("response", on_resp)

            # Inject staging shopper auth into localStorage on origin
            page.goto("http://127.0.0.1:4173/", wait_until="networkidle")
            page.evaluate(
                """(auth) => {
                    localStorage.setItem('ww-auth-token', auth.access_token || auth.token);
                    localStorage.setItem('ww-user', JSON.stringify(auth.user));
                }""",
                auth_data,
            )

            # 1. Product -> Select Size M -> Add to Cart
            url_tryon = f"http://127.0.0.1:4173/try-on?sku={TEST_SKU}&size=M"
            page.goto(url_tryon, wait_until="networkidle")
            page.wait_for_timeout(1500)
            evidence["routes_visited"].append(url_tryon)
            assert "WearWise Acceptance Boxy Tee" in page.locator("body").inner_text()
            page.locator(".add-to-cart-hero-btn").click()
            page.wait_for_timeout(800)

            # 2. Cart -> reload persistence -> quantity update
            url_cart = "http://127.0.0.1:4173/cart"
            page.goto(url_cart, wait_until="networkidle")
            page.wait_for_timeout(800)
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(800)
            evidence["routes_visited"].append(url_cart)
            cart_body = page.locator("body").inner_text()
            assert "WearWise Acceptance Boxy Tee" in cart_body and "Size: M" in cart_body
            # Test quantity increment then decrement
            page.get_by_role("button", name="Increase quantity").click()
            page.wait_for_timeout(600)
            assert "₹4,998" in page.locator("body").inner_text()
            page.get_by_role("button", name="Decrease quantity").click()
            page.wait_for_timeout(600)
            assert "₹2,499" in page.locator("body").inner_text()
            shot_cart = OUT_DIR / "m5a_cart.png"
            page.screenshot(path=str(shot_cart))
            evidence["screenshots"]["cart"] = str(shot_cart)

            # 3. Checkout -> validation error on empty -> valid demo submit
            url_checkout = "http://127.0.0.1:4173/checkout"
            page.goto(url_checkout, wait_until="networkidle")
            page.wait_for_timeout(800)
            evidence["routes_visited"].append(url_checkout)
            demo_notice = page.get_by_test_id("demo-payment-notice").inner_text()
            assert "No real payment gateway" in demo_notice
            evidence["demo_payment_notice"] = demo_notice

            # Trigger validation error before filling
            page.locator("button.place-order").click()
            page.wait_for_timeout(300)
            # Fill required fields
            for name, val in [
                ("firstName", "Riya"),
                ("lastName", "Verma"),
                ("email", shopper_email),
                ("phone", "9876543210"),
                ("address", "12 MG Road"),
                ("city", "Bengaluru"),
                ("state", "Karnataka"),
                ("pincode", "560001"),
            ]:
                page.fill(f'input[name="{name}"]', val)
            shot_chk = OUT_DIR / "m5a_checkout.png"
            page.screenshot(path=str(shot_chk))
            evidence["screenshots"]["checkout"] = str(shot_chk)

            page.locator("button.place-order").click()
            page.wait_for_url("**/order-confirmation**", timeout=15000)
            page.wait_for_timeout(1000)
            evidence["routes_visited"].append(page.url)

            # 4. Order Confirmation -> reload safety
            confirm_txt = page.locator("body").inner_text()
            assert "DEMO ORDER RECORDED" in confirm_txt
            assert "DEMO_NO_PAYMENT_CAPTURED" in confirm_txt
            assert "WearWise Acceptance Boxy Tee" in confirm_txt
            assert "Size M" in confirm_txt
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(800)
            assert "WearWise Acceptance Boxy Tee" in page.locator("body").inner_text()
            shot_conf = OUT_DIR / "m5a_confirmation.png"
            page.screenshot(path=str(shot_conf))
            evidence["screenshots"]["confirmation"] = str(shot_conf)

            # Extract order ID from URL
            order_id = page.url.split("orderId=")[-1].split("&")[0]
            evidence["order_id"] = order_id

            # 5. Order History (/orders)
            url_orders = "http://127.0.0.1:4173/orders"
            page.goto(url_orders, wait_until="networkidle")
            page.wait_for_timeout(1200)
            evidence["routes_visited"].append(url_orders)
            orders_txt = page.locator("body").inner_text()
            assert order_id in orders_txt
            assert "WearWise Acceptance Boxy Tee" in orders_txt
            assert TEST_SKU in orders_txt
            shot_ord = OUT_DIR / "m5a_order_history.png"
            page.screenshot(path=str(shot_ord))
            evidence["screenshots"]["order_history"] = str(shot_ord)

            browser.close()

        # Verify order record persisted in staging MongoDB
        mc = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        ord_doc = mc[STAGING_COMM_DB]["orders"].find_one({"id": evidence["order_id"]}, {"_id": 0})
        assert ord_doc is not None
        assert ord_doc["is_demo_checkout"] is True
        assert ord_doc["payment_status"] == "DEMO_NO_PAYMENT_CAPTURED"
        evidence["final_order_record"] = ord_doc

        # Verify protected Rev3 assets intact
        for sz, (fpath, exp_sha) in REV3_EXPECTED.items():
            assert sha256_bytes(fpath.read_bytes()) == exp_sha

        out_json = OUT_DIR / "m5a_browser_evidence.json"
        out_json.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print("M5A_JOURNEY_PASSED:", out_json)
    finally:
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
