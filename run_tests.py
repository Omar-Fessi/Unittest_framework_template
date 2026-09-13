#!/usr/bin/env python3
"""Convenience entry point for running the test suite.

    python run_tests.py                  # run every tc_*.py under tests/
    python run_tests.py tests.tc_login   # run a single module
    python run_tests.py tests.tc_login.TCLogin.test_execution   # single test

Full-run setup/teardown and the timestamped .log file are handled
automatically by the framework the moment the first testcase starts -- this
script doesn't need to know anything about that.
"""

import sys
import unittest


def main():
    argv = sys.argv[1:]
    loader = unittest.TestLoader()

    if argv:
        suite = loader.loadTestsFromNames(argv)
    else:
        suite = loader.discover(start_dir="tests", pattern="tc_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
