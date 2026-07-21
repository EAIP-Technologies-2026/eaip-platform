"""Tests for :mod:`eaip.datamask.pii`."""

from __future__ import annotations

import pytest

from eaip.datamask.models import ClassificationLevel
from eaip.datamask.pii import PiiDetector


class TestPiiDetector:
    @pytest.fixture
    def detector(self) -> PiiDetector:
        return PiiDetector()

    async def test_detect_email(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"email": "john.doe@example.com"})
        assert len(results) == 1
        assert "email" in results[0].detected_types
        assert results[0].field_name == "email"

    async def test_detect_phone(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"phone": "+1 (555) 123-4567"})
        assert len(results) == 1
        assert "phone" in results[0].detected_types

    async def test_detect_ssn(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"ssn": "123-45-6789"})
        assert len(results) == 1
        assert "ssn" in results[0].detected_types

    async def test_detect_credit_card(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"card": "4111-1111-1111-1111"})
        assert len(results) == 1
        assert "creditcard" in results[0].detected_types

    async def test_detect_ip(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"ip": "192.168.1.1"})
        assert len(results) == 1
        assert "ip" in results[0].detected_types

    async def test_detect_name(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"name": "John Doe"})
        assert len(results) == 1
        assert "name" in results[0].detected_types

    async def test_detect_multiple_types(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"contact": "john@example.com +1-555-123-4567"})
        found_types = set()
        for r in results:
            found_types.update(r.detected_types)
        assert "email" in found_types
        assert "phone" in found_types

    async def test_no_pii(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({"greeting": "hello world"})
        assert len(results) == 0

    async def test_empty_data(self, detector: PiiDetector) -> None:
        results = await detector.detect_pii({})
        assert len(results) == 0

    async def test_scan_field_email(self, detector: PiiDetector) -> None:
        detected = await detector.scan_field("email", "user@test.com")
        assert "email" in detected

    async def test_scan_field_no_match(self, detector: PiiDetector) -> None:
        detected = await detector.scan_field("name", "just a name")
        assert len(detected) == 0

    async def test_classify_public(self, detector: PiiDetector) -> None:
        result = await detector.classify_data({"greeting": "hello"})
        assert result.classification_level is ClassificationLevel.PUBLIC
        assert result.score == 0.0

    async def test_classify_confidential(self, detector: PiiDetector) -> None:
        result = await detector.classify_data(
            {"email": "user@example.com", "phone": "+1-555-123-4567"}
        )
        assert result.classification_level is ClassificationLevel.CONFIDENTIAL

    async def test_classify_critical(self, detector: PiiDetector) -> None:
        result = await detector.classify_data(
            {
                "email": "user@example.com",
                "ssn": "123-45-6789",
                "card": "4111-1111-1111-1111",
                "phone": "+1-555-123-4567",
                "ip": "10.0.0.1",
                "name": "John Doe",
            }
        )
        assert result.classification_level is ClassificationLevel.CRITICAL
        assert result.score >= 0.8
