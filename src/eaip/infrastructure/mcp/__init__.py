"""MCP Infrastructure Module.

Provides EAIMcpClient and McpAuditLogger per Phase 4 requirements.
"""

from .client import EAIMcpClient
from .audit import McpAuditLogger
from .models import McpServerManifest, McpAuditEntry, ToolSpec, ToolResult

__all__ = [
    "EAIMcpClient",
    "McpAuditLogger",
    "McpServerManifest",
    "McpAuditEntry",
    "ToolSpec",
    "ToolResult",
]
