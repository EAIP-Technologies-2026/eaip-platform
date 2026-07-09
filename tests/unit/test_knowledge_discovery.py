from __future__ import annotations

import copy

from eaip.knowledge.discovery import KnowledgeDiscovery
from eaip.knowledge.ingestion import TextParser, get_parser, register_parser
from eaip.knowledge.models import DocumentFormat


class _CustomParser:
    async def parse(self, content: bytes, **kwargs: str) -> str:
        return "custom: " + content.decode()


class TestKnowledgeDiscovery:
    def test_register_custom_parser(self) -> None:
        original = get_parser(DocumentFormat.TXT)
        discovery = KnowledgeDiscovery()
        parser = _CustomParser()
        discovery.register_custom_parser(DocumentFormat.TXT, parser)
        assert discovery.custom_parser_count() == 1
        register_parser(DocumentFormat.TXT, original)

    def test_default_parser_count(self) -> None:
        discovery = KnowledgeDiscovery()
        assert discovery.custom_parser_count() == 0
