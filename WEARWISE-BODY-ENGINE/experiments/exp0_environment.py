"""
Experiment 0: System and Dependency Inventory
WearWise Phase 0 Feasibility Study
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=15)
        return res.stdout.strip() if res.returncode == 0 else f"ERROR ({res.returncode}): {res.stderr.strip()}"
    except Exception as e:
        return f"FAILED: {str(e)}"

def get_inventory():
    data = {}
    
    # 1. OS & Architecture
    data["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
    }
    
    # 2. Python Environment
    data["python"] = {
        "version": sys.version,
        "executable": sys.executable,
        "prefix": sys.prefix,
        "is_venv": sys.prefix != sys.base_prefix,
    }
    
    # 3. CPU Info (via powershell or wmic)
    cpu_info = run_cmd("powershell -Command \"Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json\"")
    try:
        data["cpu"] = json.loads(cpu_info)
    except:
        data["cpu"] = cpu_info
        
    # 4. RAM & Disk
    mem_info = run_cmd("powershell -Command \"[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB, 2)\"")
    disk_info = run_cmd("powershell -Command \"Get-PSDrive C | Select-Object @{N='Free_GB';E={[math]::Round($_.Free/1GB,2)}}, @{N='Used_GB';E={[math]::Round($_.Used/1GB,2)}} | ConvertTo-Json\"")
    data["memory_ram_gb"] = mem_info
    try:
        data["disk_c"] = json.loads(disk_info)
    except:
        data["disk_c"] = disk_info
        
    # 5. GPU & NVIDIA Driver
    gpu_info = run_cmd("nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader")
    data["gpu_nvidia_smi"] = gpu_info
    
    # 6. CUDA Toolkit
    nvcc_info = run_cmd("nvcc --version")
    data["cuda_toolkit_nvcc"] = nvcc_info
    
    # 7. PyTorch & CUDA status
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else None
        vram_mb = torch.cuda.get_device_properties(0).total_memory / (1024**2) if cuda_avail else None
        
        # Test real GPU tensor calculation if cuda is available
        tensor_test = "SKIPPED"
        if cuda_avail:
            try:
                x = torch.randn(200, 200, device="cuda")
                y = x @ x.T
                tensor_test = f"SUCCESS: Matrix mul (200x200) computed on {y.device}"
            except Exception as e:
                tensor_test = f"FAILED: {str(e)}"
                
        data["pytorch"] = {
            "version": torch.__version__,
            "cuda_build": torch.version.cuda,
            "cuda_available": cuda_avail,
            "gpu_name": gpu_name,
            "gpu_vram_mb": vram_mb,
            "tensor_computation_test": tensor_test,
        }
    except ImportError:
        data["pytorch"] = "NOT INSTALLED"
        
    # 8. Rust & Toolchain
    data["rust"] = {
        "rustc": run_cmd("rustc --version"),
        "cargo": run_cmd("cargo --version"),
        "targets": run_cmd("rustup target list --installed"),
        "wasm_pack": run_cmd("wasm-pack --version"),
    }
    
    # 9. Node.js & npm
    data["node"] = {
        "node": run_cmd("node --version"),
        "npm": run_cmd("npm --version"),
    }
    
    # 10. Pip list / freeze
    pip_freeze = run_cmd(f"\"{sys.executable}\" -m pip freeze")
    data["pip_freeze"] = pip_freeze.splitlines()
    
    return data

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "exp0_environment.json"
    
    inv = get_inventory()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2)
    print(f"Environment inventory written to {out_file}")
