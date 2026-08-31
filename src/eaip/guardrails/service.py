"""Guardrails evaluator engine for prompt safety, PII detection/masking, and prompt injection defense."""

from __future__ import annotations

import re
from typing import Any

from eaip.guardrails.models import GuardrailConfig, GuardrailResult, GuardrailRule


class GuardrailsEngine:
    """Evaluates input prompts and completions against active safety and compliance rules."""

    PII_PATTERNS: dict[str, str] = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "API_KEY": r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?",
    }

    INJECTION_PATTERNS: list[str] = [
        r"(?i)ignore\s+(all\s+)?previous\s+instructions",
        r"(?i)system\s*override",
        r"(?i)you\s+are\s+now\s+in\s+DAN\s+mode",
        r"(?i)jailbreak",
    ]

    def __init__(self, config: GuardrailConfig | None = None) -> None:
        self.config = config or GuardrailConfig()
        self.rules: list[GuardrailRule] = []

    def add_rule(self, rule: GuardrailRule) -> None:
        self.rules.append(rule)

    def mask_pii(self, text: str) -> tuple[str, dict[str, int]]:
        masked_text = text
        counts: dict[str, int] = {}
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = list(re.finditer(pattern, masked_text))
            if matches:
                counts[pii_type] = len(matches)
                masked_text = re.sub(pattern, f"[{pii_type}_REDACTED]", masked_text)
        return masked_text, counts

    def check_prompt_injection(self, text: str) -> GuardrailResult:
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return GuardrailResult(
                    rule_id="prompt_injection_detector",
                    passed=False,
                    message="Potential prompt injection detected.",
                    details={"matched_pattern": pattern},
                )
        return GuardrailResult(
            rule_id="prompt_injection_detector",
            passed=True,
            message="No prompt injection detected.",
        )

    def evaluate_text(self, text: str) -> list[GuardrailResult]:
        results: list[GuardrailResult] = [self.check_prompt_injection(text)]
        for rule in self.rules:
            if not rule.enabled:
                continue
            matched = bool(re.search(rule.pattern, text))
            passed = not matched
            results.append(
                GuardrailResult(
                    rule_id=rule.id,
                    passed=passed,
                    message=f"Rule '{rule.name}' " + ("passed" if passed else "failed"),
                    details={"pattern": rule.pattern},
                )
            )
        return results
