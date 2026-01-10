'''Class definitions for testing BaseCmd functionality'''

from typing import Any, Callable, Literal, Sequence, TextIO
from acmd import BaseCmd, command, command_helper

__all__ = ("RegistrarBaseCmd", "EchoCmd")

class RegistrarBaseCmd(BaseCmd):
    '''BaseCmd implementation for testing method registration'''
    # Decorator-based registration
    @command("foo") # Explicitly declared command name
    def xyz(self, line: str) -> None:
        self.stdout.write("foo")

    @command_helper("foo")
    def abc(self) -> None:
        self.stdout.write(self.xyz)

    @command    # Implicitly declared command name
    def bar(self, line: str) -> None:
        self.stdout.write(line)
    
    @command_helper("bar")
    def bartender(self) -> None:
        self.stdout.write(self.bar)

    # Legacy registration
    def do_stuff(self, line: str) -> None:
        self.stdout.write("stuff")

    def help_stuff(self, line: str) -> None:
        self.stdout.write(self.do_stuff)

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