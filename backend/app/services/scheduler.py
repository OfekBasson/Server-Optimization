"""Background jobs: idle-but-reserved detection (+ takeover alerts, watch
matches) and long-standing reservation check-ins.

No job here ever auto-releases a reservation - they only ever send a
WhatsApp nudge and let the holder decide.
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import (
    NotificationType,
    OsUsername,
    Reservation,
    ReservationStatus,
    UsageSample,
    WatchRequest,
    WatchRequestStatus,
)
from ..utils import as_aware
from .matching import server_matches_request
from .notifications import send_whatsapp

logger = logging.getLogger("scheduler")


def _latest_usage_sample(db: Session, server_id: int) -> UsageSample | None:
    return (
        db.query(UsageSample)
        .filter(UsageSample.server_id == server_id)
        .order_by(UsageSample.timestamp.desc())
        .first()
    )


def _holder_os_usernames(db: Session, user_id: int, server_id: int) -> set[str]:
    rows = (
        db.query(OsUsername.os_username)
        .filter(OsUsername.user_id == user_id, OsUsername.server_id == server_id)
        .all()
    )
    return {row[0] for row in rows}


def _cooldown_ok(last_sent: datetime | None) -> bool:
    if last_sent is None:
        return True
    return datetime.now(timezone.utc) - as_aware(last_sent) >= timedelta(
        hours=settings.nudge_cooldown_hours
    )


def check_idle_reservations() -> None:
    """Flag reserved-but-idle servers, nudge the holder, alert matching
    watch requests, and detect + alert on takeover by someone else."""

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        active_reservations = (
            db.query(Reservation).filter(Reservation.status == ReservationStatus.active).all()
        )

        for reservation in active_reservations:
            sample = _latest_usage_sample(db, reservation.server_id)
            if sample is None:
                continue

            holder_usernames = _holder_os_usernames(
                db, reservation.user_id, reservation.server_id
            )
            active_usernames = {
                p.get("os_username")
                for p in (sample.active_processes or [])
                if p.get("os_username")
            }
            holder_active = bool(holder_usernames & active_usernames)
            other_active = active_usernames - holder_usernames

            is_idle_now = (
                not holder_active
                and (sample.gpu_util_percent or 0) < settings.idle_gpu_util_percent_threshold
            )

            if is_idle_now:
                if reservation.idle_since is None:
                    reservation.idle_since = sample.timestamp
                    db.commit()

                idle_minutes = (now - as_aware(reservation.idle_since)).total_seconds() / 60
                newly_idle = (
                    idle_minutes >= settings.idle_threshold_minutes and not reservation.idle_flagged
                )
                if newly_idle:
                    reservation.idle_flagged = True
                    db.commit()
                    _notify_idle(db, reservation)
                    _notify_watchers(db, reservation)

                if (
                    reservation.idle_flagged
                    and other_active
                    and _cooldown_ok(reservation.last_takeover_alert_at)
                ):
                    _notify_takeover(db, reservation, other_active)
            else:
                if reservation.idle_flagged or reservation.idle_since:
                    reservation.idle_flagged = False
                    reservation.idle_since = None
                    db.commit()
    finally:
        db.close()


def _notify_idle(db: Session, reservation: Reservation) -> None:
    user, server = reservation.user, reservation.server
    message = (
        f"Hi {user.name}, {server.name} looks idle even though you still have it "
        f"reserved. Still need it? Release it on the booking page if you're done."
    )
    send_whatsapp(
        db,
        user_id=user.id,
        whatsapp_number=user.whatsapp_number,
        notification_type=NotificationType.idle_nudge,
        message=message,
        server_id=server.id,
    )
    reservation.last_idle_nudge_at = datetime.now(timezone.utc)
    db.commit()


def _notify_watchers(db: Session, reservation: Reservation) -> None:
    server = reservation.server
    watchers = db.query(WatchRequest).filter(WatchRequest.status == WatchRequestStatus.active).all()
    for watch in watchers:
        if watch.user_id == reservation.user_id:
            continue
        if server_matches_request(server, watch):
            message = (
                f"{server.name} matches what you're looking for and looks free right "
                f"now (it's reserved but currently idle)."
            )
            send_whatsapp(
                db,
                user_id=watch.user_id,
                whatsapp_number=watch.user.whatsapp_number,
                notification_type=NotificationType.watch_match,
                message=message,
                server_id=server.id,
            )


def _notify_takeover(db: Session, reservation: Reservation, other_usernames: set[str]) -> None:
    user, server = reservation.user, reservation.server
    who = ", ".join(sorted(other_usernames))
    message = (
        f"Heads up: {server.name} (reserved by you) is now being used by {who}. "
        f"Let us know if you still need your reservation."
    )
    send_whatsapp(
        db,
        user_id=user.id,
        whatsapp_number=user.whatsapp_number,
        notification_type=NotificationType.takeover_alert,
        message=message,
        server_id=server.id,
    )
    reservation.last_takeover_alert_at = datetime.now(timezone.utc)
    db.commit()


def check_stale_reservations() -> None:
    """Re-ask holders of long-running or long-standing reservations if they
    still need the time they've booked."""

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        threshold = timedelta(days=settings.stale_reservation_days)
        active_reservations = (
            db.query(Reservation).filter(Reservation.status == ReservationStatus.active).all()
        )
        for reservation in active_reservations:
            if now - as_aware(reservation.start_time) < threshold:
                continue
            if not _cooldown_ok(reservation.last_staleness_nudge_at):
                continue

            user, server = reservation.user, reservation.server
            message = (
                f"Hi {user.name}, you've had {server.name} reserved since "
                f"{reservation.start_time:%b %d} (through {reservation.end_time:%b %d}). "
                f"Still need it for the full booking?"
            )
            send_whatsapp(
                db,
                user_id=user.id,
                whatsapp_number=user.whatsapp_number,
                notification_type=NotificationType.stale_reservation,
                message=message,
                server_id=server.id,
            )
            reservation.last_staleness_nudge_at = now
            db.commit()
    finally:
        db.close()


def close_ended_reservations() -> None:
    """Mark reservations whose booked window has passed as ended."""

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        (
            db.query(Reservation)
            .filter(Reservation.status == ReservationStatus.active, Reservation.end_time <= now)
            .update({"status": ReservationStatus.ended}, synchronize_session=False)
        )
        db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    interval = settings.scheduler_interval_minutes
    scheduler.add_job(check_idle_reservations, "interval", minutes=interval, id="check_idle")
    scheduler.add_job(check_stale_reservations, "interval", hours=6, id="check_stale")
    scheduler.add_job(close_ended_reservations, "interval", minutes=interval, id="close_ended")
    scheduler.start()
    logger.info("Scheduler started (interval=%s min)", interval)
