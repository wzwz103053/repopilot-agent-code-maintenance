from __future__ import annotations


def analyze_failure_output(test_output: str, test_exit_code: int | None) -> dict:
    """Classify pytest output for the legacy analyze_test_failure node."""
    output = (test_output or "").lower()

    if test_exit_code == 0:
        failure_type = "none"
        failure_analysis = "Tests passed."
    elif "importerror" in output or "modulenotfounderror" in output:
        failure_type = "import_error"
        failure_analysis = "The test output indicates an import failure."
    elif "assert" in output or "assertionerror" in output:
        failure_type = "assertion_failure"
        failure_analysis = "The test output indicates an assertion failure."
    elif "traceback" in output or "typeerror" in output or "keyerror" in output:
        failure_type = "runtime_error"
        failure_analysis = "The test output indicates a runtime error."
    else:
        failure_type = "unknown"
        failure_analysis = "The failure type could not be determined."

    return {
        "failure_type": failure_type,
        "failure_analysis": failure_analysis,
    }
