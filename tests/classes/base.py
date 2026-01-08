'''Class definitions for testing BaseCmd functionality'''

from acmd import BaseCmd, command, command_helper

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