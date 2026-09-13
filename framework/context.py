"""Active-testcase context.

This is what lets a helper module -- one that has no `self` reference to the
running testcase -- report `expectTrue`/`assertTrue` measurements that are
correctly attributed to whichever testcase is currently executing.

`BaseTest.setUp()` registers itself as the active testcase before calling the
author's `setup()`, and `BaseTest.tearDown()` clears it again once the
author's `teardown()` has finished running. Everything in between (setup,
test_execution, teardown, and any helper functions they call) sees the same
active testcase.

Implemented with `contextvars` rather than a plain module-level global so
that behavior stays correct if tests are ever run across multiple threads.
"""

import contextvars

_active_testcase = contextvars.ContextVar("active_testcase", default=None)


def set_active_testcase(testcase):
    """Mark `testcase` as the currently executing testcase. Returns a token
    that must be passed to `reset_active_testcase` when it finishes."""
    return _active_testcase.set(testcase)


def reset_active_testcase(token):
    """Clear the active testcase using the token from `set_active_testcase`."""
    _active_testcase.reset(token)


def get_active_testcase():
    """Return the currently executing testcase instance.

    Raises RuntimeError if called outside of a testcase's setup/execution/
    teardown -- this is a programming error in a helper module (e.g. calling
    it from module import time, or after the testcase has already finished).
    """
    testcase = _active_testcase.get()
    if testcase is None:
        raise RuntimeError(
            "expectTrue()/assertTrue() was called with no active testcase. "
            "Helper modules may only call these while a testcase's setup, "
            "test_execution, or teardown is actively running."
        )
    return testcase


def expectTrue(condition, message):
    """Module-level expectTrue for helper modules that don't have a `self`
    reference to the running testcase.

    Example (inside a helper module)::

        from framework import context as internal

        def helper_method_n():
            internal.expectTrue(some_condition, "Internal validation")

    Delegates to the currently active testcase, so the measurement is
    recorded and logged exactly as if the testcase itself had called it.
    """
    return get_active_testcase()._record_expect(bool(condition), message, from_helper=True)


def assertTrue(condition, message):
    """Module-level assertTrue for helper modules. See `expectTrue` above."""
    return get_active_testcase()._record_assert(bool(condition), message)
