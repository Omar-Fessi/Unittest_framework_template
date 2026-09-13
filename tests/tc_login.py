"""Simplest possible example: everything passes.

Run directly:      python -m unittest tests.tc_login -v
Debug in VS Code:  open this file, use "Debug: Current Testcase File"
"""

from tests import base_test


class TCLogin(base_test.BaseTest):

    def setup(self):
        self.username = "demo_user"
        self.assertTrue(bool(self.username), "Username must be provided before login")

    def test_execution(self):
        self.expectTrue(len(self.username) > 0, "Username is non-empty")
        self.expectTrue(self.username.islower(), "Username is lowercase")

    def teardown(self):
        self.username = None
