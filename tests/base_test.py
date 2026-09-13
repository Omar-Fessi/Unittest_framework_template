"""BaseTest -- the one framework file testcase authors need to know about.

Subclass this, implement `setup`, `test_execution`, and `teardown`, and
nothing else. Do NOT call `super().setup()`, `super().teardown()`, or any
other framework method -- the full lifecycle (logging, expectTrue/assertTrue
bookkeeping, error isolation, teardown guarantees, result aggregation) is
handled automatically underneath you.

    class TCExample(BaseTest):

        def setup(self):
            self.connection = create_connection()
            self.assertTrue(self.connection is not None,
                             "Connection must be initialized")

        def test_execution(self):
            self.expectTrue(self.connection.is_ready(), "Connection is ready")
            external_file.helper_method_n(self)
            self.expectTrue(self.connection.is_alive(), "Connection remains alive")

        def teardown(self):
            if self.connection:
                self.connection.close()

See the project README for the full lifecycle explanation and the
expectTrue vs. assertTrue distinction.
"""

import inspect
import time
import traceback
import unittest

from framework.context import get_active_testcase, reset_active_testcase, set_active_testcase
from framework.exceptions import AssertionAbort
from framework.logger import get_logger
from framework.results import ExpectRecord, TCReport, TCStatus, get_run_stats
from framework.runner import ensure_run_initialized


class BaseTest(unittest.TestCase):
    """Reusable unittest base class. See module docstring for usage."""

    # ------------------------------------------------------------------
    # hooks testcase authors override -- harmless no-ops by default so a
    # testcase that only needs some of the three still works fine
    # ------------------------------------------------------------------
    def setup(self):
        """Testcase-specific setup. Override in your testcase."""
        pass

    def test_execution(self):
        """Main testcase logic. Override in your testcase.

        If a subclass doesn't override this at all, the framework reports a
        clear NO_MEASUREMENTS result rather than silently marking the
        testcase as passed (see README: "result calculation").
        """
        pass

    def teardown(self):
        """Testcase-specific cleanup. Override in your testcase."""
        pass

    # ------------------------------------------------------------------
    # This is the trick that lets authors literally name their method
    # `test_execution` (matching unittest's "test*" discovery convention)
    # while still getting framework-managed abort/exception handling around
    # it, with zero boilerplate and no super() calls required.
    # ------------------------------------------------------------------
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "test_execution" in cls.__dict__:
            original = cls.__dict__["test_execution"]

            def _wrapped(self, _original=original):
                if self._aborted or self._unexpected_exception is not None:
                    reason = self._abort_reason or str(self._unexpected_exception)
                    self._logger.execution_skipped(self._tc_name, reason)
                    return
                self._logger.execution_start(self._tc_name)
                try:
                    _original(self)
                except AssertionAbort as exc:
                    self._aborted = True
                    self._abort_reason = str(exc)
                    self._logger.execution_skipped(self._tc_name, f"assertTrue failed mid-execution: {exc}")
                except Exception as exc:  # noqa: BLE001 - intentional broad catch
                    self._unexpected_exception = exc
                    self._unexpected_phase = "test_execution"
                    self._logger.exception(self._tc_name, "test_execution", exc, traceback.format_exc())
                else:
                    self._logger.execution_done(self._tc_name)

            _wrapped.__name__ = "test_execution"
            _wrapped.__doc__ = getattr(original, "__doc__", None)
            cls.test_execution = _wrapped

    # ------------------------------------------------------------------
    # framework-managed unittest lifecycle -- testcase authors never touch
    # setUp()/tearDown() directly; they exist only to host the lifecycle
    # guarantees below.
    # ------------------------------------------------------------------
    def setUp(self):
        ensure_run_initialized()

        self._logger = get_logger()
        self._tc_name = type(self).__name__
        self._expect_records = []
        self._aborted = False
        self._abort_reason = ""
        self._unexpected_exception = None
        self._unexpected_phase = None
        self._teardown_exception = None
        self._start_time = time.perf_counter()

        self._logger.tc_start(self._tc_name)
        self._ctx_token = set_active_testcase(self)

        self._logger.setup_start(self._tc_name)
        try:
            self.setup()
        except AssertionAbort as exc:
            self._aborted = True
            self._abort_reason = str(exc)
        except Exception as exc:  # noqa: BLE001
            self._unexpected_exception = exc
            self._unexpected_phase = "setup"
            self._logger.exception(self._tc_name, "setup", exc, traceback.format_exc())
        else:
            self._logger.setup_done(self._tc_name)

        # NOTE: setUp() never raises, by design. If it did, unittest would
        # skip tearDown() entirely -- and this framework's core guarantee is
        # that teardown always runs once a testcase has started.

    def tearDown(self):
        self._logger.teardown_start(self._tc_name)
        try:
            self.teardown()
        except Exception as exc:  # noqa: BLE001
            self._teardown_exception = exc
            self._logger.teardown_error(self._tc_name, exc, traceback.format_exc())
        else:
            self._logger.teardown_done(self._tc_name)
        finally:
            reset_active_testcase(self._ctx_token)

        self._finalize()

    # ------------------------------------------------------------------
    # expectTrue / assertTrue
    # ------------------------------------------------------------------
    def expectTrue(self, condition, message):
        """Record a measurement.

        This NEVER stops execution, regardless of pass/fail -- it is purely
        a recorded data point. The testcase's final result is the logical
        AND of every expectTrue call made during it (directly or via
        helpers).
        """
        return self._record_expect(bool(condition), message, from_helper=False)

    def assertTrue(self, condition, message):
        """Validate a precondition.

        On failure, this aborts the rest of the current testcase's
        setup/execution (teardown still runs, and the next testcase is
        unaffected). Use this for "is it safe to continue" checks, not for
        measuring the behavior under test -- that's what expectTrue is for.
        """
        return self._record_assert(bool(condition), message)

    def _record_expect(self, condition, message, from_helper):
        source = None
        if from_helper:
            # stack: [0]=_record_expect [1]=framework.context.expectTrue [2]=actual caller
            caller = inspect.stack()[2]
            module_name = caller.frame.f_globals.get("__name__", "?")
            source = f"{module_name}.{caller.function}"

        record = ExpectRecord(
            tc_name=self._tc_name,
            passed=condition,
            message=message,
            timestamp=self._logger.now(),
            elapsed=time.perf_counter() - self._start_time,
            source=source or "testcase",
        )
        self._expect_records.append(record)
        self._logger.expect(self._tc_name, condition, message, source=source)
        return condition

    def _record_assert(self, condition, message):
        self._logger.assertion(self._tc_name, condition, message)
        if not condition:
            raise AssertionAbort(message)
        return condition

    # ------------------------------------------------------------------
    # result aggregation
    # ------------------------------------------------------------------
    def _finalize(self):
        duration = time.perf_counter() - self._start_time
        report = TCReport(name=self._tc_name, duration=duration, expect_records=self._expect_records)

        if self._unexpected_exception is not None:
            report.status = TCStatus.ERROR
            report.reason = (
                f"Unhandled {type(self._unexpected_exception).__name__} during "
                f"{self._unexpected_phase}: {self._unexpected_exception}"
            )
        elif self._aborted:
            report.status = TCStatus.ABORTED
            report.reason = f"assertTrue failed: {self._abort_reason}"
        elif not self._expect_records:
            report.status = TCStatus.NO_MEASUREMENTS
            report.reason = "No expectTrue measurements were collected -- check the testcase/helper wiring."
        elif any(not r.passed for r in self._expect_records):
            failed = sum(1 for r in self._expect_records if not r.passed)
            report.status = TCStatus.FAILED
            report.reason = f"{failed} of {len(self._expect_records)} expectTrue measurement(s) failed"
        else:
            report.status = TCStatus.PASSED

        report.had_teardown_error = self._teardown_exception is not None

        get_run_stats().add_report(report)
        self._logger.tc_result(self._tc_name, report.status, report.reason, duration)

        if report.status != TCStatus.PASSED:
            # Surfaces the result to unittest/VS Code's test explorer so the
            # testcase shows up as failed/errored there too, without
            # affecting whether the *next* testcase runs.
            self.fail(f"{self._tc_name} -> {report.status.value}: {report.reason}")
