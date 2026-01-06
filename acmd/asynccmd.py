import inspect
from typing import Any, TextIO
import readline

from acmd.basecmd import CmdMethod
from acmd.strictasynccmd import StrictAsyncCmd

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

    def precmd(self, line: str):
        """
        Hook method executed just before the command line is
        interpreted, but after the input prompt is generated and issued.
        """
        return line

    async def precmd_async(self, line: str):
        """
        Asynchronous hook method executed just before the command line is
        interpreted, but after the input prompt is generated and issued.
        """
        return line

    def postcmd(self, stop, line: str):
        """
        Hook method executed just after a command dispatch is finished.
        """
        return stop
    
    async def postcmd_async(self, stop, line: str):
        """
        Asynchronous hook method executed just after a command dispatch is finished.
        """
        return stop

    def preloop(self):
        """
        Hook method executed once when the cmdloop() method is called.
        """
        pass

    async def preloop_async(self) -> Any:
        """
        Hook method executed once when the cmdloop() method is called.
        """
        pass

    def postloop(self):
        """
        Hook method executed once when the cmdloop() method is about to return.
        """
        pass
    
    async def postloop_async(self):
        """
        Hook method executed once when the cmdloop() method is about to return.
        """
        pass

    def parseline(self, line: str) -> tuple[str|None, str|None, str]:
        """
        Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                line = 'shell ' + line[1:]
            else:
                return None, None, line

        for i in range(len(line)):
            if line[i] not in self.identchars:
                return line[:i], line[i:], line
        return line, "", line
    
    async def onecmd(self, line: str):
        """
        Interpret the argument as though it had been typed in response to the prompt.

        This may be overridden, but should not normally need to be;
        see the precmd() and postcmd() methods for useful execution hooks.
        The return value is a flag indicating whether interpretation of
        commands by the interpreter should stop.

        """
        cmd, arg, line = self.parseline(line)
        if not line:
            return await self.emptyline()
        if cmd is None:
            return self.default(line)
        self.lastcmd = line
        if line == 'EOF' :
            self.lastcmd = ''
        if cmd == '':
            return self.default(line)
        else:
            method: CmdMethod|None = self._method_mapping.get(cmd)
            if not method:
                return self.default(line)
            if inspect.iscoroutinefunction(method):
                return await method(arg)
            return method(arg)

    async def emptyline(self):
        """
        Called when an empty line is entered in response to the prompt.

        If this method is not overridden, it repeats the last nonempty
        command entered.
        """
        if self.lastcmd:
            return await self.onecmd(self.lastcmd)
