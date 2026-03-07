# -*- coding: utf-8 -*-
"""Orchestrator for coordinating PlanningAgent and ExploringAgent instances.

Manages the full pipeline:
  Phase 1: Planning  — HTML source analysis → ExplorationPlan
  Phase 2: Dispatch  — Parallel subagent execution of task groups
  Phase 3: Aggregate — Collect results and generate report
"""
# flake8: noqa: E501
# pylint: disable=C0301

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from web.event_bus import EventSink
from web.control_hub import ControlHub

from agentscope._logging import logger

from planning_agent import PlanningAgent, ExplorationPlan, TaskGroup
from exploring_agent import (
    create_and_run_exploring_agent,
    ExplorationResult,
)
from utils.url_utils import sanitize_start_url, LocalFileServer


class Orchestrator:
    """Coordinates PlanningAgent and multiple ExploringAgent instances.

    The orchestrator manages a three-phase pipeline:
    1. Planning: Analyze HTML source code to generate exploration plans
    2. Dispatching: Launch parallel browser agents for each task group
    3. Aggregation: Collect results and produce a summary report
    """

    def __init__(
        self,
        model_config: str = "configs/model_config.json",
        mcp_config: str = "configs/mcp_config.json",
        headless: bool = True,
        record_video: bool = False,
        executable_path: Optional[str] = None,
        max_iters: int = 30,
        max_concurrent: int = 3,
    ) -> None:
        """Initialize the Orchestrator.

        Args:
            model_config: Path to model configuration file.
            mcp_config: Path to MCP configuration file.
            headless: Run browsers in headless mode.
            record_video: Record video for each subagent.
            executable_path: Path to browser executable.
            max_iters: Maximum iterations per subagent.
            max_concurrent: Maximum number of concurrent subagents.
        """
        self.model_config = model_config
        self.mcp_config = mcp_config
        self.headless = headless
        self.record_video = record_video
        self.executable_path = executable_path
        self.max_iters = max_iters
        self.max_concurrent = max_concurrent

    def _task_group_to_prompt(self, group: TaskGroup, page_url: str) -> str:
        """Convert a TaskGroup into a natural language prompt for BrowserAgent.

        Args:
            group: The TaskGroup to convert.
            page_url: The URL of the page to interact with.

        Returns:
            A detailed prompt string instructing the browser agent.
        """
        lines = [
            f"You are testing an interactive web page at {page_url}.",
            f"Your test purpose: {group.test_purpose}",
            "",
            "Please execute the following interaction steps IN ORDER:",
            "",
        ]

        for task in group.tasks:
            step_desc = f"Step {task.step_id}: [{task.action.upper()}] {task.description}"
            step_desc += f"\n  Target: {task.target}"
            if task.value:
                step_desc += f"\n  Value: {task.value}"
            step_desc += f"\n  Expected effect: {task.expected_effect}"
            lines.append(step_desc)
            lines.append("")

        lines.extend([
            f"After completing all steps, verify the expected outcome: {group.expected_outcome}",
            "",
            "IMPORTANT:",
            "- Execute each step carefully and observe the result before proceeding.",
            "- If an element is not immediately visible, try scrolling or waiting.",
            "- Report any unexpected behavior or errors.",
            "- When you have completed all steps and verified the outcome, "
            "call browser_generate_final_response to summarize your findings.",
        ])

        return "\n".join(lines)

    async def run(
        self,
        html_path: str,
        run_id: str | None = None,
        event_sink: EventSink | None = None,
        control_hub: ControlHub | None = None,
    ) -> dict:
        """Execute the full orchestration pipeline.

        Args:
            html_path: Path to the HTML file to analyze and test.
            run_id: Optional ID for this run.
            event_sink: Optional EventSink for emitting events.
            control_hub: Optional ControlHub for controlling agents.

        Returns:
            A dictionary containing the plan and all exploration results.
        """
        # ─── Phase 1: Planning ─────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("PHASE 1: PLANNING")
        logger.info("=" * 60)

        if event_sink:
            from web.event_types import RunEvent
            await event_sink.emit(RunEvent(type="run.stage", runId=run_id, payload={"stage": "planning"}))

        planning_agent = PlanningAgent(
            model_config=self.model_config,
        )
        session_dir = planning_agent.session_dir

        plan = await planning_agent.generate_plan(html_path)

        logger.info(
            "Plan generated: %d task groups for '%s'",
            len(plan.task_groups),
            plan.page_title,
        )

        # ─── Phase 2: Dispatching ─────────────────────────────────────
        logger.info("=" * 60)
        logger.info("PHASE 2: DISPATCHING %d SUBAGENTS", len(plan.task_groups))
        logger.info("=" * 60)

        if event_sink:
            from web.event_types import RunEvent
            await event_sink.emit(RunEvent(type="run.stage", runId=run_id, payload={"stage": "dispatching"}))

        # Prepare the start URL — serve local files via HTTP
        start_url, is_local = sanitize_start_url(html_path)
        local_server = None
        if is_local or start_url.startswith("file://"):
            local_server = LocalFileServer(start_url)
            start_url = local_server.hosted_url
            logger.info("Local file server started: %s", start_url)

        # Create exploration directory
        exploration_dir = os.path.join(session_dir, "exploration")
        os.makedirs(exploration_dir, exist_ok=True)

        # Launch subagents with concurrency control
        try:
            results = await self._dispatch_subagents(
                plan=plan,
                start_url=start_url,
                exploration_dir=exploration_dir,
                run_id=run_id,
                event_sink=event_sink,
                control_hub=control_hub,
            )
        finally:
            # Shutdown local server after all subagents are done
            if local_server:
                local_server.stop()
                logger.info("Local file server stopped.")

        # ─── Phase 3: Aggregation ─────────────────────────────────────
        logger.info("=" * 60)
        logger.info("PHASE 3: AGGREGATION")
        logger.info("=" * 60)

        if event_sink:
            from web.event_types import RunEvent
            await event_sink.emit(RunEvent(type="run.stage", runId=run_id, payload={"stage": "aggregation"}))

        report = self._generate_report(plan, results, session_dir)

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("Session directory: %s", session_dir)
        logger.info("=" * 60)

        return {
            "session_dir": session_dir,
            "plan": plan.model_dump(),
            "results": [r.model_dump() for r in results],
            "report_path": os.path.join(session_dir, "report.md"),
        }

    async def _dispatch_subagents(
        self,
        plan: ExplorationPlan,
        start_url: str,
        exploration_dir: str,
        run_id: str | None = None,
        event_sink: EventSink | None = None,
        control_hub: ControlHub | None = None,
    ) -> list[ExplorationResult]:
        """Dispatch ExploringAgent instances with concurrency control.

        Args:
            plan: The exploration plan with task groups.
            start_url: URL for the browser to navigate to.
            exploration_dir: Base directory for subagent work directories.
            run_id: Optional ID for this run.
            event_sink: Optional EventSink for emitting events.
            control_hub: Optional ControlHub for controlling agents.

        Returns:
            List of ExplorationResult from all subagents.
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_with_semaphore(group: TaskGroup) -> ExplorationResult:
            async with semaphore:
                work_dir = os.path.join(
                    exploration_dir,
                    f"subagent_{group.group_id}",
                )
                prompt = self._task_group_to_prompt(group, start_url)

                logger.info(
                    "Launching subagent %d: %s",
                    group.group_id,
                    group.group_name,
                )

                return await create_and_run_exploring_agent(
                    group_id=group.group_id,
                    group_name=group.group_name,
                    prompt=prompt,
                    start_url=start_url,
                    work_dir=work_dir,
                    model_config=self.model_config,
                    mcp_config=self.mcp_config,
                    headless=self.headless,
                    record_video=self.record_video,
                    executable_path=self.executable_path,
                    max_iters=self.max_iters,
                    event_sink=event_sink,
                    control_hub=control_hub,
                    run_id=run_id,
                )

        # Launch all groups concurrently (bounded by semaphore)
        tasks = [
            run_with_semaphore(group) for group in plan.task_groups
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Subagent %d failed with exception: %s",
                    i,
                    result,
                )
                final_results.append(
                    ExplorationResult(
                        group_id=i,
                        group_name=plan.task_groups[i].group_name,
                        success=False,
                        result=f"Exception: {result}",
                    ),
                )
            else:
                final_results.append(result)

        return final_results

    def _generate_report(
        self,
        plan: ExplorationPlan,
        results: list[ExplorationResult],
        session_dir: str,
    ) -> str:
        """Generate a summary report of the exploration.

        Args:
            plan: The original exploration plan.
            results: Results from all subagents.
            session_dir: Session directory to save the report.

        Returns:
            The report content as a string.
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        lines = [
            f"# Exploration Report: {plan.page_title}",
            "",
            f"**Teaching Objective**: {plan.teaching_objective}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Total Task Groups**: {total}",
            f"- **Successful**: {successful}",
            f"- **Failed**: {failed}",
            f"- **Success Rate**: {successful/total*100:.1f}%" if total > 0 else "- **Success Rate**: N/A",
            "",
            "---",
            "",
            "## Detailed Results",
            "",
        ]

        for result in results:
            status = "✅ Success" if result.success else "❌ Failed"
            lines.extend([
                f"### Group {result.group_id}: {result.group_name}",
                "",
                f"**Status**: {status}",
                "",
                f"**Result**: {result.result}",
                "",
            ])
            if result.subtask_progress_summary:
                lines.extend([
                    "**Progress Summary**:",
                    "",
                    result.subtask_progress_summary,
                    "",
                ])
            lines.extend(["---", ""])

        report_content = "\n".join(lines)

        # Save report
        report_path = os.path.join(session_dir, "report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.info("Report saved: %s", report_path)

        # Also save raw results JSON
        results_path = os.path.join(session_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(
                [r.model_dump() for r in results],
                f,
                indent=2,
                ensure_ascii=False,
            )

        return report_content
