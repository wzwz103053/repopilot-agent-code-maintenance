from repopilot_agent.agents.agent_factory import create_repopilot_agent
from repopilot_agent.agents.middleware import build_repopilot_middleware


class FakeModel:
    pass


def test_build_repopilot_middleware_returns_list():
    middleware = build_repopilot_middleware("unit_test_agent")
    assert isinstance(middleware, list)


def test_create_repopilot_agent_factory_exists():
    assert create_repopilot_agent is not None


def test_all_final_agents_import():
    from repopilot_agent.agents.repo_navigator_agent import run_repo_navigation
    from repopilot_agent.agents.planning_agent import run_patch_planning
    from repopilot_agent.agents.patch_writer_agent import run_patch_writer
    from repopilot_agent.agents.test_analyst_agent import run_test_analysis
    from repopilot_agent.agents.repair_agent import run_repair_agent
    from repopilot_agent.agents.pr_summary_agent import run_pr_summary_agent

    assert run_repo_navigation is not None
    assert run_patch_planning is not None
    assert run_patch_writer is not None
    assert run_test_analysis is not None
    assert run_repair_agent is not None
    assert run_pr_summary_agent is not None