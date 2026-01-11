from typing import Any, TextIO
import readline

from acmd.strict_async_cmd import StrictAsyncCmd

__all__ = ("AsyncCmd",)

class AsyncCmd(StrictAsyncCmd):
    """
    Async+Sync implementation of `BaseCmd`
    """

    __slots__ = (
        'apreloop_first', 'aprecmd_first',
        'apostloop_first', 'apostcmd_first'
        )

    def __init__(self,
                 completekey: str = 'tab',
                 prompt: str | None = None,
                 stdin: TextIO | Any | None = None,
                 stdout: TextIO | Any | None = None,
                 use_raw_input: bool = True,
                 intro: str | None = None,
                 ruler: str = "=",
                 doc_header: str = "Documented commands (type help <topic>):",
                 misc_header: str = "Miscellaneous help topics:",
                 undoc_header: str = "Undocumented commands:",
                 apreloop_first: bool = False,
                 apostloop_first: bool = False,
                 apostcmd_first: bool = False,
                 aprecmd_first: bool = False):
        # Flags to determine whether async or sync hook methods need to be executed first
        self.apreloop_first = apreloop_first
        self.aprecmd_first = aprecmd_first
        self.apostcmd_first = apostcmd_first
        self.apostloop_first = apostloop_first

        super(StrictAsyncCmd, self).__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header,
                                             auto_register=False)
        super(StrictAsyncCmd, self)._update_mapping(False)

    async def _preloop_wrapper(self) -> None:
        if self.apreloop_first:
            await self.apreloop()
            return self.preloop()
        self.preloop()
        return await self.apreloop()
    
    async def _precmd_wrapper(self, line: str) -> str:
        if self.aprecmd_first:
            line = await self.aprecmd(line)
            return self.precmd(line)
        line = self.precmd(line)
        return await self.aprecmd(line)

    async def _postcmd_wrapper(self, stop: Any, line: str) -> Any:
        if self.apostcmd_first:
            stop = await self.apostcmd(stop, line)
            return self.postcmd(stop, line)
        stop = self.postcmd(stop, line)
        return await self.apostcmd(stop, line)

    async def _postloop_wrapper(self) -> None:
        if self.apostloop_first:
            await self.apostloop()
            return self.postloop()
        self.postloop()
        return await self.apostloop()
    
    async def acmdloop(self):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """
        await self._preloop_wrapper()
        if self.use_rawinput and self.completekey:
            self.old_completer = readline.get_completer()
            readline.set_completer(self.complete)
            if readline.backend == "editline":
                if self.completekey == 'tab':
                    # libedit uses "^I" instead of "tab"
                    command_string = "bind ^I rl_complete"
                else:
                    command_string = f"bind {self.completekey} rl_complete"
            else:
                command_string = f"{self.completekey}: complete"
            readline.parse_and_bind(command_string)
        
        if self.intro:
            self.stdout.write(self.intro)
        
        stop = None
        while not stop:
            if self.cmdqueue:
                line = self.cmdqueue.pop(0)
            else:
                if self.use_rawinput:
                    try:
                        line = input(self.prompt)
                    except EOFError:
                        line = 'EOF'
                else:
                    self.stdout.write(self.prompt)
                    self.stdout.flush()
                    line = self.stdin.readline()
                    if not len(line):
                        line = 'EOF'
                    else:
                        line = line.rstrip('\r\n')
            
            line = await self._precmd_wrapper(line)
            stop = await self.onecmd(line)
            stop = await self._postcmd_wrapper(stop, line)
        await self._postloop_wrapper()
        if self.use_rawinput and self.completekey:
            readline.set_completer(self.old_completer)
