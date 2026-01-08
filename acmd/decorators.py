from functools import wraps
from typing import Any, Callable, Coroutine, Final

__all__ = ("COMMAND_ATTR", 'HELPER_ATTR',
           "command", "async_command",
           "command_helper", "async_command_helper")

COMMAND_ATTR: Final[str] = "__commandname__"
HELPER_ATTR: Final[str] = "__helpdata__"

def command(arg: str | Callable[..., Any] | None = None):
    def outer_decorated(method):
        @wraps(method)
        def inner_decorated(*args, **kwargs):
            return method(*args, **kwargs)
        
        setattr(inner_decorated, COMMAND_ATTR, arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated

def async_command(arg: str | Callable[..., Coroutine[Any, Any, Any]] | None = None):
    def outer_decorated(method):
        @wraps(method)
        async def inner_decorated(*args, **kwargs):
            return await method(*args, **kwargs)
        
        setattr(inner_decorated, COMMAND_ATTR, arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated

def command_helper(arg: str | Callable[..., Any]  | None = None):
    def outer_decorated(method):
        @wraps(method)
        def inner_decorated(*args, **kwargs):
            return method(*args, **kwargs)
        
        setattr(inner_decorated, HELPER_ATTR, arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated

def async_command_helper(arg: str | Callable[..., Coroutine[Any, Any, Any]] | None = None):
    def outer_decorated(method):
        @wraps(method)
        async def inner_decorated(*args, **kwargs):
            return await method(*args, **kwargs)
        
        setattr(inner_decorated, HELPER_ATTR, arg if isinstance(arg, str) else method.__name__)
        return inner_decorated
    
    return outer_decorated(arg) if callable(arg) else outer_decorated