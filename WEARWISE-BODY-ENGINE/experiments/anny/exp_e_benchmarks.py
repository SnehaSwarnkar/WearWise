"""
Experiment E: Hardware & Performance Benchmarks (Anny CPU & GPU)
WearWise Phase 0 Feasibility Study
"""

import json
import os
import sys
import time
import statistics
from pathlib import Path

def run_benchmarks():
    import psutil
    import torch
    import trimesh
    
    process = psutil.Process()
    ram_initial_mb = process.memory_info().rss / (1024 * 1024)
    
    has_cuda = torch.cuda.is_available()
    devices_to_test = ["cpu"]
    if has_cuda:
        devices_to_test.append("cuda")
        
    benchmark_results = {
        "candidate": "Anny",
        "system_ram_initial_mb": ram_initial_mb,
        "cuda_available": has_cuda,
        "gpu_name": torch.cuda.get_device_name(0) if has_cuda else "N/A",
        "devices": {},
    }
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    benchmarks_dir = base_dir / "benchmarks"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    temp_glb = benchmarks_dir / "temp_benchmark.glb"
    
    import anny
    
    for dev in devices_to_test:
        print(f"\n================ Running Benchmarks on {dev.upper()} ================")
        dev_res = {}
        
        if dev == "cuda":
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.empty_cache()
            
        ram_before_init = process.memory_info().rss / (1024 * 1024)
        
        # 1. Model Initialization Timing
        t0 = time.perf_counter()
        model = anny.Anny(local_changes="default", skinning_method="lbs").to(device=dev, dtype=torch.float32)
        init_time = time.perf_counter() - t0
        
        ram_after_init = process.memory_info().rss / (1024 * 1024)
        peak_vram_init = (torch.cuda.max_memory_allocated() / (1024 * 1024)) if dev == "cuda" else 0.0
        
        dev_res["model_init"] = {
            "time_seconds": init_time,
            "ram_increase_mb": ram_after_init - ram_before_init,
            "peak_vram_mb": peak_vram_init,
        }
        print(f"Init: {init_time:.4f} s | RAM: +{ram_after_init - ram_before_init:.1f} MB | VRAM: {peak_vram_init:.1f} MB")
        
        pose_params = torch.eye(4, device=dev, dtype=torch.float32)[None, None].repeat(1, model.bone_count, 1, 1)
        pheno_labels = list(model.phenotype_labels)
        base_pheno = {k: 0.5 for k in pheno_labels}
        base_pheno.update({"gender": 1.0, "height": 0.5, "weight": 0.5})
        
        # Helper single inference
        def single_inference(pheno, local):
            if dev == "cuda":
                torch.cuda.synchronize()
            t_start = time.perf_counter()
            with torch.no_grad():
                out = model(pose_parameters=pose_params, phenotype_kwargs=pheno, local_changes_kwargs=local)
                if "vertices" in out:
                    v = out["vertices"]
                elif "rest_vertices" in out:
                    v = out["rest_vertices"]
                v = out.get("vertices", out.get("rest_vertices"))
            if dev == "cuda":
                torch.cuda.synchronize()
            t_end = time.perf_counter()
            return v, (t_end - t_start)
            
        # 2. First (Cold) Inference
        v_cold, cold_time = single_inference(base_pheno, {})
        v_cold_np = v_cold[0].detach().cpu().numpy() if v_cold.dim() == 3 else v_cold.detach().cpu().numpy()
        faces_np = model.faces.detach().cpu().numpy() if hasattr(model, "faces") else model.get_faces().cpu().numpy()
        
        dev_res["first_inference"] = {
            "time_seconds": cold_time,
            "peak_vram_mb": (torch.cuda.max_memory_allocated() / (1024 * 1024)) if dev == "cuda" else 0.0,
        }
        print(f"First inference (cold): {cold_time * 1000:.2f} ms")
        
        # 3. 50 Warm Inferences (Repeated Workload)
        warm_times = []
        for i in range(50):
            # Vary height slightly to simulate user slider movement
            p = dict(base_pheno)
            p["height"] = 0.3 + (i % 5) * 0.1
            _, t_inf = single_inference(p, {})
            warm_times.append(t_inf * 1000)  # in ms
            
        dev_res["warm_50_inferences_ms"] = {
            "mean": statistics.mean(warm_times),
            "median_p50": statistics.median(warm_times),
            "p95": sorted(warm_times)[int(len(warm_times) * 0.95)],
            "min": min(warm_times),
            "max": max(warm_times),
            "std": statistics.stdev(warm_times),
        }
        print(f"50 Warm inferences: mean={dev_res['warm_50_inferences_ms']['mean']:.2f} ms | p50={dev_res['warm_50_inferences_ms']['median_p50']:.2f} ms | p95={dev_res['warm_50_inferences_ms']['p95']:.2f} ms")
        
        # 4. GLB Export Benchmark
        export_mesh = trimesh.Trimesh(vertices=v_cold_np, faces=faces_np, process=False)
        t_exp_0 = time.perf_counter()
        export_mesh.export(str(temp_glb), file_type="glb")
        export_time = time.perf_counter() - t_exp_0
        glb_size = os.path.getsize(temp_glb)
        if temp_glb.exists():
            temp_glb.unlink()
            
        dev_res["glb_export"] = {
            "export_time_seconds": export_time,
            "glb_size_bytes": glb_size,
            "glb_size_kb": glb_size / 1024.0,
        }
        print(f"GLB export: {export_time * 1000:.2f} ms | File size: {glb_size / 1024.0:.1f} KB")
        
        # 5. Stability & Memory Leak Test (100 Sequential Inferences)
        ram_before_100 = process.memory_info().rss / (1024 * 1024)
        crashes = 0
        t_seq_0 = time.perf_counter()
        for i in range(100):
            try:
                p = dict(base_pheno)
                p["weight"] = 0.2 + (i % 7) * 0.1
                single_inference(p, {})
            except Exception as e:
                crashes += 1
        t_seq = time.perf_counter() - t_seq_0
        ram_after_100 = process.memory_info().rss / (1024 * 1024)
        
        dev_res["stability_100_runs"] = {
            "total_time_seconds": t_seq,
            "crashes": crashes,
            "stable": bool(crashes == 0),
            "ram_delta_mb": ram_after_100 - ram_before_100,
            "peak_vram_mb": (torch.cuda.max_memory_allocated() / (1024 * 1024)) if dev == "cuda" else 0.0,
        }
        print(f"100 Sequential runs: {t_seq:.2f} s | Crashes: {crashes} | RAM delta: {ram_after_100 - ram_before_100:+.2f} MB")
        
        benchmark_results["devices"][dev] = dev_res
        
    out_file = benchmarks_dir / "anny_benchmarks.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"\nBenchmarks written to {out_file}")

if __name__ == "__main__":
    run_benchmarks()
