from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .models import NotificationType, ReservationStatus, WatchRequestStatus


# ---------- Server ----------

class ServerBase(BaseModel):
    name: str
    hostname: Optional[str] = None
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
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None
    status: ReservationStatus
    idle_flagged: bool
    idle_since: Optional[datetime] = None
    created_at: datetime


# ---------- Watch requests ----------

class WatchRequestCreate(BaseModel):
    user_id: int
    min_vram_gb: Optional[float] = None
    gpu_type: Optional[str] = None
    min_gpu_count: Optional[int] = None
    min_cpu_cores: Optional[int] = None
    min_ram_gb: Optional[float] = None
    expires_at: Optional[datetime] = None


class WatchRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    min_vram_gb: Optional[float] = None
    gpu_type: Optional[str] = None
    min_gpu_count: Optional[int] = None
    min_cpu_cores: Optional[int] = None
    min_ram_gb: Optional[float] = None
    status: WatchRequestStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None


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
    timestamp: datetime
    gpu_util_percent: Optional[float] = None
    gpu_mem_used_gb: Optional[float] = None
    cpu_util_percent: Optional[float] = None
    ram_used_gb: Optional[float] = None
    active_processes: Optional[list[dict]] = None


# ---------- Notifications ----------

class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    server_id: Optional[int] = None
    type: NotificationType
    message: str
    sent_at: datetime


# ---------- Analytics ----------

class UserAnalyticsOut(BaseModel):
    user_id: int
    reserved_hours: float
    used_hours: float
    utilization_ratio: Optional[float] = None
    reservation_count: int
    idle_flag_count: int


ServerStatusOut.model_rebuild()
