from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.post("", response_model=schemas.ReservationOut)
def create_reservation(payload: schemas.ReservationCreate, db: Session = Depends(get_db)):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    overlap = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.server_id == payload.server_id,
            models.Reservation.status == models.ReservationStatus.active,
            models.Reservation.start_time < payload.end_time,
            models.Reservation.end_time > payload.start_time,
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=409, detail="Server is already booked for part of this time range"
        )

    reservation = models.Reservation(**payload.model_dump())
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("", response_model=list[schemas.ReservationOut])
def list_reservations(
    server_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Reservation)
    if server_id is not None:
        query = query.filter(models.Reservation.server_id == server_id)
    if user_id is not None:
        query = query.filter(models.Reservation.user_id == user_id)
    return query.order_by(models.Reservation.start_time.desc()).all()


@router.post("/{reservation_id}/release", response_model=schemas.ReservationOut)
def release_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(models.Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status != models.ReservationStatus.active:
        raise HTTPException(status_code=400, detail="Reservation is not active")

    reservation.status = models.ReservationStatus.released
    reservation.released_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reservation)
    return reservation
