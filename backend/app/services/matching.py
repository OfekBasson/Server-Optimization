"""Matching a Server's specs against a WatchRequest's requirements."""

from ..models import Server, WatchRequest


def server_matches_request(server: Server, request: WatchRequest) -> bool:
    if request.gpu_types:
        wanted = {t.lower() for t in request.gpu_types}
        if (server.gpu_type or "").lower() not in wanted:
            return False
    if request.min_gpu_count is not None and (server.gpu_count or 0) < request.min_gpu_count:
        return False
    if request.min_cpu_cores is not None and (server.cpu_cores or 0) < request.min_cpu_cores:
        return False
    if request.min_ram_gb is not None and (server.ram_gb or 0) < request.min_ram_gb:
        return False
    return True
