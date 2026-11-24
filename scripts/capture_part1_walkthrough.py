"""
WearWise — Part 1: Seller Digital Garment Platform
Automated Browser Walkthrough & Visual Stage Capture
===================================================
Drives Chromium via Playwright to interactively capture all 6 studio stages:
1. Product Commercial Identity & SKU Registration
2. Multi-View Photography & Image Role Assignment
3. 2D Pattern Specification & Construction Methods (Method A, B, C)
4. Finished Garment Measurements Table (S, M, L) & Grading
5. Fabric Mechanical Properties & 8 Provisional Presets
6. 13-Stage Generation, Static Mannequin Presentation & Automated QA Audit
"""

import os
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "artifacts", "demonstration"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_walkthrough():
    print("=== Launching Playwright Chromium Walkthrough ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        # Navigate to Merchant Garment Studio
        url = "http://localhost:3000/merchant-studio"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Stage 1: Identity
        print("Capturing Stage 1: Product Identity...")
        s1_path = os.path.join(OUTPUT_DIR, "part1_stage1_identity.png")
        page.screenshot(path=s1_path, full_page=True)

        # Move to Stage 2: Images
        print("Switching to Stage 2: Dual-Role Images...")
        page.click("button.step-nav-pill:nth-child(2)")
        page.wait_for_timeout(1000)
        s2_path = os.path.join(OUTPUT_DIR, "part1_stage2_imagery.png")
        page.screenshot(path=s2_path, full_page=True)

        # Move to Stage 3: Pattern
        print("Switching to Stage 3: Pattern Specification...")
        page.click("button.step-nav-pill:nth-child(3)")
        page.wait_for_timeout(1000)
        s3_path = os.path.join(OUTPUT_DIR, "part1_stage3_pattern.png")
        page.screenshot(path=s3_path, full_page=True)

        # Move to Stage 4: Measurements
        print("Switching to Stage 4: Finished Measurements...")
        page.click("button.step-nav-pill:nth-child(4)")
        page.wait_for_timeout(1000)
        s4_path = os.path.join(OUTPUT_DIR, "part1_stage4_measurements.png")
        page.screenshot(path=s4_path, full_page=True)

        # Move to Stage 5: Fabric Properties & Presets
        print("Switching to Stage 5: Fabric Properties...")
        page.click("button.step-nav-pill:nth-child(5)")
        page.wait_for_timeout(1000)
        s5_path = os.path.join(OUTPUT_DIR, "part1_stage5_fabrics.png")
        page.screenshot(path=s5_path, full_page=True)

        # Move to Stage 6: 3D Preview & QA
        print("Switching to Stage 6: 3D Preview, Motion & QA Audit...")
        page.click("button.step-nav-pill:nth-child(6)")
        page.wait_for_timeout(4000) # Allow Three.js canvas to mount and render
        s6_path = os.path.join(OUTPUT_DIR, "part1_stage6_preview_qa.png")
        page.screenshot(path=s6_path, full_page=True)

        # Open Manifest Modal
        print("Opening Package Manifest Modal...")
        try:
            page.click("button:has-text('VIEW DIGITAL GARMENT PACKAGE MANIFEST')")
            page.wait_for_timeout(1000)
            manifest_path = os.path.join(OUTPUT_DIR, "part1_stage6_manifest_modal.png")
            page.screenshot(path=manifest_path, full_page=False)
            print(f"Captured Manifest modal: {manifest_path}")
        except Exception as e:
            print(f"Could not open manifest modal: {e}")

        browser.close()
        print("=== Visual Walkthrough Capture Complete ===")
        print(f"Artifacts saved in {OUTPUT_DIR}")

if __name__ == "__main__":
    capture_walkthrough()
