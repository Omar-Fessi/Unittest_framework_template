# Python unittest Framework Template

A reusable template for writing structured, scalable test suites in Python.

## Project Structure

```
project_root/
├── framework/          # Core framework engine
├── tests/              # Test cases (tc_*.py files)
├── helpers/            # Shared helper modules
├── logs/               # Per-run log files (auto-generated)
├── .vscode/            # VS Code run/debug configurations
├── run_tests.py        # CLI entry point
└── README.md
```

## Requirements

- Python 3.8+ (3.11+ recommended)
- No third-party dependencies — uses standard library only

## Getting Started

```bash
git clone https://github.com/Omar-Fessi/Unittest_framework_template.git
cd Unittest_framework_template
python run_tests.py
```

## Writing a Test Case

Create a new file under `tests/` named `tc_<name>.py`:

```python
from tests import base_test
from helpers import external_file


class TCExample(base_test.BaseTest):

    def setup(self):
        self.connection = create_connection()
        self.assertTrue(self.connection is not None, "Connection must be initialized")

    def test_execution(self):
        self.expectTrue(self.connection.is_ready(), "Connection is ready")
        external_file.helper_method()
        self.expectTrue(self.connection.is_alive(), "Connection remains alive")

    def teardown(self):
        if self.connection:
            self.connection.close()
```

Each test case implements three methods:

| Method | Purpose |
|--------|---------|
| `setup` | Initialize resources before the test |
| `test_execution` | Run the actual test logic |
| `teardown` | Clean up resources after the test |

## Assertions

| Method | Behavior on Failure |
|--------|-------------------|
| `expectTrue(condition, message)` | Records failure, continues execution |
| `assertTrue(condition, message)` | Aborts current phase, jumps to teardown |

Use `assertTrue` for preconditions (e.g. connection established). Use `expectTrue` for actual test measurements — all are collected and reported even if some fail.

## Test Results

| Status | Meaning |
|--------|---------|
| `PASSED` | All `expectTrue` checks passed |
| `FAILED` | At least one `expectTrue` check failed |
| `ABORTED` | `assertTrue` failed — test could not proceed |
| `ERROR` | Unhandled exception during execution |
| `NO_MEASUREMENTS` | No `expectTrue` calls were made |

## Running Tests

```bash
# Run full suite
python run_tests.py

# Run a single test module
python run_tests.py tests.tc_login

# Using unittest directly
python -m unittest tests.tc_login -v
```

## VS Code Integration

- **Test Explorer**: Open the Testing sidebar and run or debug individual tests or the full suite.
- **Launch Configurations**: Use the Run and Debug panel to select:
  - `Run: Full Test Suite`
  - `Run: Current Testcase File`

## Logs

Each run generates a timestamped log file under `logs/`:

```
logs/test_run_2026-09-13_10-50-01-125.log
```

Console output is colorized. Log files are plain text and never overwritten.

### Sample Output

```
══════════════════════════════════════════════════════════════════════
 TEST RUN SUMMARY
══════════════════════════════════════════════════════════════════════
Total testcases  : 5
Passed           : 2
Failed           : 1
Aborted          : 1
Errors           : 1

Total expectTrue : 10
  Passed         : 9
  Failed         : 1

FINAL RESULT     : ✗ FAILED
══════════════════════════════════════════════════════════════════════
```

## Adding Helpers

Place shared logic in `helpers/`. Helper modules report measurements using the framework context:

```python
# helpers/my_helper.py
from framework import context

def validate_response(response):
    context.expectTrue(response.status == 200, "Response status is 200")
    context.expectTrue(response.body is not None, "Response body is not empty")
```

Results from helpers are attributed to the calling test case in the logs.

## Scaling

Add more `tc_*.py` files under `tests/` and more helpers under `helpers/` — discovery and aggregation are automatic.
