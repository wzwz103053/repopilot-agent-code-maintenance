# RepoPilot Resume Description

## English Version

Built RepoPilot, a LangGraph + LangChain based multi-agent code maintenance system that scans repositories, routes issue types, retrieves relevant code context, investigates root causes, generates patch plans, writes patches, evaluates patch quality, applies Guardrails, supports Human Review, runs tests, repairs failures, and produces PR-style summaries.

Implemented a hybrid workflow-agent architecture using LangGraph StateGraph, conditional edges, subgraphs, shared state, retrieval-augmented investigation, middleware, Guardrails, Patch Evaluator loop, validation and repair loops, LangSmith Studio observability, and benchmark metrics.

## Chinese Version

构建 RepoPilot，一个基于 LangGraph + LangChain 的多 Agent 代码维护系统。系统支持自动扫描代码仓库、识别任务类型、检索相关代码上下文、分析根因、生成修复计划、生成 patch、评估 patch 质量、执行 Guardrails、安全检查、支持 Human Review、应用 patch、运行测试、失败修复循环，并生成 PR 风格总结。

项目采用 hybrid workflow-agent 架构：外层 LangGraph workflow 负责流程控制、条件分支、子图、安全边界、人工审核、测试验证和失败恢复；内层 LangChain agents 负责动态代码调查、工具调用、根因分析、patch 生成、Patch Evaluator 评估和结果总结。

## Resume Bullet Points

- Built a LangGraph + LangChain multi-agent code maintenance workflow with Issue Router, repository scanning, retrieval-augmented investigation, patch generation, Patch Evaluator, Guardrails, Human Review, test validation, and repair loops.
- Designed a hybrid workflow-agent architecture using LangGraph StateGraph, conditional edges, subgraphs, shared state, middleware, and LangSmith Studio tracing.
- Implemented benchmark metrics including patch apply rate, test pass rate, retrieval recall, files-to-modify accuracy, modified-files accuracy, repair attempts, and runtime.