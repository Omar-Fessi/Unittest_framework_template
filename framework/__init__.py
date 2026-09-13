"""
Internal test-framework engine.

Nothing in this package is meant to be touched by testcase authors. It is
imported by `tests/base_test.py`, which is the only file testcase authors
need to know about (they subclass `BaseTest` from there).

Modules:
    exceptions.py -- internal control-flow exception(s)
    context.py    -- active-testcase tracking so helper modules can report
                     expectTrue()/assertTrue() without holding a reference
                     to the running testcase
    logger.py     -- timestamped, per-run .log file + colored console output
    results.py    -- data structures for expectTrue records and run-wide
                     statistics
    runner.py     -- once-per-process full-run setup/teardown lifecycle
"""
