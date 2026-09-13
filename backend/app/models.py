import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReservationStatus(str, enum.Enum):
    active = "active"
    ended = "ended"
    released = "released"


class WatchRequestStatus(str, enum.Enum):
    active = "active"
    fulfilled = "fulfilled"
    expired = "expired"


class NotificationType(str, enum.Enum):
    idle_nudge = "idle_nudge"
    stale_reservation = "stale_reservation"
    watch_match = "watch_match"
    takeover_alert = "takeover_alert"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    university_email = Column(String, unique=True, nullable=False, index=True)
    whatsapp_number = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    # Only ever set for admins - regular users never log in, so never have one.
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    os_usernames = relationship(
        "OsUsername", back_populates="user", cascade="all, delete-orphan"
    )
    reservations = relationship("Reservation", back_populates="user")
    watch_requests = relationship("WatchRequest", back_populates="user")


class OsUsername(Base):
    """Maps a Linux account on a specific server to an app User.

    Needed to attribute UsageSample process ownership back to a lab
    member, since OS accounts may not be identical across all 6 machines.
    """

    __tablename__ = "os_usernames"
    __table_args__ = (UniqueConstraint("server_id", "os_username", name="uq_server_os_username"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    os_username = Column(String, nullable=False)

    user = relationship("User", back_populates="os_usernames")
    server = relationship("Server", back_populates="os_usernames")


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    hostname = Column(String, nullable=True)
    ssh_port = Column(Integer, nullable=True)
    pi = Column(String, nullable=True)

    gpu_type = Column(String, nullable=True)
    gpu_count = Column(Integer, default=0)
    vram_gb = Column(Float, nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    ram_gb = Column(Float, nullable=True)
    disk_gb = Column(Float, nullable=True)

    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    os_usernames = relationship(
        "OsUsername", back_populates="server", cascade="all, delete-orphan"
    )
    reservations = relationship("Reservation", back_populates="server")
    usage_samples = relationship("UsageSample", back_populates="server")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    purpose = Column(String, nullable=True)

    status = Column(Enum(ReservationStatus), default=ReservationStatus.active, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    released_at = Column(DateTime(timezone=True), nullable=True)

    # Idle-but-reserved tracking (drives nudges + the takeover alert loop)
    idle_flagged = Column(Boolean, default=False, nullable=False)
    idle_since = Column(DateTime(timezone=True), nullable=True)
    last_idle_nudge_at = Column(DateTime(timezone=True), nullable=True)
    last_takeover_alert_at = Column(DateTime(timezone=True), nullable=True)

    # Long-standing reservation check-ins
    last_staleness_nudge_at = Column(DateTime(timezone=True), nullable=True)

    server = relationship("Server", back_populates="reservations")
    user = relationship("User", back_populates="reservations")


class UsageSample(Base):
    __tablename__ = "usage_samples"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    gpu_util_percent = Column(Float, nullable=True)
    gpu_mem_used_gb = Column(Float, nullable=True)
    cpu_util_percent = Column(Float, nullable=True)
    ram_used_gb = Column(Float, nullable=True)

    # [{"os_username": "alice", "process": "python train.py", "pid": 1234}, ...]
    active_processes = Column(JSON, nullable=True)

    server = relationship("Server", back_populates="usage_samples")


class WatchRequest(Base):
    """An ad hoc, expiring 'notify me when a server like this is free' request.

    Deliberately not a permanent per-user profile: what someone needs
    changes task to task, so requests are created for a specific need and
    retired once fulfilled or expired.
    """

    __tablename__ = "watch_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # None/empty means "any GPU type"; a server matches if its gpu_type is
    # one of these (case-insensitive)
    gpu_types = Column(JSON, nullable=True)
    min_gpu_count = Column(Integer, nullable=True)
    min_cpu_cores = Column(Integer, nullable=True)
    min_ram_gb = Column(Float, nullable=True)

    status = Column(Enum(WatchRequestStatus), default=WatchRequestStatus.active, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="watch_requests")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=True)
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=utcnow)
