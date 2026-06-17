from repopilot_agent.nodes.route import route_after_tests


def test_route_after_tests_passed_goes_to_pr_summary():
    state = {
        "test_status": "passed",
        "repair_attempts": 0,
        "max_repair_attempts": 2,
    }

    assert route_after_tests(state) == "pr_summary"


def test_route_after_tests_failed_with_attempts_left_goes_to_repair():
    state = {
        "test_status": "failed",
        "repair_attempts": 0,
        "max_repair_attempts": 2,
    }

    assert route_after_tests(state) == "repair_subgraph"


def test_route_after_tests_failed_with_attempts_exhausted_goes_to_pr_summary():
    state = {
        "test_status": "failed",
        "repair_attempts": 2,
        "max_repair_attempts": 2,
    }

    assert route_after_tests(state) == "pr_summary"


def test_route_after_tests_unknown_with_attempts_left_goes_to_repair():
    state = {
        "test_status": "unknown",
        "repair_attempts": 0,
        "max_repair_attempts": 1,
    }

    assert route_after_tests(state) == "repair_subgraph"