# asiocmd: Modern cmd with async support

# Overview
`asiocmd` provides a very lightweight repacking of Python's cmd.Cmd class for building command line interfaces. The package contains 2 classes, namely `Cmd` and an inherited `AsyncCmd`

### Cmd
`Cmd` provides virtually the same functionality and development interface as `cmd.Cmd`, with the primary difference being in the way methods are looked up at runtime.

### AsyncCmd
An implementation of `Cmd` with added support for asynchronous methods 

# Installation
```bash
pip install asiocmd
```

# Usage
```python
from asiocmd import (AsyncCmd,
                  command, command_helper,
                  async_command, async_command_helper)

class DemoCmd(AsyncCmd):
    # Instance methods decorated with @command are registered as CLI commands

    # Command names can be specified as the decorator argument
    @command("foo")
    def arbitrary_name(self, line: str) -> None: ...

    # If the name argument is not provided,
    # the function name is taken as command name
    @command
    def bar(self, line: str) -> None: ...

    # Legacy support for cmd.Cmd's naming convention of do_*
    def do_xyz(self, line: str) -> None: ...

    # Helpers can be registered with @command_helper(<command_name>)
    @command_helper("foo")
    def arbitrary_helper(self) -> None: ...

    # Again, cmd.Cmd's helper naming convention is still supported
    def help_bar(self) -> None: ...

    # Asynchronous methods and helpers follow
    # the same convention, just with different decorators

    @async_command("afoo")
    async def async_name(self, line: str) -> None: ...

    @async_command
    async def abar(self, line: str) -> None: ...

    async def do_abc(self, line: str) -> None: ...

    @async_command_helper("afoo")
    async def afoo_helper(self) -> None: ...

# Launching the CLI
if __name__ == '__main__':
    asyncio.run(DemoCmd().acmdloop())
```

Note: **Cmd** uses cmdloop() to launch itself, the coroutine `acmdloop` belongs only to **AsyncCmd** to provide support for asynchronous methods.

Stacking of decorators are also supported, given that function metadata is preserved using `functools.wraps`

```python
from asiocmd import (AsyncCmd, command)
import functools

def generic_method_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Some working
        return func(*args, **kwargs)
    return wrapper

class DemoCmd(AsyncCmd):
    @generic_method_decorator
    @command_helper("foo")
    def abc(self) -> None: pass

    @generic_method_decorator
    def do_bar(self, line: str) -> None: pass
```