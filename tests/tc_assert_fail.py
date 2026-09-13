"""Demonstrates assertTrue aborting a testcase during setup.

Because the precondition fails, `test_execution` never runs at all -- but
`teardown` still runs (cleanup is guaranteed), and the framework moves on to
the next testcase without interruption.

Run directly:      python -m unittest tests.tc_assert_fail -v
"""

from tests import base_test


class TCAssertFail(base_test.BaseTest):

    def setup(self):
        self.resource = None
        # Deliberately fails: no resource was ever acquired.
        self.assertTrue(self.resource is not None, "Resource must be available before running")

    def test_execution(self):
        # Never reached -- assertTrue above already aborted the testcase.
        self.expectTrue(True, "This should never run")

    def teardown(self):
        # Still runs even though setup aborted, so cleanup is guaranteed.
        self.resource = "cleaned"
