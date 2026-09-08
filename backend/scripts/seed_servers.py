"""Seed the lab's servers. Edit SERVERS to match the real hardware, then
run once (`python scripts/seed_servers.py`) - safe to re-run, existing
servers (matched by name) are left untouched.
"""

from app.database import SessionLocal
from app.models import Server

SERVERS = [
    {"name": "gpu-1", "hostname": "gpu-1.lab.local", "gpu_type": "RTX 4090", "gpu_count": 2, "vram_gb": 24, "cpu_cores": 32, "ram_gb": 128, "disk_gb": 2000},
    {"name": "gpu-2", "hostname": "gpu-2.lab.local", "gpu_type": "RTX 4090", "gpu_count": 2, "vram_gb": 24, "cpu_cores": 32, "ram_gb": 128, "disk_gb": 2000},
    {"name": "gpu-3", "hostname": "gpu-3.lab.local", "gpu_type": "A100", "gpu_count": 1, "vram_gb": 80, "cpu_cores": 64, "ram_gb": 256, "disk_gb": 4000},
    {"name": "gpu-4", "hostname": "gpu-4.lab.local", "gpu_type": "A100", "gpu_count": 1, "vram_gb": 80, "cpu_cores": 64, "ram_gb": 256, "disk_gb": 4000},
    {"name": "gpu-5", "hostname": "gpu-5.lab.local", "gpu_type": "RTX 3090", "gpu_count": 4, "vram_gb": 24, "cpu_cores": 48, "ram_gb": 256, "disk_gb": 4000},
    {"name": "gpu-6", "hostname": "gpu-6.lab.local", "gpu_type": "RTX 3090", "gpu_count": 4, "vram_gb": 24, "cpu_cores": 48, "ram_gb": 256, "disk_gb": 4000},
]

if __name__ == "__main__":
    db = SessionLocal()
    try:
        added = 0
        for spec in SERVERS:
            if not db.query(Server).filter(Server.name == spec["name"]).first():
                db.add(Server(**spec))
                added += 1
        db.commit()
        print(f"Added {added} new server(s); {len(SERVERS) - added} already existed.")
    finally:
        db.close()
