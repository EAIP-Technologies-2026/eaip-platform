"""IncidentCommTool — send notifications and manage status pages."""

from __future__ import annotations

from eaip.inccomm.events import (
    IncidentEscalated,
    NotificationSent,
    StatusPageUpdated,
)
from eaip.inccomm.exceptions import IncidentNotFoundError
from eaip.inccomm.models import (
    CommConfig,
    CommStatus,
    IncidentComm,
    PageStatus,
    StatusPage,
)
from eaip.logging.context import get_logger
from eaip.shared.time import utc_now


class IncidentCommTool:
    """Central service for incident communications and status page management."""

    def __init__(self, config: CommConfig | None = None) -> None:
        self._config = config or CommConfig()
        self._communications: dict[str, IncidentComm] = {}
        self._status_pages: dict[str, StatusPage] = {}
        self._log = get_logger("eaip.inccomm.comm")

    @property
    def config(self) -> CommConfig:
        return self._config

    async def send_notification(self, comm: IncidentComm) -> IncidentComm:
        """Send a notification for an incident."""
        updated = comm.model_copy(update={"status": CommStatus.SENT, "sent_at": utc_now()})
        self._communications[comm.id] = updated
        NotificationSent(
            comm_id=comm.id,
            incident_id=comm.incident_id,
            channel=comm.channel,
            status=CommStatus.SENT,
        )
        self._log.info(
            "inccomm.notification.sent",
            comm_id=comm.id,
            incident_id=comm.incident_id,
            channel=comm.channel.value,
        )
        return updated

    async def get_communication(self, comm_id: str) -> IncidentComm:
        """Get a communication by ID."""
        comm = self._communications.get(comm_id)
        if comm is None:
            raise IncidentNotFoundError(f"Communication not found: {comm_id}")
        return comm

    async def list_communications(self, incident_id: str | None = None) -> list[IncidentComm]:
        """List communications, optionally filtered by incident."""
        result = list(self._communications.values())
        if incident_id is not None:
            result = [c for c in result if c.incident_id == incident_id]
        return sorted(result, key=lambda c: c.id)

    async def create_status_page(self, page: StatusPage) -> StatusPage:
        """Create a status page for an incident."""
        self._status_pages[page.id] = page
        self._log.info(
            "inccomm.status_page.created",
            page_id=page.id,
            incident_id=page.incident_id,
        )
        return page

    async def update_status_page(self, page_id: str, new_status: PageStatus) -> StatusPage:
        """Update the status of a status page."""
        page = self._status_pages.get(page_id)
        if page is None:
            raise IncidentNotFoundError(f"Status page not found: {page_id}")

        previous = page.status
        updated = page.model_copy(update={"status": new_status, "updated_at": utc_now()})
        self._status_pages[page_id] = updated

        StatusPageUpdated(
            page_id=page_id,
            incident_id=page.incident_id,
            new_status=new_status,
        )

        if new_status == PageStatus.RESOLVED and previous != PageStatus.RESOLVED:
            self._log.info(
                "inccomm.incident.resolved",
                incident_id=page.incident_id,
                page_id=page_id,
            )

        return updated

    async def escalate_incident(self, incident_id: str, escalation_level: int = 1) -> StatusPage:
        """Escalate an incident to a higher severity level."""
        pages = [p for p in self._status_pages.values() if p.incident_id == incident_id]
        if not pages:
            raise IncidentNotFoundError(f"No status page for incident: {incident_id}")

        page = pages[0]
        previous = page.status
        new_status = PageStatus.IDENTIFIED if escalation_level <= 2 else PageStatus.MONITORING

        updated = page.model_copy(update={"status": new_status, "updated_at": utc_now()})
        self._status_pages[page.id] = updated

        IncidentEscalated(
            incident_id=incident_id,
            previous_status=previous,
            new_status=new_status,
            escalation_level=escalation_level,
        )

        self._log.info(
            "inccomm.incident.escalated",
            incident_id=incident_id,
            level=escalation_level,
            previous=previous.value,
            new=new_status.value,
        )
        return updated

    async def get_statistics(self) -> dict[str, object]:
        """Return summary statistics."""
        total_comm = len(self._communications)
        sent = sum(1 for c in self._communications.values() if c.status == CommStatus.SENT)
        delivered = sum(
            1 for c in self._communications.values() if c.status == CommStatus.DELIVERED
        )
        failed = sum(1 for c in self._communications.values() if c.status == CommStatus.FAILED)
        return {
            "total_communications": total_comm,
            "sent": sent,
            "delivered": delivered,
            "failed": failed,
            "total_status_pages": len(self._status_pages),
        }


__all__ = ["IncidentCommTool"]
