from tests.conf import test_io
from tests.classes.base import RegistrarBaseCmd

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
