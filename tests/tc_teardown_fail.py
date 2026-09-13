"""Demonstrates a teardown that raises an exception.

The failure is caught and logged clearly, but it never blocks the next
testcase -- or the full-run teardown -- from running.

Run directly:      python -m unittest tests.tc_teardown_fail -v
"""

from tests import base_test


class TCTeardownFail(base_test.BaseTest):

    def setup(self):
        pass

    def test_execution(self):
        self.expectTrue(True, "Main logic runs fine")

    def teardown(self):
        raise RuntimeError("Simulated cleanup failure (e.g. connection already closed)")
