from repopilot_agent.tools.test_tools import infer_test_command, run_test_command


def test_infer_test_command_prefers_tests_directory(tmp_path):
    (tmp_path / "tests").mkdir()

    command = infer_test_command(str(tmp_path))

    assert command[-2:] == ["pytest", "tests"]


def test_run_test_command_captures_passed_status(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    result = run_test_command(str(tmp_path), timeout_seconds=15)

    assert result["test_status"] == "passed"
    assert result["test_exit_code"] == 0
