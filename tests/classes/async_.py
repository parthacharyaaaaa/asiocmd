import asyncio
from typing import Literal
from acmd import (AsyncCmd,
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