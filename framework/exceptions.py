"""Internal exceptions used to drive testcase control flow.

Testcase authors never need to import or catch these directly -- they are
raised and handled entirely inside `tests/base_test.py`.
"""


class AssertionAbort(Exception):
    """Raised internally when `assertTrue()` fails.

    This aborts the remainder of the current testcase's setup/execution flow
    (the framework guarantees `teardown()` still runs), but never propagates
    out to unittest itself -- `BaseTest` catches it and routes execution to
    teardown, then moves on to the next testcase.
    """
