"""PII detection service — regex-based detection for common data types."""

from __future__ import annotations

import re
import uuid
from typing import Any

from eaip.datamask.events import DataClassified, PiiDetected
from eaip.datamask.models import (
    ClassificationLevel,
    DataClassificationResult,
    PiiDetectionResult,
)
from eaip.events.bus import EventBus
from eaip.logging.context import get_logger

logger = get_logger("eaip.datamask.pii")

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_NAME_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


class PiiDetector:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._event_bus = event_bus or EventBus()

    async def detect_pii(self, data: dict[str, Any]) -> list[PiiDetectionResult]:
        results: list[PiiDetectionResult] = []
        for field_name, value in data.items():
            if isinstance(value, str):
                detected = await self.scan_field(field_name, value)
                if detected:
                    sample = value[:100]
                    result = PiiDetectionResult(
                        id=str(uuid.uuid4()),
                        field_name=field_name,
                        detected_types=tuple(detected),
                        confidence=self._calculate_confidence(detected),
                        occurrence_count=len(self._find_occurrences(value, detected)),
                        sample_values=(sample,),
                        location=field_name,
                    )
                    results.append(result)
                    await self._event_bus.publish(PiiDetected(result=result))
        return results

    async def scan_field(self, name: str, value: str) -> list[str]:
        detected_types: list[str] = []
        if _EMAIL_PATTERN.search(value):
            detected_types.append("email")
        if _PHONE_PATTERN.search(value):
            detected_types.append("phone")
        if _SSN_PATTERN.search(value):
            detected_types.append("ssn")
        if _CREDIT_CARD_PATTERN.search(value):
            detected_types.append("creditcard")
        if _IP_PATTERN.search(value):
            detected_types.append("ip")
        if _NAME_PATTERN.search(value):
            detected_types.append("name")
        return detected_types

    async def classify_data(self, data: dict[str, Any]) -> DataClassificationResult:
        pii_results = await self.detect_pii(data)
        types_found: set[str] = set()
        for r in pii_results:
            types_found.update(r.detected_types)

        score = min(len(types_found) / 7.0, 1.0) if types_found else 0.0

        if score >= 0.8:
            level = ClassificationLevel.CRITICAL
        elif score >= 0.5:
            level = ClassificationLevel.RESTRICTED
        elif score >= 0.2:
            level = ClassificationLevel.CONFIDENTIAL
        else:
            level = ClassificationLevel.PUBLIC

        result = DataClassificationResult(
            id=str(uuid.uuid4()),
            data_type="|".join(sorted(types_found)) if types_found else "none",
            classification_level=level,
            findings=tuple(sorted(types_found)),
            score=score,
        )
        await self._event_bus.publish(DataClassified(result=result))
        return result

    def _calculate_confidence(self, detected_types: list[str]) -> float:
        if not detected_types:
            return 0.0
        base = 1.0
        for t in detected_types:
            if t in ("email", "ip"):
                base *= 0.95
            elif t in ("ssn", "creditcard"):
                base *= 0.98
            else:
                base *= 0.85
        return round(base, 4)

    def _find_occurrences(self, value: str, detected_types: list[str]) -> list[str]:
        occurrences: list[str] = []
        for t in detected_types:
            if t == "email":
                occurrences.extend(_EMAIL_PATTERN.findall(value))
            elif t == "phone":
                occurrences.extend(_PHONE_PATTERN.findall(value))
            elif t == "ssn":
                occurrences.extend(_SSN_PATTERN.findall(value))
            elif t == "creditcard":
                occurrences.extend(_CREDIT_CARD_PATTERN.findall(value))
            elif t == "ip":
                occurrences.extend(_IP_PATTERN.findall(value))
            elif t == "name":
                occurrences.extend(_NAME_PATTERN.findall(value))
        return occurrences
