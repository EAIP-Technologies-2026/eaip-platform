"""A minimal, typed ``Result`` monad.

Why not exceptions? Because the Platform Foundation favours **explicit**
failure modes at well-defined boundaries (config loading, plugin discovery,
external IO). Domain code may still raise exceptions internally — the result
type only appears in public adapter contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Generic, NoReturn, TypeVar, final

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")
F = TypeVar("F")


@final
@dataclass(frozen=True, slots=True)
class Ok(Generic[T_co]):
    """Successful outcome carrying a value of type ``T``."""

    value: T_co

    is_ok: Final[bool] = True
    is_err: Final[bool] = False

    def unwrap(self) -> T_co:
        """Return the contained value."""
        return self.value

    def unwrap_or(self, _default: T_co, /) -> T_co:  # pragma: no cover - trivial
        return self.value

    def map(self, fn: Callable[[T_co], U]) -> Ok[U]:  # type: ignore[name-defined]
        return Ok(fn(self.value))


@final
@dataclass(frozen=True, slots=True)
class Err(Generic[E_co]):
    """Failure outcome carrying an error of type ``E``."""

    error: E_co

    is_ok: Final[bool] = False
    is_err: Final[bool] = True

    def unwrap(self) -> NoReturn:
        raise _ResultUnwrapError(self.error)

    def unwrap_or(self, default: U, /) -> U:
        return default

    def map(self, _fn: Callable[..., object]) -> Err[E_co]:  # type: ignore[name-defined]
        return self


#: Discriminated union covering both arms.
Result = Ok[T_co] | Err[E_co]  # type: ignore[valid-type]


class _ResultUnwrapError(RuntimeError):
    """Raised when :meth:`Err.unwrap` is called."""

    def __init__(self, error: object) -> None:
        super().__init__(f"Result.unwrap() called on Err({error!r})")
        self.error = error


# Late import to silence ruff's reordering while keeping mypy happy.
from collections.abc import Callable  # noqa: E402

__all__ = ["Err", "Ok", "Result"]
