import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..utils import as_aware

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _user_stats(db: Session, user_id: int) -> schemas.UserAnalyticsOut:
    reservations = db.query(models.Reservation).filter(models.Reservation.user_id == user_id).all()

    reserved_hours = 0.0
    idle_flag_count = 0
    for r in reservations:
        end = (
            as_aware(r.released_at)
            if r.released_at
            else min(as_aware(r.end_time), datetime.now(timezone.utc))
        )
        reserved_hours += max((end - as_aware(r.start_time)).total_seconds(), 0) / 3600
        if r.idle_flagged:
            idle_flag_count += 1

    # Approximate used_hours by counting usage samples, during each
    # reservation window, where one of the holder's OS accounts was active.
    # Each sample is treated as representing one agent poll interval.
    sample_hours = settings.agent_poll_interval_minutes / 60
    used_hours = 0.0
    for r in reservations:
        holder_usernames = {
            row[0]
            for row in db.query(models.OsUsername.os_username)
            .filter(
                models.OsUsername.user_id == user_id, models.OsUsername.server_id == r.server_id
            )
            .all()
        }
        if not holder_usernames:
            continue
        samples = (
            db.query(models.UsageSample)
            .filter(
                models.UsageSample.server_id == r.server_id,
                models.UsageSample.timestamp >= r.start_time,
                models.UsageSample.timestamp <= r.end_time,
            )
            .all()
        )
        for s in samples:
            active = {p.get("os_username") for p in (s.active_processes or [])}
            if active & holder_usernames:
                used_hours += sample_hours

    return schemas.UserAnalyticsOut(
        user_id=user_id,
        reserved_hours=round(reserved_hours, 2),
        used_hours=round(used_hours, 2),
        utilization_ratio=round(used_hours / reserved_hours, 2) if reserved_hours else None,
        reservation_count=len(reservations),
        idle_flag_count=idle_flag_count,
    )


@router.get("/users/{user_id}", response_model=schemas.UserAnalyticsOut)
def user_analytics(user_id: int, db: Session = Depends(get_db)):
    return _user_stats(db, user_id)


@router.get("/export")
def export_csv(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "user_id",
            "name",
            "reserved_hours",
            "used_hours",
            "utilization_ratio",
            "reservation_count",
            "idle_flag_count",
        ]
    )
    for user in users:
        stats = _user_stats(db, user.id)
        writer.writerow(
            [
                user.id,
                user.name,
                stats.reserved_hours,
                stats.used_hours,
                stats.utilization_ratio,
                stats.reservation_count,
                stats.idle_flag_count,
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=usage_analytics.csv"},
    )
