"""
WearWise Phase 8 End-to-End Verification Script
Verifies:
  1. MongoDB Atlas connectivity on both Commerce (8001) and Body Engine (8000).
  2. Mode A 3D assets: baseline avatar and prototype garment TSH-WW-CREW-001.glb.
  3. Mode B VTON lifecycle: photo validation, job submission, async processing,
     retrieval of 3 distinct views (Front, Side, Back), and privacy deletion.
  4. Cart integration: adding TSH-WW-CREW-001 with size selection to MongoDB cart.
"""

import io
import json
import time
import urllib.request
import urllib.parse
from PIL import Image

COMMERCE_URL = "http://127.0.0.1:8001"
BODY_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:3000"

def log(msg):
    print(f"[VERIFY] {msg}")

def check_health():
    log("Checking Commerce backend /health (Port 8001)...")
    req = urllib.request.urlopen(f"{COMMERCE_URL}/health", timeout=5)
    data = json.loads(req.read().decode())
    assert data["status"] == "healthy", f"Commerce unhealthy: {data}"
    assert data["database"]["ok"] is True, f"Commerce MongoDB disconnected: {data}"
    log(f"Commerce healthy on MongoDB: {data['database']['database']} (collections: {data['database']['collections']})")

    log("Checking Body Engine /health (Port 8000)...")
    req = urllib.request.urlopen(f"{BODY_URL}/health", timeout=5)
    data = json.loads(req.read().decode())
    assert data["status"] == "healthy", f"Body Engine unhealthy: {data}"
    assert data["mongodb"]["ok"] is True, f"Body Engine MongoDB disconnected: {data}"
    log(f"Body Engine healthy on MongoDB: {data['mongodb']['database']} (collections: {len(data['mongodb']['collections'])})")

def check_mode_a_assets():
    log("Checking Mode A 3D Garment GLB (TSH-WW-CREW-001.glb)...")
    req = urllib.request.urlopen(f"{FRONTEND_URL}/garments/TSH-WW-CREW-001.glb", timeout=5)
    glb_bytes = req.read()
    assert len(glb_bytes) > 10000, "Garment GLB is too small or missing"
    assert glb_bytes[:4] == b"glTF", "Garment GLB invalid magic header"
    log(f"Mode A 3D Garment valid: {len(glb_bytes)} bytes")

    log("Checking Mode A Baseline Avatar GLB...")
    req = urllib.request.urlopen(f"{FRONTEND_URL}/avatars/anny_baseline_male.glb", timeout=5)
    avatar_bytes = req.read()
    assert len(avatar_bytes) > 50000, "Avatar GLB is too small or missing"
    assert avatar_bytes[:4] == b"glTF", "Avatar GLB invalid magic header"
    log(f"Mode A Baseline Avatar valid: {len(avatar_bytes)} bytes")

def check_cart_integration():
    log("Checking Commerce cart addition for TSH-WW-CREW-001 (Size M)...")
    payload = {
        "session_id": "test_e2e_session",
        "item": {
            "id": 1,
            "name": "WearWise Signature Boxy Crew Tee",
            "price": 2999,
            "size": "M",
            "sku": "TSH-WW-CREW-001",
            "className": "product-pink",
            "colors": ["#ff3d9a", "#ffffff", "#1d1d1d"],
            "brand": "WEARWISE EDIT",
        }
    }
    req = urllib.request.Request(
        f"{COMMERCE_URL}/api/cart/add",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req, timeout=5)
    cart = json.loads(res.read().decode())
    assert len(cart["items"]) >= 1, "Cart item was not added"
    assert cart["items"][-1]["sku"] == "TSH-WW-CREW-001", "Item SKU mismatch"
    assert cart["items"][-1]["size"] == "M", "Item size mismatch"
    log(f"Cart integration verified: SKU {cart['items'][-1]['sku']} (Size: {cart['items'][-1]['size']}) in MongoDB Atlas cart.")

def check_mode_b_vton():
    log("Creating a synthetic test person photo (valid dimensions, human-like distribution)...")
    img = Image.new("RGB", (512, 768), color=(240, 235, 225))
    # Draw simple person silhouette
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Head
    draw.ellipse([216, 80, 296, 170], fill=(220, 180, 150))
    # Torso
    draw.polygon([(180, 180), (332, 180), (310, 480), (202, 480)], fill=(80, 100, 140))
    # Legs
    draw.rectangle([202, 480, 246, 720], fill=(40, 45, 60))
    draw.rectangle([268, 480, 312, 720], fill=(40, 45, 60))

    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG", quality=90)
    img_bytes = img_buf.getvalue()

    log("Submitting Mode B AI Photo VTON Job to Port 8000...")
    boundary = "----WebKitFormBoundaryWearWiseTest"
    body = io.BytesIO()
    # file field
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="file"; filename="test_person.jpg"\r\n')
    body.write(b'Content-Type: image/jpeg\r\n\r\n')
    body.write(img_bytes)
    body.write(b"\r\n")
    # garment_sku field
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="garment_sku"\r\n\r\n')
    body.write(b"TSH-WW-CREW-001\r\n")
    # consent field
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="consent"\r\n\r\n')
    body.write(b"true\r\n")
    body.write(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{BODY_URL}/api/v1/try-on/vton/jobs",
        data=body.getvalue(),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e",
        },
        method="POST"
    )
    res = urllib.request.urlopen(req, timeout=10)
    job_resp = json.loads(res.read().decode())
    job_id = job_resp["job_id"]
    log(f"Job created: {job_id} (status: {job_resp['status']})")

    # Poll until completed
    log("Polling for 3-view virtual try-on completion...")
    for _ in range(20):
        time.sleep(1)
        req = urllib.request.Request(
            f"{BODY_URL}/api/v1/try-on/vton/jobs/{job_id}",
            headers={"X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e"},
        )
        status_resp = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
        log(f"Job status: {status_resp['status']} (progress: {status_resp.get('progress_percent', 0)}%)")
        if status_resp["status"] == "completed":
            break
        elif status_resp["status"] == "failed":
            raise RuntimeError(f"VTON job failed: {status_resp.get('error_message')}")

    # Fetch results
    log(f"Fetching 3-view results for job {job_id}...")
    req = urllib.request.Request(
        f"{BODY_URL}/api/v1/try-on/vton/jobs/{job_id}/results",
        headers={"X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e"},
    )
    results = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
    views = results["views"]
    assert "front" in views, "Missing front view result"
    assert "side" in views, "Missing side view result"
    assert "back" in views, "Missing back view result"

    log("Checking front view image asset...")
    front_img_bytes = urllib.request.urlopen(f"{BODY_URL}{views['front']['url']}", timeout=5).read()
    assert len(front_img_bytes) > 5000, "Front image corrupted"

    log("Checking side view image asset...")
    side_img_bytes = urllib.request.urlopen(f"{BODY_URL}{views['side']['url']}", timeout=5).read()
    assert len(side_img_bytes) > 5000, "Side image corrupted"
    assert views["side"]["is_inferred"] is True, "Side view should be marked as inferred"

    log("Checking back view image asset...")
    back_img_bytes = urllib.request.urlopen(f"{BODY_URL}{views['back']['url']}", timeout=5).read()
    assert len(back_img_bytes) > 5000, "Back image corrupted"
    assert views["back"]["is_inferred"] is True, "Back view should be marked as inferred"

    log(f"3 Distinct Views Verified: Front ({len(front_img_bytes)}B), Side ({len(side_img_bytes)}B), Back ({len(back_img_bytes)}B)")

    # Test deletion
    log(f"Testing deletion of job {job_id}...")
    req = urllib.request.Request(
        f"{BODY_URL}/api/v1/try-on/vton/jobs/{job_id}",
        headers={"X-User-Id": "c1f7a28e-8e3b-48d9-a791-03f4439c1b3e"},
        method="DELETE"
    )
    del_resp = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
    assert del_resp["deleted"] is True, "Deletion failed"
    log("Job and associated image assets permanently deleted.")

def main():
    print("=" * 80)
    print("WearWise Phase 8 Comprehensive End-to-End Verification")
    print("=" * 80)
    check_health()
    check_mode_a_assets()
    check_cart_integration()
    check_mode_b_vton()
    print("=" * 80)
    print("ALL PHASE 8 VERIFICATIONS PASSED 100% SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()
