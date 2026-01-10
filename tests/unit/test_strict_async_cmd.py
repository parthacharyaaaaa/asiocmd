import pytest
from tests.conf import test_io
from tests.classes.strict_async import AsyncHookTestCmd
from acmd import StrictAsyncCmd

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