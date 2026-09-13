from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict

from .models import NotificationType, ReservationStatus, WatchRequestStatus
from .utils import as_aware


def _as_aware_or_none(v: Optional[datetime]) -> Optional[datetime]:
    return as_aware(v) if v is not None else None


# Datetimes read back from the DB aren't reliably timezone-aware (SQLite in
# particular drops tzinfo entirely) - coercing here guarantees every "Out"
# schema always serializes with an explicit UTC offset, so the frontend
# never has to guess what timezone a bare timestamp is in.
AwareDatetime = Annotated[datetime, BeforeValidator(as_aware)]
AwareDatetimeOrNone = Annotated[Optional[datetime], BeforeValidator(_as_aware_or_none)]


# ---------- Server ----------

class ServerBase(BaseModel):
    name: str
    hostname: Optional[str] = None
    ssh_port: Optional[int] = None
    pi: Optional[str] = None
    gpu_type: Optional[str] = None
    gpu_count: int = 0
    vram_gb: Optional[float] = None
    cpu_cores: Optional[int] = None
    ram_gb: Optional[float] = None
    disk_gb: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class ServerCreate(ServerBase):
    pass


class ServerOut(ServerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ServerStatusOut(ServerOut):
    current_reservation: Optional["ReservationOut"] = None
    is_idle_flagged: bool = False


# ---------- Reservation ----------

class ReservationCreate(BaseModel):
    server_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    server_id: int
    user_id: int
    start_time: AwareDatetime
    end_time: AwareDatetime
    purpose: Optional[str] = None
    status: ReservationStatus
    idle_flagged: bool
    idle_since: AwareDatetimeOrNone = None
    created_at: AwareDatetime


class ReservationReschedule(BaseModel):
    start_time: datetime
    end_time: datetime


# ---------- Watch requests ----------

class WatchRequestCreate(BaseModel):
    user_id: int
    gpu_types: Optional[list[str]] = None
    min_gpu_count: Optional[int] = None
    min_cpu_cores: Optional[int] = None
    min_ram_gb: Optional[float] = None
    expires_at: Optional[datetime] = None


class WatchRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    gpu_types: Optional[list[str]] = None
    min_gpu_count: Optional[int] = None
    min_cpu_cores: Optional[int] = None
    min_ram_gb: Optional[float] = None
    status: WatchRequestStatus
    created_at: AwareDatetime
    expires_at: AwareDatetimeOrNone = None
    fulfilled_at: AwareDatetimeOrNone = None


# ---------- Usage samples (posted by the monitoring agent) ----------

class ActiveProcess(BaseModel):
    os_username: str
    process: str
    pid: Optional[int] = None


class UsageSampleIn(BaseModel):
    server_name: str
    gpu_util_percent: Optional[float] = None
    gpu_mem_used_gb: Optional[float] = None
    cpu_util_percent: Optional[float] = None
    ram_used_gb: Optional[float] = None
    active_processes: list[ActiveProcess] = []


class UsageSampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    server_id: int
    timestamp: AwareDatetime
    gpu_util_percent: Optional[float] = None
    gpu_mem_used_gb: Optional[float] = None
    cpu_util_percent: Optional[float] = None
    ram_used_gb: Optional[float] = None
    active_processes: Optional[list[dict]] = None


# ---------- OS username mapping ----------

class OsUsernameCreate(BaseModel):
    university_email: str
    server_name: str
    os_username: str


class OsUsernameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    server_id: int
    os_username: str


# ---------- Users / identification ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    university_email: str
    whatsapp_number: Optional[str] = None
    is_admin: bool = False


class UserSummary(BaseModel):
    """Public list for the "who are you" picker - no whatsapp number."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    university_email: str


class UserCreate(BaseModel):
    name: str
    university_email: str
    whatsapp_number: Optional[str] = None
    is_admin: bool = False
    password: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_admin: Optional[bool] = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class SetPasswordRequest(BaseModel):
    password: str


# ---------- Notifications ----------

class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    server_id: Optional[int] = None
    type: NotificationType
    message: str
    sent_at: AwareDatetime


# ---------- Analytics ----------

class UserAnalyticsOut(BaseModel):
    user_id: int
    reserved_hours: float
    used_hours: float
    utilization_ratio: Optional[float] = None
    reservation_count: int
    idle_flag_count: int


ServerStatusOut.model_rebuild()
