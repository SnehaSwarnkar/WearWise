import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(r"c:\Users\Lenovo\Documents\Major Project\WearWise")
FRONTEND_DIR = REPO / "frontend"
DIR_7 = REPO / "artifacts" / "phase10_experimental" / "phase10_7"
DIR_7.mkdir(parents=True, exist_ok=True)


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--fabric", required=True, choices=["waffle_knit_240", "rigid_poplin_140"])
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()

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
            page.goto("http://127.0.0.1:4173/experimental-phase10", wait_until="networkidle")
            page.wait_for_timeout(1000)

            page.get_by_test_id(f"fabric-btn-{args.fabric}").click()
            samples = []
            poses = ["P0", "P1", "P3", "P6", "P8", "P11", "P0"]
            t_start = time.time()
            idx = 0
            while time.time() - t_start < args.seconds:
                pid = poses[idx % len(poses)]
                page.get_by_test_id(f"pose-btn-{pid}").click()
                page.wait_for_timeout(1500)
                raw = page.get_by_test_id("phase10-telemetry").get_attribute("data-metrics")
                if raw:
                    m = json.loads(raw)
                    samples.append({"t_sec": round(time.time() - t_start, 2), "pose": pid, **m})
                idx += 1

            browser.close()

        fps_vals = [s["fps"] for s in samples]
        solve_vals = [s["lastSolveMs"] for s in samples]
        col_vals = [s["collisionTimeMs"] for s in samples]
        p95_vals = [s["p95FrameMs"] for s in samples]
        heap_vals = [s["heapMB"] for s in samples if s.get("heapMB") is not None]

        summary = {
            "fabric": args.fabric,
            "duration_sec": round(time.time() - t_start, 2),
            "sample_count": len(samples),
            "avg_fps": round(sum(fps_vals) / max(1, len(fps_vals)), 2),
            "min_fps": min(fps_vals) if fps_vals else 0,
            "avg_solve_ms": round(sum(solve_vals) / max(1, len(solve_vals)), 2),
            "max_solve_ms": max(solve_vals) if solve_vals else 0,
            "avg_collision_ms": round(sum(col_vals) / max(1, len(col_vals)), 2),
            "p95_frame_ms_mean": round(sum(p95_vals) / max(1, len(p95_vals)), 2),
            "heap_start_mb": heap_vals[0] if heap_vals else None,
            "heap_end_mb": heap_vals[-1] if heap_vals else None,
            "heap_growth_mb": round(heap_vals[-1] - heap_vals[0], 2) if len(heap_vals) >= 2 else None,
            "samples": samples,
        }
        out_path = DIR_7 / f"sustained_{args.fabric}.json"
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("SUSTAINED_OK:", out_path)
    finally:
        p_fe.terminate()
        subprocess.run(["cmd", "/c", "taskkill /F /IM node.exe /FI \"WINDOWTITLE eq vite*\" >nul 2>&1"], check=False)


if __name__ == "__main__":
    main()
