from typing import Any, Callable, Coroutine, TypeAlias

__all__ = ("CmdMethod",)

CmdMethod: TypeAlias = Callable[..., Any | Coroutine[Any, Any, Any]]