"""Knowledge discovery — plugin-based knowledge source discovery."""

from __future__ import annotations

from eaip.knowledge.base import DocumentParser
from eaip.knowledge.ingestion import register_parser
from eaip.knowledge.models import DocumentFormat
from eaip.logging.context import get_logger


class KnowledgeDiscovery:
    """Discovers custom parsers and knowledge sources from plugins.

    Scans installed plugins for custom document parsers and
    registers them with the ingestion pipeline.
    """

    def __init__(self) -> None:
        """Initialize KnowledgeDiscovery."""
        self._log = get_logger("eaip.knowledge.discovery")
        self._custom_parsers: list[DocumentParser] = []

    def register_custom_parser(self, fmt: DocumentFormat, parser: DocumentParser) -> None:
        """Register a custom document parser.

        Args:
            fmt: The document format this parser handles.
            parser: The parser implementation.
        """
        register_parser(fmt, parser)
        self._custom_parsers.append(parser)
        self._log.info("knowledge.discovery.parser_registered", format=fmt.value)

    def custom_parser_count(self) -> int:
        """Return the number of custom parsers registered.

        Returns:
            The custom parser count.
        """
        return len(self._custom_parsers)


__all__ = ["KnowledgeDiscovery"]
