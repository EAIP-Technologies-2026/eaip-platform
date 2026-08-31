"""MCP Audit Logger."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from eaip.logging.context import get_logger
from .models import McpAuditEntry


class McpAuditLogger:
    """Logs MCP tool executions according to Phase 4 audit rules."""

    def __init__(self) -> None:
        self.log = get_logger("eaip.mcp.audit")

    def log_entry(self, entry: McpAuditEntry) -> None:
        """Log a structured MCP audit entry."""
        log_data = entry.model_dump(exclude_none=True)
        log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # In a real environment, this would write to a dedicated secure audit sink
        # Here we use structlog to ensure it flows into the standard observability pipeline
        self.log.info(
            "mcp_audit",
            **log_data
        )

    def log_registration(self, server_id: str, name: str, success: bool, error: str | None = None) -> None:
        self.log_entry(McpAuditEntry(
            correlation_id="",
            action="register_server",
            server_id=server_id,
            status="SUCCESS" if success else "FAILED",
            error=error
        ))

    def log_invocation(
        self,
        correlation_id: str,
        server_id: str,
        tool_name: str,
        principal: str,
        args_hash: str,
        result_hash: str | None,
        duration_ms: float,
        success: bool,
        error: str | None = None
    ) -> None:
        self.log_entry(McpAuditEntry(
            correlation_id=correlation_id,
            action="invoke_tool",
            server_id=server_id,
            tool_name=tool_name,
            principal=principal,
            args_hash=args_hash,
            result_hash=result_hash,
            duration_ms=duration_ms,
            status="SUCCESS" if success else "FAILED",
            error=error
        ))
