# RepoPilot Workflow

RepoPilot combines deterministic workflow control with dynamic agent behavior.

The main path is:

1. Run preflight guardrails.
2. Scan repository files.
3. Route the issue.
4. Retrieve relevant code context.
5. Investigate root cause.
6. Plan a minimal patch.
7. Generate and validate a unified diff.
8. Run patch quality and safety checks.
9. Pause for human review when required.
10. Apply approved patches.
11. Run tests.
12. Enter the repair loop when tests fail and attempts remain.
13. Produce a PR-style summary.

LangGraph controls state, branching, interrupts, and validation gates. LangChain agents perform tool-using reasoning where deterministic code alone would be too rigid.
