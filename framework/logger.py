"""Per-run logging.

Every complete test run gets its own `.log` file under `logs/`, named with
the exact runtime timestamp it started (down to the millisecond, so rapid
consecutive runs never collide or overwrite each other):

    logs/test_run_2026-09-13_10-50-01-125.log

The same messages are also written to the console. Console output is
colorized (when the terminal supports it) for readability; the `.log` file
itself is kept as clean plain text.
"""

import datetime
import io
import os
import sys
import threading
from pathlib import Path

# Ensure stdout can handle Unicode box-drawing / tick / cross characters on
# Windows, where the default console encoding is usually cp1252.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"


class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class RunLogger:
    """Singleton: the first testcase to run creates it (lazily), so it works
    the same way whether the suite is launched via `run_tests.py`, plain
    `python -m unittest`, or a single file debugged directly from VS Code.
    """

    _instance = None
    _create_lock = threading.Lock()

    def __init__(self, run_id, log_path):
        self.run_id = run_id
        self.log_path = log_path
        self._file_lock = threading.Lock()
        self._fh = open(log_path, "a", encoding="utf-8")
        self._color = _supports_color()

    @classmethod
    def get(cls):
        if cls._instance is not None:
            return cls._instance
        with cls._create_lock:
            if cls._instance is None:
                LOGS_DIR.mkdir(parents=True, exist_ok=True)
                now = datetime.datetime.now()
                run_id = now.strftime("%Y-%m-%d_%H-%M-%S-") + f"{now.microsecond // 1000:03d}"
                log_path = LOGS_DIR / f"test_run_{run_id}.log"
                cls._instance = cls(run_id, log_path)
            return cls._instance

    # ------------------------------------------------------------------
    # low-level helpers
    # ------------------------------------------------------------------
    def now(self):
        return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _write(self, line, color=None):
        with self._file_lock:
            self._fh.write(line + "\n")
            self._fh.flush()
        if self._color and color:
            print(f"{color}{line}{_Ansi.RESET}")
        else:
            print(line)

    def close(self):
        with self._file_lock:
            try:
                self._fh.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # run-level
    # ------------------------------------------------------------------
    def run_start(self):
        bar = "\u2550" * 70
        self._write(bar)
        self._write(" TEST RUN START")
        self._write(f" Run ID    : {self.run_id}")
        self._write(" Framework : Universal unittest template")
        self._write(bar)

    def full_setup_start(self):
        self._write(f"[{self.now()}] [RUN]       Full setup started", _Ansi.CYAN)

    def full_setup_done(self):
        self._write(f"[{self.now()}] [RUN]       Full setup completed", _Ansi.CYAN)

    def full_setup_error(self, exc):
        self._write(f"[{self.now()}] [ERROR]     Full setup raised {type(exc).__name__}: {exc}", _Ansi.RED)

    def full_teardown_start(self):
        self._write("")
        self._write("\u2500" * 70)
        self._write(f"[{self.now()}] [RUN]       Full teardown started", _Ansi.CYAN)

    def full_teardown_done(self):
        self._write(f"[{self.now()}] [RUN]       Full teardown completed", _Ansi.CYAN)

    def full_teardown_error(self, exc):
        self._write(f"[{self.now()}] [ERROR]     Full teardown raised {type(exc).__name__}: {exc}", _Ansi.RED)

    # ------------------------------------------------------------------
    # testcase-level
    # ------------------------------------------------------------------
    def tc_start(self, name):
        self._write("")
        self._write("\u2500" * 70)
        self._write(f"[TC START] {name}")
        self._write("\u2500" * 70)

    def setup_start(self, name):
        self._write(f"[{self.now()}] [SETUP]     {name} setup started", _Ansi.CYAN)

    def setup_done(self, name):
        self._write(f"[{self.now()}] [SETUP]     {name} setup completed", _Ansi.CYAN)

    def execution_start(self, name):
        self._write(f"[{self.now()}] [EXECUTE]   {name} test_execution started", _Ansi.CYAN)

    def execution_done(self, name):
        self._write(f"[{self.now()}] [EXECUTE]   {name} test_execution completed", _Ansi.CYAN)

    def execution_skipped(self, name, reason):
        self._write(f"[{self.now()}] [EXECUTE]   {name} test_execution skipped ({reason})", _Ansi.YELLOW)

    def expect(self, name, passed, message, source=None):
        mark = "\u2713 PASS" if passed else "\u2717 FAIL"
        color = _Ansi.GREEN if passed else _Ansi.RED
        suffix = f"  [via {source}]" if source else ""
        self._write(f'[{self.now()}] [EXPECT]    {name} | {mark} | "{message}"{suffix}', color)

    def assertion(self, name, passed, message):
        mark = "\u2713 PASS" if passed else "\u2717 FAIL"
        color = _Ansi.GREEN if passed else _Ansi.YELLOW
        self._write(f'[{self.now()}] [ASSERT]    {name} | {mark} | "{message}"', color)

    def exception(self, name, phase, exc, tb_text):
        self._write(
            f"[{self.now()}] [ERROR]     {name} | Unhandled {type(exc).__name__} during {phase}: {exc}",
            _Ansi.RED,
        )
        for line in tb_text.rstrip().splitlines():
            self._write(f"                          {line}", _Ansi.GRAY)

    def teardown_start(self, name):
        self._write(f"[{self.now()}] [TEARDOWN]  {name} teardown started", _Ansi.CYAN)

    def teardown_done(self, name):
        self._write(f"[{self.now()}] [TEARDOWN]  {name} teardown completed", _Ansi.CYAN)

    def teardown_error(self, name, exc, tb_text):
        self._write(f"[{self.now()}] [ERROR]     {name} | Teardown raised {type(exc).__name__}: {exc}", _Ansi.RED)
        for line in tb_text.rstrip().splitlines():
            self._write(f"                          {line}", _Ansi.GRAY)

    def tc_result(self, name, status, reason, duration):
        passed = status.value == "PASSED"
        color = _Ansi.GREEN if passed else _Ansi.RED
        mark = "\u2713 PASSED" if passed else f"\u2717 {status.value}"
        self._write("")
        self._write(f"[RESULT]    {name} \u2192 {mark}", color)
        if reason:
            self._write(f"            Reason   : {reason}")
        self._write(f"            Duration : {duration:.3f}s")

    # ------------------------------------------------------------------
    # run summary
    # ------------------------------------------------------------------
    def summary(self, stats):
        bar = "\u2550" * 70
        self._write("")
        self._write(bar)
        self._write(" TEST RUN SUMMARY")
        self._write(bar)
        self._write(f"Total testcases  : {stats['total']}")
        self._write(f"Passed           : {stats['passed']}")
        self._write(f"Failed           : {stats['failed']}")
        self._write(f"Aborted          : {stats['aborted']}")
        self._write(f"Errors           : {stats['errors']}")
        self._write(f"No Measurements  : {stats['no_measurements']}")
        self._write(f"Teardown Errors  : {stats['teardown_errors']} (logged, non-fatal)")
        self._write("")
        self._write(f"Total expectTrue : {stats['total_expect']}")
        self._write(f"  Passed         : {stats['expect_passed']}")
        self._write(f"  Failed         : {stats['expect_failed']}")
        self._write("")
        overall_ok = (
            stats["failed"] == 0
            and stats["aborted"] == 0
            and stats["errors"] == 0
            and stats["no_measurements"] == 0
        )
        final = "\u2713 PASSED" if overall_ok else "\u2717 FAILED"
        color = _Ansi.GREEN if overall_ok else _Ansi.RED
        self._write(f"FINAL RESULT     : {final}", color)
        self._write(bar)


def get_logger():
    return RunLogger.get()
