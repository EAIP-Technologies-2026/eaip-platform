"""ModuleLoader — validates, registers, and manages the module registry.

:class:`ModuleLoader` is the gatekeeper for all
:class:`~eaip.runtime.module.RuntimeModule` instances.  Before a module can be
activated it must pass contract validation:

1. The value must satisfy the :class:`~eaip.runtime.module.RuntimeModule`
   structural protocol (``isinstance`` check via ``runtime_checkable``).
2. The module name must be non-empty and unique within the loader's registry.
3. Every declared dependency name is a non-empty string (existence is verified
   by the :class:`~eaip.runtime.graph.DependencyGraph` at start time).

The loader is **not** responsible for startup order or activation — that is
handled by :class:`~eaip.runtime.host.RuntimeHost`.
"""

from __future__ import annotations

from eaip.logging.context import get_logger
from eaip.runtime.exceptions import ModuleLoadError
from eaip.runtime.module import RuntimeModule


class ModuleLoader:
    """Validates and stores :class:`RuntimeModule` instances before activation."""

    def __init__(self) -> None:
        self._modules: dict[str, RuntimeModule] = {}
        self._log = get_logger("eaip.runtime.loader")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, module: RuntimeModule) -> None:
        """Validate and register ``module``.

        Raises :class:`~eaip.runtime.exceptions.ModuleLoadError` if:

        - ``module`` does not satisfy the :class:`RuntimeModule` protocol.
        - ``module.name`` is empty.
        - A module with the same name is already registered.
        """
        self._validate(module)
        if module.name in self._modules:
            raise ModuleLoadError(
                f"a module named {module.name!r} is already registered",
                context={"name": module.name},
            )
        self._modules[module.name] = module
        self._log.info(
            "runtime.module_registered",
            module=module.name,
            dependencies=list(module.dependencies),
        )

    def unregister(self, name: str) -> bool:
        """Remove the module with ``name``.  Returns ``True`` if it was present."""
        removed = self._modules.pop(name, None) is not None
        if removed:
            self._log.info("runtime.module_unregistered", module=name)
        return removed

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, name: str) -> RuntimeModule | None:
        """Return the module registered under ``name``, or ``None``."""
        return self._modules.get(name)

    def all(self) -> list[RuntimeModule]:
        """Return all registered modules in registration order."""
        return list(self._modules.values())

    def names(self) -> list[str]:
        """Sorted list of registered module names."""
        return sorted(self._modules)

    def __len__(self) -> int:
        return len(self._modules)

    def __contains__(self, name: str) -> bool:
        return name in self._modules

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(module: RuntimeModule) -> None:
        if not isinstance(module, RuntimeModule):
            raise ModuleLoadError(
                f"object of type {type(module).__name__!r} does not satisfy "
                "the RuntimeModule protocol",
                context={"type": type(module).__name__},
            )
        if not module.name or not module.name.strip():
            raise ModuleLoadError(
                "module name must be a non-empty string",
                context={"name": repr(module.name)},
            )
        for dep in module.dependencies:
            if not dep or not dep.strip():
                raise ModuleLoadError(
                    f"module {module.name!r} declared an empty dependency name",
                    context={"module": module.name},
                )


__all__ = ["ModuleLoader"]
