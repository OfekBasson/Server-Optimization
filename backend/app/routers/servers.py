from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/servers", tags=["servers"])


@router.get("", response_model=list[schemas.ServerStatusOut])
def list_servers(db: Session = Depends(get_db)):
    servers = db.query(models.Server).all()
    out = []
    for server in servers:
        current = (
            db.query(models.Reservation)
            .filter(
                models.Reservation.server_id == server.id,
                models.Reservation.status == models.ReservationStatus.active,
                models.Reservation.start_time <= datetime.now(timezone.utc),
            )
            .order_by(models.Reservation.start_time)
            .first()
        )
        status_out = schemas.ServerStatusOut.model_validate(server)
        if current:
            status_out.current_reservation = schemas.ReservationOut.model_validate(current)
            status_out.is_idle_flagged = current.idle_flagged
        out.append(status_out)
    return out


@router.post("", response_model=schemas.ServerOut)
def create_server(payload: schemas.ServerCreate, db: Session = Depends(get_db)):
    server = models.Server(**payload.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.get("/{server_id}", response_model=schemas.ServerOut)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.get(models.Server, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.get("/{server_id}/calendar", response_model=list[schemas.ReservationOut])
def server_calendar(
    server_id: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Reservation).filter(models.Reservation.server_id == server_id)
    if start:
        query = query.filter(models.Reservation.end_time >= start)
    if end:
        query = query.filter(models.Reservation.start_time <= end)
    return query.order_by(models.Reservation.start_time).all()
