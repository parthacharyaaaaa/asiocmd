import inspect
from typing import Any, Callable, NoReturn, TextIO
import readline

from acmd.base_cmd import BaseCmd
from acmd.decorators import async_command
from acmd.typing import CmdMethod

__all__ = ("AsyncCmd",)

class AsyncCmd(BaseCmd):
    """
    Async+Sync implementation of `BaseCmd`
    """

    __slots__ = (
        'apreloop_first', 'aprecmd_first',
        'apostloop_first', 'apostcmd_first'
        )

    @staticmethod
    def check_async(method: Callable) -> bool:
        return inspect.iscoroutinefunction(inspect.unwrap(method))

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

        super().__init__(completekey, prompt, stdin, stdout, use_raw_input, intro, ruler, doc_header, misc_header, undoc_header)

    # Asynchronous hook methods
    async def aprecmd(self, line: str):
        """
        Asynchronous hook method executed just before the command line is
        interpreted, but after the input prompt is generated and issued.
        """
        return line
    
    async def apostcmd(self, stop, line: str):
        """
        Asynchronous hook method executed just after a command dispatch is finished.
        """
        return stop

    async def apreloop(self) -> Any:
        """
        Asynchronous hook method executed once when the acmdloop() method is called.
        """
        pass
    
    async def apostloop(self):
        """
        Asynchronous hook method executed once when the acmdloop() method is about to return.
        """
        pass

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
    
    # Synchronous command loop strictly not allowed
    def cmdloop(self) -> NoReturn:
        raise NotImplementedError(f"{self.__class__.__name__} does not allow synchronous command loop")

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
            if inspect.iscoroutinefunction(inspect.unwrap(method)):
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
        
    @async_command("help")
    async def async_do_help(self, arg: str) -> None:
        """
        List available commands with "help" or detailed help with "help cmd".
        """
        if arg:
            help_method: CmdMethod|None = self._helper_mapping.get(arg.strip())
            if not help_method:
                self.stdout.write(f"No help available for: {arg}")
                return
            
            if inspect.iscoroutinefunction(inspect.unwrap(help_method)):
                await help_method()
            else:
                help_method()
            return
        
        # Display help (if available) for all registered commands
        self.print_topics(self.doc_header, list(self._helper_mapping.keys()), 80)
        self.stdout.write("\n")
        self.print_topics(self.undoc_header, list(self._method_mapping.keys() - self._helper_mapping.keys()), 80)