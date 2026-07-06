"""ApplicationCompositionRoot — top-level composition that wires the entire EAIP application.

The :class:`ApplicationCompositionRoot` is responsible for:

1. Loading configuration from provided sources.
2. Creating and configuring the :class:`~eaip.platform.platform.Platform`.
3. Creating and configuring the :class:`~eaip.runtime.kernel.RuntimeKernel`.
4. Wiring infrastructure (clock, id generator, secret provider).
5. Wiring capabilities.
6. Wiring runtime modules.
7. Dependency injection bootstrap.
8. Establishing startup ordering via the :class:`StartupPipeline`.

This class composes existing components — it does NOT duplicate runtime logic.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from eaip.config.loader import ConfigLoader
from eaip.config.sources import ConfigSource, DictSource, EnvSource
from eaip.dependency_injection.container import Container
from eaip.logging.context import get_logger
from eaip.runtime.builder import RuntimeBuilder
from eaip.runtime.kernel import RuntimeKernel

if TYPE_CHECKING:
    from eaip.platform.platform import Platform
    from eaip.plugins.plugin import Plugin
    from eaip.runtime.module import RuntimeModule


class ApplicationCompositionRoot:
    """Composition root that wires the entire EAIP application.

    Usage::

        root = ApplicationCompositionRoot()
        root.load_config(source)
        root.build_platform()
        root.build_kernel(modules=[...], plugins=[...])
        root.wire()

        # Access composed objects
        platform = root.platform
        kernel = root.kernel
    """

    def __init__(self) -> None:
        """Initialize the composition root with empty state."""
        self._platform: Platform | None = None
        self._kernel: RuntimeKernel | None = None
        self._container: Container | None = None
        self._config_source: ConfigSource | None = None
        self._config_loader: ConfigLoader | None = None
        self._log = get_logger("eaip.application.composition")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform(self) -> Platform | None:
        """The composed :class:`~eaip.platform.platform.Platform`, if built."""
        return self._platform

    @property
    def kernel(self) -> RuntimeKernel | None:
        """The composed :class:`~eaip.runtime.kernel.RuntimeKernel`, if built."""
        return self._kernel

    @property
    def container(self) -> Container | None:
        """The DI :class:`~eaip.dependency_injection.container.Container`, if built."""
        return self._container

    @property
    def is_composed(self) -> bool:
        """``True`` once :meth:`wire` has been called successfully."""
        return self._platform is not None

    # ------------------------------------------------------------------
    # Configuration loading
    # ------------------------------------------------------------------

    def load_config(
        self,
        source: ConfigSource | None = None,
        raw: dict[str, Any] | None = None,
    ) -> None:
        """Load configuration from a source or raw dictionary.

        Args:
            source: A :class:`~eaip.config.sources.ConfigSource` instance.
            raw: A raw dictionary to use as config (creates a ``DictSource``).

        At least one of *source* or *raw* must be provided.
        """
        if source is not None:
            self._config_source = source
        elif raw is not None:
            self._config_source = DictSource(raw)
        else:
            self._config_source = EnvSource(prefix="EAIP_")

        self._config_loader = ConfigLoader(self._config_source)
        self._log.debug("composition.config_loaded", source=type(self._config_source).__name__)

    def config_source(self) -> ConfigSource | None:
        """Return the configured config source."""
        return self._config_source

    # ------------------------------------------------------------------
    # Platform building
    # ------------------------------------------------------------------

    def build_platform(
        self,
        settings: Any = None,
        container: Container | None = None,
        configure_logging: bool = True,
    ) -> Platform:
        """Build and return the :class:`~eaip.platform.platform.Platform`.

        Args:
            settings: Optional pre-built ``PlatformSettings``.
            container: Optional pre-built DI container.
            configure_logging: Whether to configure logging from settings.

        Returns:
            The composed platform instance (also available via ``.platform``).
        """
        from eaip.application import build_platform as _build_platform  # noqa: PLC0415, I001  # circular import

        kwargs: dict[str, Any] = {}
        if configure_logging:
            kwargs["configure_logging"] = True
        else:
            kwargs["configure_logging"] = False

        if settings is not None:
            kwargs["settings"] = settings

        plugins: list[Plugin] = []
        kwargs["plugins"] = plugins

        result = _build_platform(**kwargs)
        self._platform = result
        self._container = result.container

        if container is not None:
            self._container = container
            self._log.debug("composition.using_custom_container")

        self._log.info(
            "composition.platform_built",
            name=result.name,
            version=result.version,
        )
        return result

    # ------------------------------------------------------------------
    # Kernel building
    # ------------------------------------------------------------------

    def build_kernel(
        self,
        modules: Iterable[RuntimeModule] | None = None,
        plugins: Iterable[Plugin] | None = None,
    ) -> RuntimeKernel:
        """Build and return the :class:`~eaip.runtime.kernel.RuntimeKernel`.

        Args:
            modules: Runtime modules to register with the kernel.
            plugins: Plugins to register with the kernel.

        Returns:
            The composed kernel instance (also available via ``.kernel``).

        Raises:
            RuntimeError: If ``build_platform`` has not been called first.
        """
        if self._platform is None:
            raise RuntimeError("build_platform() must be called before build_kernel()")

        builder = RuntimeBuilder(platform=self._platform)

        if modules is not None:
            for mod in modules:
                builder = builder.with_module(mod)

        if plugins is not None:
            for plugin in plugins:
                builder = builder.with_plugin(plugin)

        kernel = builder.build()
        self._kernel = kernel
        self._log.info(
            "composition.kernel_built",
            modules=len(kernel.host.module_names),
        )
        return kernel

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def wire(self) -> None:
        """Perform final wiring after all components are built.

        This ensures the composition root, startup pipeline, and diagnostics
        are properly connected.  Idempotent.
        """
        if self._platform is None:
            raise RuntimeError("build_platform() must be called before wire()")

        self._log.info("composition.wired")
        self._log.debug(
            "composition.summary",
            platform_name=self._platform.name,
            platform_version=self._platform.version,
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def create(self, **kwargs: Any) -> tuple[Platform, RuntimeKernel | None]:
        """Convenience method: load, build, and wire in one call.

        Args:
            **kwargs: Forwarded to :meth:`load_config`, :meth:`build_platform`,
                and :meth:`build_kernel`.

        Returns:
            ``(platform, kernel)`` tuple.
        """
        self.load_config(source=kwargs.get("source"), raw=kwargs.get("raw"))
        self.build_platform(
            settings=kwargs.get("settings"),
            container=kwargs.get("container"),
            configure_logging=kwargs.get("configure_logging", True),
        )
        kernel: RuntimeKernel | None = None
        if "modules" in kwargs or "plugins" in kwargs:
            kernel = self.build_kernel(
                modules=kwargs.get("modules"),
                plugins=kwargs.get("plugins"),
            )
        self.wire()
        assert self._platform is not None
        return self._platform, kernel


__all__ = ["ApplicationCompositionRoot"]
