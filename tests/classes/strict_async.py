from typing import Any, Literal, Sequence, TextIO
from acmd import (StrictAsyncCmd,
                  command, command_helper,
                  async_command, async_command_helper)

class AsyncHookTestCmd(StrictAsyncCmd):
    __slots__ = ('output_array')

    def __init__(self, completekey: str = 'tab', prompt: str | None = None, stdin: TextIO | Any | None = None, stdout: TextIO | Any | None = None, use_raw_input: bool = True, intro: str | None = None, ruler: str = "=", doc_header: str = "Documented commands (type help <topic>):", misc_header: str = "Miscellaneous help topics:", undoc_header: str = "Undocumented commands:", excluded_commands: Sequence[str] | None = None):
        self.output_array: list[str] = [i.__name__ for i in (self.preloop, self.precmd, self.postcmd, self.postloop)]
        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header, excluded_commands)

    async def apreloop(self):
        self.output_array.remove(self.preloop.__name__)
        self.stdout.write("preloop\n")
    
    async def apostloop(self):
        self.output_array.remove(self.postloop.__name__)
        self.stdout.write("postloop")

    async def aprecmd(self, line: str):
        self.output_array.remove(self.precmd.__name__)
        self.stdout.write("precmd\n")
        return line

    async def apostcmd(self, stop, line: str):
        self.output_array.remove(self.postcmd.__name__)
        self.stdout.write("postcmd\n")
        return line
    
    # Synchronous hook methods derived from BaseCmd, should never be called in StrictAsyncCmd
    def preloop(self):
        raise NotImplementedError(f"Synchronous hook method {self.preloop.__name__} called in {StrictAsyncCmd.__name__}")
    def precmd(self, line: str):
        raise NotImplementedError(f"Synchronous hook method {self.precmd.__name__} called in {StrictAsyncCmd.__name__}")
    def postcmd(self, stop, line: str):
        raise NotImplementedError(f"Synchronous hook method {self.postcmd.__name__} called in {StrictAsyncCmd.__name__}")
    def postloop(self):
        raise NotImplementedError(f"Synchronous hook method {self.postloop.__name__} called in {StrictAsyncCmd.__name__}")
    
    # NOTE: BaseCmd's method cmdloop when inherited in StrictAsyncCmd already raises NotImplementedError
    # The reason hook methods are tested explicitly is because they are ideally never called in acmdloop

    @async_command
    async def exit(self, line: str) -> Literal[True]: return True
    @async_command
    async def foo(self, line: str) -> None: pass

