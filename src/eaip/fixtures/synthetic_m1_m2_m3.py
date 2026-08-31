from __future__ import annotations

from datetime import UTC, datetime, timedelta

SYNTHETIC_M1 = {
    "apex": [{"subject": "client onboarding", "content": "Apex standard: KYC before SOW", "memory_type": "institutional", "confidence": 0.9}],
    "nova": [{"subject": "supplier AlloyWorks", "content": "Nova supplier lead time 14 days", "memory_type": "enterprise_fact"}],
    "meridian": [{"subject": "policy HIPAA", "content": "Meridian policy requires quarterly access review", "memory_type": "institutional"}],
}
SYNTHETIC_M2 = {
    "apex": [{"target": "demand", "predicted_value": 120, "confidence": 0.7}],
    "nova": [{"target": "failure_rate", "predicted_value": 0.05}],
    "meridian": [{"target": "staffing_gap", "predicted_value": 2}],
}
SYNTHETIC_M3 = {
    "apex": [{"failure": "tool timeout", "expected_diagnosis": "tool_failure"}],
    "nova": [{"failure": "connector degraded", "expected_diagnosis": "connector_failure"}],
    "meridian": [{"failure": "policy denied", "expected_diagnosis": "policy_failure"}],
}
__all__ = ["SYNTHETIC_M1", "SYNTHETIC_M2", "SYNTHETIC_M3"]
