from typing import Literal
import pytest
from tests.conf import test_io
import io
from acmd import AsyncCmd
from tests.classes.async_ import AsyncTestCmd, AsyncHookCmd, AsyncDecoratorCmd
from unittest.mock import patch

def test_loop(test_io) -> None:
    stdin, stdout = test_io
    cmd: AsyncCmd = AsyncCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    failed: bool = False
    try:
        cmd.cmdloop()
    except NotImplementedError:
        failed = True
    
    assert failed, \
        "AsyncCmd failed to reject sync cmdloop"

def _get_output(kwarg: Literal["apreloop_first", "aprecmd_first", "apostcmd_first", "apostloop_first"],
                  flag: bool) -> tuple[str, str]:
    if kwarg == "apreloop_first":
        return (
            (AsyncHookCmd.apreloop.__name__, AsyncHookCmd.preloop.__name__)
            if flag
            else (AsyncHookCmd.preloop.__name__, AsyncHookCmd.apreloop.__name__)
        )

    elif kwarg == "aprecmd_first":
        return (
            (AsyncHookCmd.aprecmd.__name__, AsyncHookCmd.precmd.__name__)
            if flag
            else (AsyncHookCmd.precmd.__name__, AsyncHookCmd.aprecmd.__name__)
        )

    elif kwarg == "apostcmd_first":
        return (
            (AsyncHookCmd.apostcmd.__name__, AsyncHookCmd.postcmd.__name__)
            if flag
            else (AsyncHookCmd.postcmd.__name__, AsyncHookCmd.apostcmd.__name__)
        )

    elif kwarg == "apostloop_first":
        return (
            (AsyncHookCmd.apostloop.__name__, AsyncHookCmd.postloop.__name__)
            if flag
            else (AsyncHookCmd.postloop.__name__, AsyncHookCmd.apostloop.__name__)
        )

@pytest.mark.asyncio
async def test_hooks() -> None:
    output_stream: str = "exit"

    hook_kwargs: list[str] = ["apreloop_first", "aprecmd_first", "apostcmd_first", "apostloop_first"]
    for b in range(0, 0b10000):
        kwarg_combination: dict[str, bool] = {hook_kwarg : bool(b & (2**i))
                                              for i, hook_kwarg
                                              in enumerate(hook_kwargs)}
        expected_outputs: list[str] = [expected_output
                                       for kwarg, flag in kwarg_combination.items()
                                       for expected_output in _get_output(kwarg, flag)]  # pyright: ignore[reportArgumentType]
        
        stdin, stdout = io.StringIO(), io.StringIO()
        acmd: AsyncHookCmd = AsyncHookCmd(stdin=stdin, stdout=stdout, use_raw_input=False,
                                          apreloop_first=kwarg_combination["apreloop_first"],
                                          aprecmd_first=kwarg_combination["aprecmd_first"],
                                          apostcmd_first=kwarg_combination["apostcmd_first"],
                                          apostloop_first=kwarg_combination["apostloop_first"])

        stdin.write(output_stream)
        stdin.seek(0)
        await acmd.acmdloop()
        assert acmd.order_list == expected_outputs, \
            f'''Unexpected outputs for hook methods
            Hook flags: {kwarg_combination},
            Expected Output: {', '.join(expected_outputs)},
            Observed output: {', '.join(acmd.order_list)}'''

@pytest.mark.asyncio
@patch("asyncio.open_connection")
async def test_functionality(mock_aio, test_io) -> None:
    stdin, stdout = test_io
    cmd: AsyncTestCmd = AsyncTestCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    host, port = 'localhost', 8080

    commands: tuple[tuple[str,str,str], ...] = (
        ("foo", "", cmd.foo.__name__),
        ("afoo", "", cmd.afoo.__name__),
        ("bar", "", cmd.do_bar.__name__),
        ("io", f"{host}:{port}", cmd.io.__name__),
        ("help", "bar", cmd.help_bar.__name__),
        ("help", "foo", cmd.foo_helper.__name__),
        ("help", "io", cmd.io_helper.__name__),
        ("exit", "", cmd.do_exit.__name__)
    )

    stdin.write("\n".join(f"{command}{arg if not arg else ' '+arg}" for command, arg, _ in commands))
    stdin.seek(0)

    await cmd.acmdloop()

    mock_aio.assert_awaited_with(host=host, port=port)

    stdout.seek(0)
    output_lines: list[str] = [line.strip("\n ").split()[1]
                               for line in stdout.readlines()[1:]]    # Exclude cmd intro
    
    for index, line in enumerate(output_lines):
        # Match stdout with expected outputs
        assert line == commands[index][2], \
        f"Unexpected output for command {commands[index][0]}"

@pytest.mark.asyncio
async def test_cmd_decorators(test_io):
    stdin, stdout = test_io
    cmd: AsyncDecoratorCmd = AsyncDecoratorCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    expected_outputs: list[str] = [cmd.foo.__name__, cmd.abc.__name__,
                                   cmd.do_bar.__name__, cmd.help_bar.__name__, cmd.reversed_foo.__name__,
                                   cmd.afoo.__name__, cmd.aabc.__name__, cmd.do_abar.__name__,
                                   cmd.help_abar.__name__, cmd.areversed_foo.__name__]
    stdin.write("\n".join(["foo", "help foo", "bar", "help bar", "rfoo",
                           "afoo", "help afoo", "abar", "help abar", "arfoo",
                           "exit"]))
    stdin.seek(0)

    await cmd.acmdloop()

    assert cmd.method_decorator_calls == expected_outputs, \
        f'''Expected output not found
        Expected: ({', '.join(expected_outputs)})
        Observed: ({', '.join(cmd.method_decorator_calls)})'''