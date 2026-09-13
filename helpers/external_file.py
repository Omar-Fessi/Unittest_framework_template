"""Example external/helper module.

Helper modules never need a reference to the currently running testcase --
they just import the framework's context-aware `expectTrue`/`assertTrue` and
call them directly, exactly like a testcase would call `self.expectTrue(...)`.
The framework automatically attributes these calls to whichever testcase is
currently executing, and they show up in that testcase's log and final
result as if they'd been called directly from the testcase file.

    from framework import context as internal

    def helper_method_n():
        internal.expectTrue(some_condition, "Internal validation")
"""

from framework import context as internal


def helper_method_n():
    """Pretend this does some real work on behalf of the calling testcase,
    then reports what it found back to the active testcase."""
    condition_3 = False  # e.g. a downstream service check that failed
    condition_4 = True  # e.g. a downstream service check that passed

    internal.expectTrue(condition_3, "Internal validation 3")
    internal.expectTrue(condition_4, "Internal validation 4")


def verify_connection_alive(connection):
    """Another example: a helper that both gates (assertTrue) and measures
    (expectTrue) using data passed in from the calling testcase."""
    internal.assertTrue(connection is not None, "Connection object must exist")
    internal.expectTrue(connection.get("alive", False), "Connection reports alive")
