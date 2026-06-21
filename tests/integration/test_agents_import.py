import pytest

pytest.importorskip(
    "langchain",
    reason="Agent import smoke tests require optional LangChain dependency.",
)

from repopilot_agent.agents.patch_writer_agent import run_patch_writer
from repopilot_agent.agents.test_analyst_agent import run_test_analysis
from repopilot_agent.agents.repair_agent import run_repair_agent
from repopilot_agent.agents.pr_summary_agent import run_pr_summary_agent


def test_final_agents_import():
    assert run_patch_writer is not None
    assert run_test_analysis is not None
    assert run_repair_agent is not None
    assert run_pr_summary_agent is not None
