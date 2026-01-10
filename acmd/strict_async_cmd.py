import inspect
from typing import Any, Callable, NoReturn, Sequence, TextIO

from acmd.base_cmd import BaseCmd
from acmd.decorators import async_command, COMMAND_ATTR, HELPER_ATTR
from acmd.typing import CmdMethod, SupportsContains

import readline

__all__ = ("StrictAsyncCmd",)

class StrictAsyncCmd(BaseCmd):
    """
    Strictly asynchronous implementation of `BaseCmd`
    """
    
    __slots__ = ('_ignored_sync_methods',)

    # Synchronous methods strictly not allowed
    def cmdloop(self) -> NoReturn:
        raise NotImplementedError(f"{self.__class__.__name__} does not allow synchronous command loop")

    @staticmethod
    def check_async(method: Callable) -> bool:
        return inspect.iscoroutinefunction(method)

    def _update_mapping(self, overwrite: bool) -> None:
        if overwrite:
            self._method_mapping.clear()
            self._helper_mapping.clear()
        
        illegal_sync_commands: list[str] = []
        for name, method in inspect.getmembers(self, inspect.ismethod):
            cmdname = getattr(method, COMMAND_ATTR, None)
            helpname = getattr(method, HELPER_ATTR, None)

            if cmdname and helpname:
                raise ValueError(f"Method {name} ({repr(method)}) cannot be both a command and a helper")

            # NOTE: If a command has a docstring AND a dedicated helper method, then the latter will be given priority

            if cmdname is not None: # Method decorated with @command or @async_command
                if not (StrictAsyncCmd.check_async(method) or name in self._ignored_sync_methods):
                    illegal_sync_commands.append(name)
                    continue

                self._method_mapping[cmdname] = method
                if docs:=inspect.cleandoc(method.__doc__ or ''):
                    self._helper_mapping.setdefault(cmdname, lambda d=docs : self.stdout.write(d))
            
            elif name.startswith("do_"):  # Legacy method, defined as do_*()
                name = name[3:]
                if not (StrictAsyncCmd.check_async(method) or name in self._ignored_sync_methods):
                    illegal_sync_commands.append(name)
                    continue

                # Commands defined with decorators are prioritised over legacy commands of the same name
                self._method_mapping.setdefault(name, method)
                if docs:=inspect.cleandoc(method.__doc__ or ''):
                    self._helper_mapping.setdefault(name, lambda d=docs : self.stdout.write(d))
            
            # NOTE: Helper methods are allowed to be synchronous
            elif helpname is not None: # Method decorated with @command_helper or @async_command_helper
                self._helper_mapping[helpname] = method
            elif name.startswith("help_"):  # Legacy method for help, defined as help_*()
                self._helper_mapping.setdefault(name[5:], method)

        if illegal_sync_commands:
            raise NotImplementedError(f"Registered sync commands ({', '.join(illegal_sync_commands)}) identified")

        if difference := (self._helper_mapping.keys() - self._method_mapping.keys()):
            raise ValueError(f"helpers: ({', '.join(difference)}) are defined for non-existent methods")

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
                 undoc_header: str = "Undocumented commands:"):
        self._ignored_sync_methods = ("help",)
        super().__init__(completekey, prompt,
                         stdin, stdout,
                         use_raw_input,
                         intro, ruler,
                         doc_header, misc_header, undoc_header)
            
    async def acmdloop(self):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """
        await self.apreloop()
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
            
            line = await self.aprecmd(line)
            stop = await self.onecmd(line)
            stop = await self.apostcmd(stop, line)
        await self.apostloop()

        if self.use_rawinput and self.completekey:
            readline.set_completer(self.old_completer)

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
            
            if inspect.iscoroutinefunction(help_method):
                await help_method()
            else:
                help_method()
            return
        
        # Display help (if available) for all registered commands
        self.print_topics(self.doc_header, list(self._helper_mapping.keys()), 80)
        self.stdout.write("\n")
        self.print_topics(self.undoc_header, list(self._method_mapping.keys() - self._helper_mapping.keys()), 80)