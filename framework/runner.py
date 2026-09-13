"""Full-run (whole-suite) setup/teardown.

This is intentionally decoupled from unittest's own module-level
`setUpModule`/`tearDownModule` hooks, which fire once *per test module* --
not once per run. Instead, the first testcase to execute triggers
`ensure_run_initialized()`, which runs `full_run_setup()` exactly once and
registers `full_run_teardown()` (plus the final run summary) to run via
`atexit`, which fires once no matter how the suite was launched: the full
suite, a single test module, or a single test debugged directly in VS Code.

`atexit` also guarantees full-run teardown executes even if testcases fail,
since unittest failures don't raise -- they're just recorded -- and even in
the rarer case of an uncaught crash elsewhere in the process, `atexit`
handlers still run during normal interpreter shutdown.
"""

import atexit
import threading

from .logger import get_logger
from .results import get_run_stats

_init_lock = threading.Lock()
_initialized = False

_teardown_lock = threading.Lock()
_teardown_done = False


def full_run_setup():
    """Extension point.

    Customize this to perform one-time initialization for the entire test
    run: opening shared connections, loading configuration, preparing
    fixtures/environments that every testcase can rely on, etc. Left as a
    no-op by default. Safe to edit -- this is framework *configuration*, not
    framework internals.
    """
    pass


def full_run_teardown():
    """Extension point: one-time cleanup for the entire test run.

    Guaranteed to run exactly once, even if one or more testcases failed,
    aborted, or raised unexpected exceptions. Safe to edit.
    """
    pass


def ensure_run_initialized():
    """Idempotent: only the very first testcase in a run actually triggers
    full-run setup and registers full-run teardown."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        logger = get_logger()
        logger.run_start()
        logger.full_setup_start()
        try:
            full_run_setup()
        except Exception as exc:  # noqa: BLE001 - must never abort the run
            logger.full_setup_error(exc)
        logger.full_setup_done()
        atexit.register(_run_full_teardown_once)
        _initialized = True


def _run_full_teardown_once():
    global _teardown_done
    with _teardown_lock:
        if _teardown_done:
            return
        _teardown_done = True
        logger = get_logger()
        logger.full_teardown_start()
        try:
            full_run_teardown()
        except Exception as exc:  # noqa: BLE001
            logger.full_teardown_error(exc)
        logger.full_teardown_done()
        logger.summary(get_run_stats().summary())
        logger.close()
