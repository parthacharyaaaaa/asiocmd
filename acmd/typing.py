from typing import Any, Callable, Coroutine, Protocol, TypeAlias, TypeVar

__all__ = ("CmdMethod", "SupportsContains")

CmdMethod: TypeAlias = Callable[..., Any | Coroutine[Any, Any, Any]]

T = TypeVar("T", bound=str, covariant=True)

class SupportsContains(Protocol[T]):
    def __contains__(self, o: object, /) -> bool: ...