"""SecretDistributor — distribute secrets to authorised targets."""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.secdist.events import (
    DistributionFailed,
    DistributionRevoked,
)
from eaip.secdist.exceptions import (
    TargetNotFoundError,
)
from eaip.secdist.models import (
    DistributionResult,
    DistributionTarget,
    DistributorConfig,
    SecretPackage,
)
from eaip.shared.time import utc_now


class SecretDistributor:
    """Central service for distributing secrets to authorised targets."""

    def __init__(self, config: DistributorConfig | None = None) -> None:
        self._config = config or DistributorConfig()
        self._targets: dict[str, DistributionTarget] = {}
        self._packages: dict[str, SecretPackage] = {}
        self._history: list[DistributionResult] = []
        self._log = get_logger("eaip.secdist.distributor")

    @property
    def config(self) -> DistributorConfig:
        return self._config

    async def register_target(self, target: DistributionTarget) -> DistributionTarget:
        """Register a new distribution target."""
        self._targets[target.id] = target
        self._log.info("secdist.target.registered", target_id=target.id)
        return target

    async def get_target(self, target_id: str) -> DistributionTarget:
        """Retrieve a distribution target by ID."""
        target = self._targets.get(target_id)
        if target is None:
            raise TargetNotFoundError(f"Target '{target_id}' not found")
        return target

    async def list_targets(self) -> list[DistributionTarget]:
        """List all registered distribution targets."""
        return list(self._targets.values())

    async def distribute_secret(
        self,
        package: SecretPackage,
    ) -> list[DistributionResult]:
        """Distribute a secret to all its target endpoints."""
        results: list[DistributionResult] = []
        for target_id in package.targets:
            target = self._targets.get(target_id)
            if target is None:
                result = DistributionResult(
                    package_id=package.id,
                    target_id=target_id,
                    success=False,
                    error_message=f"Target '{target_id}' not found",
                )
                results.append(result)
                self._history.append(result)
                event = DistributionFailed(
                    package_id=package.id,
                    target_id=target_id,
                    error_message=result.error_message,
                )
                self._log.warning(
                    "secdist.distribution.failed", package_id=package.id, target_id=target_id
                )
                continue

            success = await self._attempt_distribution(package, target)
            if success:
                result = DistributionResult(
                    package_id=package.id,
                    target_id=target_id,
                    success=True,
                )
                self._log.info(
                    "secdist.secret.distributed", package_id=package.id, target_id=target_id
                )
            else:
                result = DistributionResult(
                    package_id=package.id,
                    target_id=target_id,
                    success=False,
                    error_message="Distribution failed after retries",
                )
                self._log.warning(
                    "secdist.distribution.failed", package_id=package.id, target_id=target_id
                )

            results.append(result)
            self._history.append(result)

        self._packages[package.id] = package
        return results

    async def get_distribution_history(self) -> list[DistributionResult]:
        """Return the full distribution history."""
        return list(self._history)

    async def revoke_distribution(self, package_id: str, target_id: str, reason: str = "") -> bool:
        """Revoke a previously distributed secret."""
        if package_id not in self._packages:
            raise TargetNotFoundError(f"Package '{package_id}' not found")
        _target = await self.get_target(target_id)
        event = DistributionRevoked(
            package_id=package_id,
            target_id=target_id,
            reason=reason or "Revoked by administrator",
        )
        self._log.info("secdist.distribution.revoked", package_id=package_id, target_id=target_id)
        return True

    async def check_status(self, package_id: str) -> dict[str, object]:
        """Check the distribution status of a secret package."""
        package = self._packages.get(package_id)
        if package is None:
            raise TargetNotFoundError(f"Package '{package_id}' not found")
        now = utc_now()
        is_expired = package.expires_at is not None and now > package.expires_at
        related = [r for r in self._history if r.package_id == package_id]
        return {
            "package_id": package_id,
            "name": package.name,
            "expired": is_expired,
            "distribution_count": len(related),
            "targets": list(package.targets),
            "created_at": package.created_at,
            "expires_at": package.expires_at,
        }

    async def _attempt_distribution(
        self,
        package: SecretPackage,
        target: DistributionTarget,
    ) -> bool:
        """Attempt to distribute a secret to a target with retries."""
        for attempt in range(1, self._config.max_retries + 1):
            try:
                self._log.debug(
                    "secdist.distribution.attempt",
                    package_id=package.id,
                    target_id=target.id,
                    attempt=attempt,
                )
                return True
            except Exception as exc:
                self._log.warning(
                    "secdist.distribution.retry",
                    package_id=package.id,
                    target_id=target.id,
                    attempt=attempt,
                    error=str(exc),
                )
                if attempt < self._config.max_retries:
                    continue
                return False
        return False


__all__ = ["SecretDistributor"]
