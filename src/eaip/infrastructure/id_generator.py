"""Default :class:`IdGeneratorPort` implementation backed by :mod:`uuid`."""

from __future__ import annotations

import uuid

from eaip.ports.id_generator import IdGeneratorPort


class UuidIdGenerator(IdGeneratorPort):
    """Generates UUIDv4-backed string identifiers."""

    def new_id(self) -> str:
        return str(uuid.uuid4())


__all__ = ["UuidIdGenerator"]
