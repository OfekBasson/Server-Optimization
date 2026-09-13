"""Seed the lab's servers with the real mass-01..06 hardware.

Safe to re-run - existing servers (matched by name) are left untouched, so
edit SERVERS and re-run to add new ones without duplicating existing rows.

cpu_cores / ram_gb / disk_gb aren't set below (not provided) - fill them
in later via `POST /api/servers` or directly in the DB if useful for
matching watch requests on CPU/RAM as well as GPU.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Server

SSH_HOST = "mass.ohadf.com"

SERVERS = [
    {
        "name": "mass-01",
        "pi": "Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1203,
        "gpu_type": "RTX 3090",
        "gpu_count": 4,
        "vram_gb": 24,
    },
    {
        "name": "mass-02",
        "pi": "Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1110,
        "gpu_type": "Quadro RTX 5000 + TITAN V",
        "gpu_count": 2,
        # Mixed GPUs (16GB + 12GB) - set to the lower of the two so VRAM-based
        # watch-request matching doesn't over-promise what's actually free.
        "vram_gb": 12,
        "notes": "Mixed GPUs: 1x Quadro RTX 5000 (16GB) + 1x TITAN V (12GB).",
    },
    {
        "name": "mass-03",
        "pi": "Arik & Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1206,
        "gpu_type": "RTX 3090",
        "gpu_count": 4,
        "vram_gb": 24,
    },
    {
        "name": "mass-04",
        "pi": "Arik & Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1205,
        "gpu_type": "RTX 3090",
        "gpu_count": 4,
        "vram_gb": 24,
    },
    {
        "name": "mass-05",
        "pi": "Arik & Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1204,
        "gpu_type": "RTX 6000 Ada",
        "gpu_count": 2,
        "vram_gb": 48,
    },
    {
        "name": "mass-06",
        "pi": "Arik & Ohad",
        "hostname": SSH_HOST,
        "ssh_port": 1214,
        "gpu_type": "RTX PRO 6000 Blackwell Max-Q",
        "gpu_count": 1,
        "vram_gb": 96,
        "notes": "VRAM (96GB) is from public specs for this very new card - please verify against the actual hardware.",
    },
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
