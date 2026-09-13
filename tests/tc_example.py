"""Example testcase demonstrating expectTrue calls made both directly by the
testcase AND indirectly through an external helper module. One of the
helper's measurements deliberately fails, so the final testcase result is
FAILED even though every individual step still runs to completion.

Run directly:      python -m unittest tests.tc_example -v
Debug in VS Code:  open this file, use "Debug: Current Testcase File"
"""

from helpers import external_file
from tests import base_test


class TCExample(base_test.BaseTest):

    def setup(self):
        self.connection = {"ready": True, "alive": True}
        self.assertTrue(self.connection is not None, "Connection must be initialized")

    def test_execution(self):
        self.expectTrue(True, "Login succeeds")
        self.expectTrue(True, "User profile loads")

        # This helper reports two more expectTrue measurements on our
        # behalf -- one of which fails. Execution continues regardless.
        external_file.helper_method_n()

        self.expectTrue(True, "Session token is valid")
        self.expectTrue(True, "Response time is acceptable")

    def teardown(self):
        self.connection = None
