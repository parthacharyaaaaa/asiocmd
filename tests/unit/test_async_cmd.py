import pytest
from tests.conf import test_io
from acmd import AsyncCmd
from tests.classes.async_ import AsyncTestCmd
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