"""Data classification service — classify data, evaluate compliance, and manage classification levels."""

from __future__ import annotations

from typing import Any

from eaip.audit.exceptions import ClassificationError
from eaip.audit.models import ClassificationLevel, DataClassification


class DataClassifier:
    def __init__(self) -> None:
        self._classifications: dict[str, DataClassification] = {}

    def classify(self, data: Any, context: dict[str, Any] | None = None) -> DataClassification:
        data_type = self._infer_data_type(data)
        existing = self._classifications.get(data_type)
        if existing:
            return existing
        level = self._infer_level(data, context or {})
        classification = DataClassification(
            id=data_type,
            name=f"{data_type}_classification",
            level=level,
            rules=(),
            retention_days=90,
        )
        self._classifications[data_type] = classification
        return classification

    async def evaluate(self, data: Any, classification: DataClassification) -> bool:
        inferred = self.classify(data)
        return inferred.level == classification.level

    def get_classification_level(self, data_type: str) -> ClassificationLevel:
        existing = self._classifications.get(data_type)
        if existing is None:
            raise ClassificationError(f"No classification found for data type {data_type!r}")
        return existing.level

    def list_classifications(self) -> list[DataClassification]:
        return list(self._classifications.values())

    def register_classification(self, classification: DataClassification) -> DataClassification:
        self._classifications[classification.id] = classification
        return classification

    @staticmethod
    def _infer_data_type(data: Any) -> str:
        if isinstance(data, dict):
            return str(data.get("type", type(data).__name__))
        return type(data).__name__

    @staticmethod
    def _infer_level(data: Any, context: dict[str, Any]) -> ClassificationLevel:
        if context.get("sensitive"):
            return ClassificationLevel.RESTRICTED
        if context.get("confidential"):
            return ClassificationLevel.CONFIDENTIAL
        return ClassificationLevel.INTERNAL


__all__ = ["DataClassifier"]
