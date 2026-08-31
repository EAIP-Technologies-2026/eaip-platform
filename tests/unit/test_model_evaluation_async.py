"""Unit test for ModelEvaluationService completion evaluation."""

from __future__ import annotations

import pytest

from eaip.model_evaluation import ModelEvaluationService


@pytest.mark.asyncio
async def test_evaluate_completion() -> None:
    svc = ModelEvaluationService()
    scores = await svc.evaluate_completion("Explain quantum computing", "Quantum computing uses qubits.")
    assert "relevance_score" in scores
    assert "factuality_score" in scores
    assert scores["relevance_score"] > 0
