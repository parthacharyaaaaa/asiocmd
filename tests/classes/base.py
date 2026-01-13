'''Class definitions for testing BaseCmd functionality'''

from functools import wraps
from typing import Any, Literal, TextIO
from acmd import BaseCmd, command, command_helper
from acmd.decorators import HELPER_ATTR, COMMAND_ATTR

__all__ = ("RegistrarBaseCmd", "EchoCmd")

class RegistrarBaseCmd(BaseCmd):
    '''BaseCmd implementation for testing method registration'''
    # Decorator-based registration
    @command("foo") # Explicitly declared command name
    def xyz(self, line: str) -> None:
        self.stdout.write("foo")

    @command_helper("foo")
    def abc(self) -> None:
        self.stdout.write(self.xyz.__name__)

    @command    # Implicitly declared command name
    def bar(self, line: str) -> None:
        self.stdout.write(line)
    
    @command_helper("bar")
    def bartender(self) -> None:
        self.stdout.write(self.bar.__name__)

    # Legacy registration
    def do_stuff(self, line: str) -> None:
        self.stdout.write("stuff")

    def help_stuff(self, line: str) -> None:
        self.stdout.write(self.do_stuff.__name__)

    # Should never show up in command line
    def unregistered(self, line: str) -> None: ...

class EchoCmd(BaseCmd):
    @command
    def echo(self, line: str) -> None:
        self.stdout.write(line)

    @command
    def exit(self, line: str) -> Literal[True]:
        return True
    
class HookCmd(BaseCmd):

    __slots__ = ('output_array')

    def __init__(self, completekey: str = 'tab', prompt: str | None = None, stdin: TextIO | Any | None = None, stdout: TextIO | Any | None = None, use_raw_input: bool = True, intro: str | None = None, ruler: str = "=", doc_header: str = "Documented commands (type help <topic>):", misc_header: str = "Miscellaneous help topics:", undoc_header: str = "Undocumented commands:"):
        self.output_array: list[str] = [i.__name__ for i in (self.preloop, self.precmd, self.postcmd, self.postloop)]
        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header)

    def preloop(self):
        self.output_array.remove(self.preloop.__name__)
        self.stdout.write("preloop\n")
    
    def postloop(self):
        self.output_array.remove(self.postloop.__name__)
        self.stdout.write("postloop")

    def precmd(self, line: str):
        self.output_array.remove(self.precmd.__name__)
        self.stdout.write("precmd\n")
        return line

    def postcmd(self, stop, line: str):
        self.output_array.remove(self.postcmd.__name__)
        self.stdout.write("postcmd\n")
        return line
    
    @command
    def exit(self, line: str) -> Literal[True]:
        return True
    
    @command
    def foo(self, line: str) -> None:
        pass

class DecoratorCmd(BaseCmd):
    
    __slots__ = ("method_decorator_calls",)
    
    # Generic decorators
    @staticmethod
    def generic_method_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not (args and isinstance(args[0], DecoratorCmd)):
                raise ValueError(f"Bound method {func.__name__} called without {DecoratorCmd.__class__.__name__} as first postional argument")
            
            instance: DecoratorCmd = args[0]
            instance.method_decorator_calls.append(func.__name__)
            return func(*args, **kwargs)
        return wrapper
            
    def __init__(self, completekey: str = 'tab', prompt: str | None = None, stdin: TextIO | Any | None = None, stdout: TextIO | Any | None = None, use_raw_input: bool = True, intro: str | None = None, ruler: str = "=", doc_header: str = "Documented commands (type help <topic>):", misc_header: str = "Miscellaneous help topics:", undoc_header: str = "Undocumented commands:", auto_register: bool = True):
        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header, auto_register)
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
    
    @command
    def exit(self, line: str) -> Literal[True]: return True