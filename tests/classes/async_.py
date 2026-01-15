import asyncio
from functools import wraps
from typing import Any, Literal, TextIO
from asiocmd import (AsyncCmd,
                  command, command_helper,
                  async_command, async_command_helper)

class AsyncTestCmd(AsyncCmd):
    # Synchronous command and command helpers
    @command
    def foo(self, line: str) -> None:
        self.stdout.write(self.foo.__name__)

    @command_helper("foo")
    def foo_helper(self) -> None:
        self.stdout.write(self.foo_helper.__name__)

    def do_bar(self, line: str) -> None:
        self.stdout.write(self.do_bar.__name__)
    
    def help_bar(self) -> None:
        self.stdout.write(self.help_bar.__name__)

    # Asynchronous
    @async_command
    async def io(self, line: str) -> None:
        host, port = line.split(":")
        try:
            await asyncio.open_connection(host=host, port=int(port))
        except ConnectionError:
            pass
        finally:
            self.stdout.write(self.io.__name__)

    @async_command_helper("io")
    async def io_helper(self) -> None:
        self.stdout.write(self.io_helper.__name__)
    
    @async_command
    async def afoo(self, line: str) -> None:
        self.stdout.write(self.afoo.__name__)
    
    @async_command_helper("afoo")
    async def afoo_helper(self) -> None:
        self.stdout.write(self.afoo_helper.__name__)

    def do_exit(self, line: str) -> Literal[True]:
        self.stdout.write(self.do_exit.__name__)
        return True
    
class AsyncHookCmd(AsyncCmd):
    __slots__ = ("order_list",)
    def __init__(self, completekey: str = 'tab', prompt: str | None = None, stdin: TextIO | Any | None = None, stdout: TextIO | Any | None = None, use_raw_input: bool = True, intro: str | None = None, ruler: str = "=", doc_header: str = "Documented commands (type help <topic>):", misc_header: str = "Miscellaneous help topics:", undoc_header: str = "Undocumented commands:", apreloop_first: bool = False, apostloop_first: bool = False, apostcmd_first: bool = False, aprecmd_first: bool = False):
        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header, apreloop_first, apostloop_first, apostcmd_first, aprecmd_first)
        self.order_list: list[str] = []
    
    def preloop(self):
        self.order_list.append(self.preloop.__name__)
    def precmd(self, line: str):
        self.order_list.append(self.precmd.__name__)
        return line
    def postcmd(self, stop, line: str):
        self.order_list.append(self.postcmd.__name__)
        return stop
    def postloop(self):
        self.order_list.append(self.postloop.__name__)
    
    async def apreloop(self):
        self.order_list.append(self.apreloop.__name__)
    async def aprecmd(self, line: str):
        self.order_list.append(self.aprecmd.__name__)
        return line
    async def apostcmd(self, stop, line: str):
        self.order_list.append(self.apostcmd.__name__)
        return stop
    async def apostloop(self):
        self.order_list.append(self.apostloop.__name__)
    
    @command
    def exit(self, line: str) -> Literal[True]:
        return True
    
class AsyncDecoratorCmd(AsyncCmd):
    
    __slots__ = ("method_decorator_calls",)
    
    # Generic decorators
    @staticmethod
    def generic_method_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not (args and isinstance(args[0], AsyncDecoratorCmd)):
                raise ValueError(f"Bound method {func.__name__} called without {AsyncDecoratorCmd.__class__.__name__} as first postional argument")
            
            instance: AsyncDecoratorCmd = args[0]
            instance.method_decorator_calls.append(func.__name__)
            return func(*args, **kwargs)
        return wrapper
            
    def __init__(self, completekey: str = 'tab', prompt: str | None = None, stdin: TextIO | Any | None = None, stdout: TextIO | Any | None = None, use_raw_input: bool = True, intro: str | None = None, ruler: str = "=", doc_header: str = "Documented commands (type help <topic>):", misc_header: str = "Miscellaneous help topics:", undoc_header: str = "Undocumented commands:", auto_register: bool = True):
        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header)
        self.method_decorator_calls: list[str] = []

    @generic_method_decorator
    @command
    def foo(self, line: str) -> None: pass

    @generic_method_decorator
    @command_helper("foo")
    def abc(self) -> None: pass

    @generic_method_decorator
    def do_bar(self, line: str) -> None: pass

    @generic_method_decorator
    def help_bar(self) -> None: pass

    @command("rfoo")
    @generic_method_decorator
    def reversed_foo(self, line: str) -> None: pass

    @generic_method_decorator
    @async_command
    async def afoo(self, line: str) -> None: pass

    @generic_method_decorator
    @async_command_helper("afoo")
    async def aabc(self) -> None: pass

    @generic_method_decorator
    async def do_abar(self, line: str) -> None: pass

    @generic_method_decorator
    async def help_abar(self) -> None: pass

    @async_command("arfoo")
    @generic_method_decorator
    async def areversed_foo(self, line: str) -> None: pass
    
    @command
    def exit(self, line: str) -> Literal[True]: return True