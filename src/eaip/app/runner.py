"""Application entry point with signal-driven graceful shutdown."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from eaip.app.builder import ApplicationBuilder
from eaip.app.lifecycle import ApplicationLifecycle
from eaip.core.signals import ShutdownSignal, install_shutdown_handlers
from eaip.logging.context import get_logger
from eaip.services.collection import ServiceCollection
from eaip.settings.core_settings import PlatformSettings

OnRunningCallback = Callable[[ApplicationLifecycle], Awaitable[None]]


class ApplicationRunner:
    """Runs an EAIP application with signal-driven lifecycle management.

    Usage::

        runner = ApplicationRunner(app)
        await runner.run()
    """

    def __init__(
        self,
        application: ApplicationLifecycle,
        *,
        install_signals: bool = True,
    ) -> None:
        """Wrap an *application* lifecycle.

        Args:
            application: The application lifecycle to manage.
            install_signals: Whether to install SIGINT/SIGTERM handlers.
        """
        self._application = application
        self._install_signals = install_signals
        self._log = get_logger("eaip.app.runner")

    @property
    def application(self) -> ApplicationLifecycle:
        """Return the managed application lifecycle."""
        return self._application

    async def run(self, on_running: OnRunningCallback | None = None) -> None:
        """Start the application and wait for a shutdown signal.

        Args:
            on_running: Optional callback invoked after the application starts.
        """
        shutdown = ShutdownSignal()
        if self._install_signals:
            install_shutdown_handlers(shutdown)

        await self._application.start()
        try:
            if on_running is not None:
                await on_running(self._application)
            if not shutdown.is_set():
                self._log.info("app.awaiting_shutdown")
                await shutdown.wait()
        except BaseException as exc:
            self._log.error("app.runner_error", error=repr(exc))
            raise
        finally:
            await self._application.stop()


async def run_application(
    configure_services: Callable[[ServiceCollection], None] | None = None,
    settings: PlatformSettings | None = None,
    on_running: OnRunningCallback | None = None,
    install_signals: bool = True,
    builder: ApplicationBuilder | None = None,
) -> None:
    """Convenience function to build and run an application in one call.

    Args:
        configure_services: Optional callback to register services.
        settings: Optional platform settings (loaded from env if omitted).
        on_running: Optional callback invoked after the application starts.
        install_signals: Whether to install SIGINT/SIGTERM handlers.
        builder: Optional pre-configured ApplicationBuilder. If omitted,
            a new builder is created.
    """
    if builder is None:
        builder = ApplicationBuilder()
    if configure_services is not None:
        builder.with_services(configure_services)
    if settings is not None:
        builder.with_settings(settings)

    application = builder.build()
    runner = ApplicationRunner(
        application=application,
        install_signals=install_signals,
    )
    await runner.run(on_running=on_running)
