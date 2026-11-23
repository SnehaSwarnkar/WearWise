"""
Automated 3D WebGL Viewer Screenshot Capture
Uses Playwright Chromium to open the Three.js 3D avatar inspector,
waits for WebGL models to render, and takes production screenshots.
"""

import os
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture_viewer_screenshots():
    base_dir = Path(__file__).resolve().parent.parent
    img_dir = base_dir / "artifacts" / "phase4a" / "images"
    brain_dir = Path(r"C:\Users\Lenovo\.gemini\antigravity\brain\c57b9fa6-3e23-4fa2-b534-c1f6bc625ad8\phase4a")
    img_dir.mkdir(parents=True, exist_ok=True)
    brain_dir.mkdir(parents=True, exist_ok=True)

    print("Launching Chromium for 3D Viewer screenshot capture...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--enable-webgl", "--use-gl=angle", "--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("Navigating to http://localhost:8088/viewer.html ...")
        page.goto("http://localhost:8088/viewer.html", wait_until="networkidle")

        # Wait for loading overlay to hide (model loaded)
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=15000)
        time.sleep(2.5)  # Allow WebGL frames to settle

        # 1. Capture Combined Custom Avatar
        out_main = img_dir / "screenshot_3d_viewer_combined.png"
        page.screenshot(path=str(out_main))
        shutil.copyfile(out_main, brain_dir / "screenshot_3d_viewer_combined.png")
        shutil.copyfile(out_main, img_dir / "screenshot_3d_viewer.png")
        shutil.copyfile(out_main, brain_dir / "screenshot_3d_viewer.png")
        print(f"Captured: {out_main}")

        # 2. Switch to Neutral Masculine Baseline
        page.select_option("#avatar-select", "neutral_masculine.glb")
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=15000)
        time.sleep(2.0)
        out_neutral = img_dir / "screenshot_3d_viewer_neutral.png"
        page.screenshot(path=str(out_neutral))
        shutil.copyfile(out_neutral, brain_dir / "screenshot_3d_viewer_neutral.png")
        print(f"Captured: {out_neutral}")

        # 3. Switch to Belly Fullness Control
        page.select_option("#avatar-select", "control_belly_fullness.glb")
        page.wait_for_selector("#loading-overlay", state="hidden", timeout=15000)
        time.sleep(2.0)
        out_belly = img_dir / "screenshot_3d_viewer_belly.png"
        page.screenshot(path=str(out_belly))
        shutil.copyfile(out_belly, brain_dir / "screenshot_3d_viewer_belly.png")
        print(f"Captured: {out_belly}")

        # 4. Switch to Wireframe Mode
        page.click("#btn-wireframe")
        time.sleep(1.0)
        out_wire = img_dir / "screenshot_3d_viewer_wireframe.png"
        page.screenshot(path=str(out_wire))
        shutil.copyfile(out_wire, brain_dir / "screenshot_3d_viewer_wireframe.png")
        print(f"Captured: {out_wire}")

        browser.close()
    print("All 3D viewer screenshots captured and saved successfully.")

if __name__ == "__main__":
    capture_viewer_screenshots()
