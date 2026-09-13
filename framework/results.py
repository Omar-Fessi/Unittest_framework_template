"""Data structures for expectTrue measurements and run-wide statistics."""

import threading
from dataclasses import dataclass, field
from enum import Enum


class TCStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    ERROR = "ERROR"
    NO_MEASUREMENTS = "NO_MEASUREMENTS"


@dataclass
class ExpectRecord:
    tc_name: str
    passed: bool
    message: str
    timestamp: str
    elapsed: float
    source: str


@dataclass
class TCReport:
    name: str
    duration: float = 0.0
    expect_records: list = field(default_factory=list)
    status: TCStatus = TCStatus.PASSED
    reason: str = ""
    had_teardown_error: bool = False


class RunStats:
    """Aggregates every testcase's report across a single test run.

    A single lock is enough here: unittest's default runner executes
    testcases sequentially, so contention is minimal. If testcases are ever
    run concurrently, this still keeps `add_report` safe.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.tc_reports = []

    def add_report(self, report):
        with self._lock:
            self.tc_reports.append(report)

    def summary(self):
        with self._lock:
            reports = list(self.tc_reports)

        total_expect = sum(len(r.expect_records) for r in reports)
        expect_passed = sum(1 for r in reports for e in r.expect_records if e.passed)

        return {
            "total": len(reports),
            "passed": sum(1 for r in reports if r.status == TCStatus.PASSED),
            "failed": sum(1 for r in reports if r.status == TCStatus.FAILED),
            "aborted": sum(1 for r in reports if r.status == TCStatus.ABORTED),
            "errors": sum(1 for r in reports if r.status == TCStatus.ERROR),
            "no_measurements": sum(1 for r in reports if r.status == TCStatus.NO_MEASUREMENTS),
            "teardown_errors": sum(1 for r in reports if r.had_teardown_error),
            "total_expect": total_expect,
            "expect_passed": expect_passed,
            "expect_failed": total_expect - expect_passed,
        }


_run_stats = RunStats()


def get_run_stats():
    return _run_stats
