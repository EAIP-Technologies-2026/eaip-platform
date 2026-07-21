"""Host discovery service — network scanning, host registration, status tracking."""

from __future__ import annotations

from eaip.hostdisc.exceptions import HostNotFoundError
from eaip.hostdisc.models import DiscoveryConfig, DiscoveryJob, Host, HostStatus


class HostDiscoveryService:
    def __init__(self, config: DiscoveryConfig | None = None) -> None:
        self._config = config or DiscoveryConfig()
        self._hosts: dict[str, Host] = {}
        self._jobs: dict[str, DiscoveryJob] = {}

    @property
    def config(self) -> DiscoveryConfig:
        return self._config

    async def register_host(self, host: Host) -> Host:
        self._hosts[host.id] = host
        return host

    async def get_host(self, host_id: str) -> Host:
        host = self._hosts.get(host_id)
        if host is None:
            raise HostNotFoundError(f"Host {host_id} not found")
        return host

    async def update_host_status(self, host_id: str, status: HostStatus) -> Host:
        host = await self.get_host(host_id)
        updated = host.model_copy(update={"status": status, "last_seen": host.last_seen})
        self._hosts[host_id] = updated
        return updated

    async def create_job(self, job: DiscoveryJob) -> DiscoveryJob:
        self._jobs[job.id] = job
        return job

    async def list_hosts(self) -> list[Host]:
        return list(self._hosts.values())

    async def list_jobs(self) -> list[DiscoveryJob]:
        return list(self._jobs.values())


__all__ = ["HostDiscoveryService"]
