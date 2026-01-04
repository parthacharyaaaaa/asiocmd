from functools import wraps
from typing import Any, Callable, Coroutine

__all__ = ("command", "async_command")

def command(arg: str | Callable[..., Any] | None = None):
    def outer_decorated(method: Callable[..., Any]):
        @wraps(method)
        def inner_decorated(*args, **kwargs):
            return method(*args, **kwargs)
        
        setattr(inner_decorated, "__commandname__", arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated

def async_command(arg: str | Callable[..., Coroutine[Any, Any, Any]] | None = None):
    def outer_decorated(method: Callable[..., Any]):
        @wraps(method)
        async def inner_decorated(*args, **kwargs):
            return await method(*args, **kwargs)
        
        setattr(inner_decorated, "__commandname__", arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated