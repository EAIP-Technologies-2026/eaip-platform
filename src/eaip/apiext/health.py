"""Health check for the API Extensions subsystem."""

from __future__ import annotations

from eaip.apiext.caching import ResponseCache
from eaip.apiext.composition import ApiComposer
from eaip.apiext.rate_limit_policy import RateLimitPolicyEngine
from eaip.apiext.transforms import ResponseTransformer
from eaip.health.checks import HealthReport, HealthStatus


class ApiExtHealthCheck:
    """Health check for the API Extensions subsystem.

    Reports healthy when all sub-components are initialised.
    """

    name: str = "apiext"

    def __init__(
        self,
        composer: ApiComposer,
        cache: ResponseCache,
        rate_limit_engine: RateLimitPolicyEngine,
        transformer: ResponseTransformer,
    ) -> None:
        """Initialize the health check with all subsystem components.

        Args:
            composer: The API composer instance.
            cache: The response cache instance.
            rate_limit_engine: The rate-limit policy engine.
            transformer: The response transformer instance.
        """
        self._composer = composer
        self._cache = cache
        self._rate_limit_engine = rate_limit_engine
        self._transformer = transformer

    async def check(self) -> HealthReport:
        """Run the API Extensions health check.

        Returns:
            A health report describing the subsystem status.
        """
        composition_count = len(self._composer.list_compositions())
        cache_stats = await self._cache.get_stats()
        policy_count = len(self._rate_limit_engine.list_policies())
        transform_count = len(self._transformer.list_transforms())

        return HealthReport(
            component=self.name,
            status=HealthStatus.HEALTHY,
            message="API Extensions subsystem operational",
            details={
                "composition_count": composition_count,
                "cache_size": cache_stats.get("size", 0),
                "cache_max_size": cache_stats.get("max_size", 0),
                "policy_count": policy_count,
                "transform_count": transform_count,
            },
        )


__all__ = ["ApiExtHealthCheck"]
