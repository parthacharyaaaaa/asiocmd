from tests.conf import test_io
from tests.classes.base import RegistrarBaseCmd, EchoCmd, HookCmd

def test_base_cmd_registration(test_io):
    stdin, stdout = test_io
    test_cmd: RegistrarBaseCmd = RegistrarBaseCmd(stdin=stdin, stdout=stdout)
    
    assert "unregistered" not in test_cmd._method_mapping, \
    "Method not prefixed with do_ and not decorated with command registered in test_cmd"

    # Invariant: There should exist no helper methods for unregistered command functions
    assert not (leftover_helpers:=(test_cmd._helper_mapping.keys() - test_cmd._method_mapping.keys())), \
    f"Helper method(s) {', '.join(leftover_helpers)} declared for unregistered command methods"

    methods: list[str] = ["foo", "bar", "stuff"]
    unregistered_methods: list[str] = [method for method in methods if method not in test_cmd._method_mapping]
    assert not unregistered_methods, \
    f"Method(s) ({', '.join(unregistered_methods)}) decorated with @command or prefixed with do_ not registered"

    unregistered_helpers: list[str] = [method for method in methods if method not in test_cmd._helper_mapping]
    assert not unregistered_helpers, \
    f"Helper method(s) ({', '.join(unregistered_helpers)}) decorated with @command_helper or prefixed with help_ not registered"

def test_base_cmd_io(test_io):
    stdin, stdout = test_io
    test_cmd: EchoCmd = EchoCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    echo_string: str = "Echoed String"
    stdin.write(f"echo {echo_string}\nexit\n")
    stdin.seek(0)

    test_cmd.cmdloop()

    stdout.seek(len(test_cmd.intro) + len(test_cmd.prompt) + 1) # CLI intro, prompt, and spacing

    assert stdout.readline().rstrip("\n") == echo_string, "Echo failed"

def test_base_cmd_hooks(test_io):
    stdin, stdout = test_io
    hook_cmd: HookCmd = HookCmd(stdin=stdin, stdout=stdout, use_raw_input=False)

    stdin.write("\n".join(("foo", "exit")))
    stdin.seek(0)

    hook_cmd.cmdloop()
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
    