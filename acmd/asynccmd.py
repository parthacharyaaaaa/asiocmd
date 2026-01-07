from typing import Any, TextIO
import readline

from acmd.strictasynccmd import StrictAsyncCmd

__all__ = ("AsyncCmd",)

class AsyncCmd(StrictAsyncCmd):
    """
    Async+Sync implementation of `BaseCmd`
    """

    __slots__ = (
        'preloop_async_first', 'async_precmd_first',
        'postloop_async_first', 'async_postcmd_first'
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
                 preloop_async_first: bool = False,
                 postloop_async_first: bool = False,
                 async_postcmd_first: bool = False,
                 async_precmd_first: bool = False):
        # Flags to determine whether async or sync hook methods need to be executed first
        self.preloop_async_first = preloop_async_first
        self.async_precmd_first = async_precmd_first
        self.async_postcmd_first = async_postcmd_first
        self.postloop_async_first = postloop_async_first

        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header)

    async def _preloop_wrapper(self) -> None:
        if self.preloop_async_first:
            await self.preloop_async()
            self.preloop()
        else:
            self.preloop()
            await self.preloop_async()
    
    async def _precmd_wrapper(self, line: str) -> str:
        if self.async_precmd_first:
            line = await self.precmd_async(line)
            return self.precmd(line)
        else:
            line = self.precmd(line)
            return await self.precmd_async(line)

    async def _postcmd_wrapper(self, stop: Any, line: str) -> None:
        if self.async_postcmd_first:
            stop = await self.postcmd_async(stop, line)
            return self.postcmd(stop, line)
        else:
            stop = self.postcmd(stop, line)
            return await self.postcmd_async(stop, line)

    async def _postloop_wrapper(self) -> None:
        if self.postloop_async_first:
            await self.postloop_async()
            self.postloop()
        else:
            self.postloop()
            await self.postloop_async()
    
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
            self.stdout.write(str(self.intro)+"\n")
        
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
