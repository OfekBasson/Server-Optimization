from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db

router = APIRouter(prefix="/api", tags=["usage"])


def verify_agent_key(x_agent_key: str = Header(...)):
    if x_agent_key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Invalid agent key")


@router.post("/usage", response_model=schemas.UsageSampleOut)
def post_usage_sample(
    payload: schemas.UsageSampleIn,
    db: Session = Depends(get_db),
    _=Depends(verify_agent_key),
):
    server = db.query(models.Server).filter(models.Server.name == payload.server_name).first()
    if not server:
        raise HTTPException(status_code=404, detail=f"Unknown server '{payload.server_name}'")

    sample = models.UsageSample(
        server_id=server.id,
        gpu_util_percent=payload.gpu_util_percent,
        gpu_mem_used_gb=payload.gpu_mem_used_gb,
        cpu_util_percent=payload.cpu_util_percent,
        ram_used_gb=payload.ram_used_gb,
        active_processes=[p.model_dump() for p in payload.active_processes],
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


@router.get("/servers/{server_id}/usage", response_model=list[schemas.UsageSampleOut])
def get_usage_history(server_id: int, limit: int = 200, db: Session = Depends(get_db)):
    return (
        db.query(models.UsageSample)
        .filter(models.UsageSample.server_id == server_id)
        .order_by(models.UsageSample.timestamp.desc())
        .limit(limit)
        .all()
    )
