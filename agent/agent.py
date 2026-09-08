"""Canvas Lab monitoring agent.

A plain background daemon (not an AI/LLM agent) that runs on each lab
server. Every POLL_INTERVAL_SECONDS it collects GPU/CPU/RAM utilization
and which OS user owns each active GPU process, then POSTs a snapshot to
the central backend's /api/usage endpoint. That per-process ownership is
what lets the backend tell "the reservation holder is using this" apart
from "someone else started using it".

Run one copy per server, with SERVER_NAME set to that server's `name` in
the backend's Server table (see backend/scripts/seed_servers.py).
"""

import os
import socket
import time
from typing import Any, Optional

import psutil
import requests

try:
    import pynvml

    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
AGENT_API_KEY = os.environ.get("AGENT_API_KEY", "change-me")
SERVER_NAME = os.environ.get("SERVER_NAME", socket.gethostname())
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "900"))  # 15 min default


def _process_owner(pid: int) -> Optional[str]:
    try:
        return psutil.Process(pid).username()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_gpu_stats() -> tuple[Optional[float], Optional[float], list[dict[str, Any]]]:
    """Returns (avg_util_percent, total_mem_used_gb, active_processes)."""
    if not HAS_NVML:
        return None, None, []

    device_count = pynvml.nvmlDeviceGetCount()
    utils: list[float] = []
    mem_used_gb = 0.0
    processes: list[dict[str, Any]] = []

    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)

        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        utils.append(util.gpu)

        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        mem_used_gb += mem.used / (1024**3)

        try:
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        except pynvml.NVMLError:
            procs = []

        for proc in procs:
            owner = _process_owner(proc.pid)
            if owner is None:
                continue
            try:
                name = psutil.Process(proc.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                name = "unknown"
            processes.append({"os_username": owner, "process": name, "pid": proc.pid})

    avg_util = sum(utils) / len(utils) if utils else None
    return avg_util, mem_used_gb, processes


def get_cpu_ram_stats() -> tuple[float, float]:
    cpu_percent = psutil.cpu_percent(interval=1)
    ram_used_gb = psutil.virtual_memory().used / (1024**3)
    return cpu_percent, ram_used_gb


def collect_sample() -> dict[str, Any]:
    gpu_util, gpu_mem_gb, gpu_processes = get_gpu_stats()
    cpu_util, ram_used_gb = get_cpu_ram_stats()

    return {
        "server_name": SERVER_NAME,
        "gpu_util_percent": gpu_util,
        "gpu_mem_used_gb": gpu_mem_gb,
        "cpu_util_percent": cpu_util,
        "ram_used_gb": ram_used_gb,
        "active_processes": gpu_processes,
    }


def report(sample: dict[str, Any]) -> None:
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/usage",
            json=sample,
            headers={"X-Agent-Key": AGENT_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[agent] failed to report usage: {exc}")


def main() -> None:
    print(
        f"[agent] starting for server '{SERVER_NAME}', reporting to {BACKEND_URL} "
        f"every {POLL_INTERVAL_SECONDS}s (nvml {'available' if HAS_NVML else 'unavailable'})"
    )
    while True:
        report(collect_sample())
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
