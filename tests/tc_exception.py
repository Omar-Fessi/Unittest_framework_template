"""Demonstrates an unhandled Python exception during test_execution.

The framework logs this distinctly from an expectTrue failure (it's an
[ERROR], not an [EXPECT] FAIL), still runs teardown, and moves on to the
next testcase.

Run directly:      python -m unittest tests.tc_exception -v
"""

from tests import base_test


class TCException(base_test.BaseTest):

    def setup(self):
        self.divisor = 0

    def test_execution(self):
        self.expectTrue(True, "Step before the crash")
        result = 10 / self.divisor  # raises ZeroDivisionError
        self.expectTrue(True, "Step after the crash (never reached)")

    def teardown(self):
        # Still runs even though test_execution raised.
        self.divisor = None
