import asyncio
import inspect
from typing import Callable
import pytest
from tests.conf import test_io
from tests.classes.strict_async import AsyncHookTestCmd, AsyncCommandCmd
from acmd import StrictAsyncCmd

from unittest.mock import patch

def test_loop(test_io):
    stdin, stdout = test_io
    cmd: StrictAsyncCmd = StrictAsyncCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    failed: bool = False
    try:
        cmd.cmdloop()
    except NotImplementedError:
        failed = True
    finally:
        assert failed, \
        f"{StrictAsyncCmd.__name__} failed to raise error on calling sync loop {StrictAsyncCmd.cmdloop.__name__}"

@pytest.mark.asyncio
async def test_hooks(test_io):
    stdin, stdout = test_io
    hook_cmd: AsyncHookTestCmd = AsyncHookTestCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    stdin.write("\n".join(("foo", "exit")))
    stdin.seek(0)

    await hook_cmd.acmdloop()
    assert not hook_cmd.output_array, \
    f"Hook method(s) ({', '.join(str(i) for i in hook_cmd.output_array)}) not invoked"

    output_lines: list[str] = stdout.getvalue().split("\n")
    # Check order of hook methods, which should be
    # 1) preloop
    # 2) Intro
    # 3) Prompt + precmd
    # 4) postcmd
    # 5) postloop
    
    assert len(output_lines) == 5, \
    "Unexpected output captured, does not match expected stdout sequence"

    output_lines[2] = output_lines[2].split()[1]    # Remove prompt from #3 
    output_lines.pop(1) # Remove captured intro
    
    for hook_output in ("preloop", "precmd", "postcmd", "postloop"):
        assert hook_output == output_lines.pop(0), \
        "Unexpected output captured, does not match expected stdout sequence"

def test_commands_registration(test_io):
    stdin, stdout = test_io
    cmd: AsyncCommandCmd = AsyncCommandCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    # Ensure that no synchronous methods are registered, and given async commands are registered
    sync_commands: dict[str, Callable] = {}
    async_commands: set[str] = {"afoo", "network_io", "exit", "help"}
    async_helpers: set[str] = {"afoo", "network_io"}

    for name, method in cmd._method_mapping.items():
        if not inspect.iscoroutinefunction(method) and name not in cmd._ignored_sync_methods:
            sync_commands[name] = method
        assert name in async_commands, \
            f"Async command {name} not registered"
    
    assert not (diff:=async_helpers - cmd._helper_mapping.keys()), \
        f"Unregistered helpers: {', '.join(diff)}"

    if sync_commands:
        raise NotImplementedError(f"Methods ({', '.join(name for name in sync_commands.keys())}) are synchronous and not supported by {StrictAsyncCmd.__name__}")
    
@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_command_functionality(mock_open_connection, test_io):
    stdin, stdout = test_io
    cmd: AsyncCommandCmd = AsyncCommandCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    mock_host, mock_port = "localhost", 8080

    # 3-tuples of command, arguments, and expected stdout
    commands: tuple[tuple[str, str, str], ...] = (
        ("afoo", "", "afoo"),
        ("help", "afoo", "afoo_helper"),
        ("network_io", f"{mock_host}:{mock_port}", "mock_io"),
        ("help", "network_io", "io_helper"),
        ("exit", "", "exit")
    )
    
    stdin.write("\n".join(f"{command}{arg if not arg else ' '+arg}" for command, arg, _ in commands))
    stdin.seek(0)

    await cmd.acmdloop()

    # Check if network I/O was awaited
    mock_open_connection.assert_awaited_with(host=mock_host, port=mock_port)

    stdout.seek(0)

    output_lines: list[str] = [line.strip("\n ").split()[1]
                               for line in stdout.readlines()[1:]]    # Exclude cmd intro
    for index, line in enumerate(output_lines):
        # Match stdout with expected outputs
        assert line == commands[index][2], \
        f"Unexpected output for command {commands[index][0]}"
