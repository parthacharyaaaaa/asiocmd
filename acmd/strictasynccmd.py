import inspect
from typing import Any, NoReturn

from acmd.basecmd import BaseCmd, CmdMethod
from acmd.decorators import async_command

import readline

__all__ = ("StrictAsyncCmd",)

class StrictAsyncCmd(BaseCmd):
    """
    Strictly asynchronous implementation of `BaseCmd`
    """
    
    # Synchronous methods strictly not allowed
    def cmdloop(self) -> NoReturn:
        raise NotImplementedError(f"{self.__class__.__name__} does not allow synchronous command loop")

    async def acmdloop(self):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """
        await self.preloop_async()
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
            
            line = await self.precmd_async(line)
            stop = await self.onecmd(line)
            stop = await self.postcmd_async(stop, line)
        await self.postloop_async()

        if self.use_rawinput and self.completekey:
            readline.set_completer(self.old_completer)

    async def precmd_async(self, line: str):
        """
        Asynchronous hook method executed just before the command line is
        interpreted, but after the input prompt is generated and issued.
        """
        return line
    
    async def postcmd_async(self, stop, line: str):
        """
        Asynchronous hook method executed just after a command dispatch is finished.
        """
        return stop

    async def preloop_async(self) -> Any:
        """
        Asynchronous hook method executed once when the acmdloop() method is called.
        """
        pass
    
    async def postloop_async(self):
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
        self.print_topics(self.undoc_header, list(self._method_mapping.keys() - self._helper_mapping.keys()), 80)
