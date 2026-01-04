from typing import Callable, Coroutine, Any, TypeAlias

CmdMethod: TypeAlias = Callable[..., Coroutine[Any, Any, Any]|Any]