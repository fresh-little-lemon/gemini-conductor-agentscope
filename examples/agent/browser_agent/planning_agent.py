# -*- coding: utf-8 -*-
"""Planning Agent for interactive HTML page analysis.

Reads HTML source code and uses LLM to generate structured exploration plans
that can be dispatched to multiple ExploringAgent instances for parallel execution.
"""
# flake8: noqa: E501
# pylint: disable=C0301

import os
import json
import glob
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from utils.model_loader import AutoModel, AutoFormatter
from utils.token_tracker import TokenUsageTracker
from utils.logger_utils import setup_session_logger, session_context

from agentscope.message import Msg
from agentscope._logging import logger

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROMPT_DIR = os.path.join(_CURRENT_DIR, "build_in_prompt")

with open(
    os.path.join(_PROMPT_DIR, "planning_agent_sys_prompt.md"),
    "r",
    encoding="utf-8",
) as f:
    _PLANNING_AGENT_SYS_PROMPT = f.read()


# ─── Pydantic Data Models ─────────────────────────────────────────────

class ExplorationTask(BaseModel):
    """A single interaction step within a task group."""

    step_id: int = Field(description="Sequential step ID within the group")
    action: str = Field(
        description="Action type: click, drag, input, hover, select, slide, scroll, toggle",
    )
    target: str = Field(
        default="",
        description="CSS selector or descriptive identifier for the target element",
    )
    value: Optional[str] = Field(
        default=None,
        description="Value to set (for inputs/sliders/selects) or null",
    )
    description: str = Field(
        description="Human-readable description of the action",
    )
    expected_effect: str = Field(
        description="Expected visual or logical effect after the action",
    )


class TaskGroup(BaseModel):
    """A group of tasks that must be executed serially.
    Different groups can be executed in parallel."""

    group_id: int = Field(description="Unique group ID")
    group_name: str = Field(description="Descriptive name for this test group")
    test_purpose: str = Field(description="What this group tests/explores")
    tasks: list[ExplorationTask] = Field(
        description="Ordered list of tasks to execute serially",
    )
    expected_outcome: str = Field(
        description="Overall expected result after completing this group",
    )


class ExplorationPlan(BaseModel):
    """Complete exploration plan for an interactive page."""

    page_title: str = Field(description="Title of the analyzed page")
    teaching_objective: str = Field(
        description="What the page teaches and how",
    )
    interactive_elements_summary: str = Field(
        description="Brief overview of all interactive elements found",
    )
    task_groups: list[TaskGroup] = Field(
        description="List of task groups for parallel execution",
    )


# ─── Planning Agent ───────────────────────────────────────────────────

class PlanningAgent:
    """Analyzes HTML source code and generates structured exploration plans.

    This agent reads local HTML files, sends the source code to an LLM
    for analysis, and produces an ExplorationPlan that can be dispatched
    to multiple ExploringAgent instances.
    """

    def __init__(
        self,
        model_config: str = "configs/model_config.json",
        sys_prompt: str = _PLANNING_AGENT_SYS_PROMPT,
        session_dir: Optional[str] = None,
    ) -> None:
        """Initialize the PlanningAgent.

        Args:
            model_config: Path to model configuration JSON file.
            sys_prompt: System prompt for HTML analysis.
            session_dir: Override session directory. If None, auto-generated.
        """
        self.sys_prompt = sys_prompt

        # Setup tracker and session directory
        self.tracker = TokenUsageTracker(session_dir=session_dir)
        self.session_dir = self.tracker.session_dir

        # Setup logging
        self.session_logger = setup_session_logger(
            self.session_dir,
            self.tracker.timestamp,
            {"component": "planning_agent", "model_config": model_config},
        )

        # Load model and formatter
        self.model = AutoModel.from_config(model_config)
        self.model = self.tracker.track_model(self.model)
        self.formatter = AutoFormatter.from_config(model_config)

        # Plan output directory
        self.plan_dir = os.path.join(self.session_dir, "plan")
        os.makedirs(self.plan_dir, exist_ok=True)

        logger.info("PlanningAgent initialized. Session dir: %s", self.session_dir)

    def read_html_source(self, html_path: str) -> str:
        """Read and return the content of an HTML file.

        Args:
            html_path: Path to the HTML file.

        Returns:
            The full HTML source code as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        abs_path = os.path.abspath(html_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"HTML file not found: {abs_path}")

        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info("Read HTML file: %s (%d bytes)", abs_path, len(content))
        return content

    async def analyze_html(self, html_source: str) -> ExplorationPlan:
        """Analyze HTML source code and generate an exploration plan.

        Args:
            html_source: The complete HTML source code string.

        Returns:
            An ExplorationPlan object with structured task groups.
        """
        user_prompt = (
            "Please analyze the following HTML source code of an interactive "
            "teaching web page. Identify all interactive elements, understand "
            "the teaching objective, analyze element dependencies, and generate "
            "a structured exploration plan.\n\n"
            "HTML Source Code:\n"
            "```html\n"
            f"{html_source}\n"
            "```"
        )

        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                Msg("user", user_prompt, "user"),
            ],
        )

        logger.info("Sending HTML to LLM for analysis...")
        res = await self.model(prompt)

        # Extract response text (handle both streaming and non-streaming)
        response_text = ""
        if self.model.stream:
            async for chunk in res:
                if chunk.content:
                    response_text += chunk.content[0].get("text", "")
        else:
            response_text = res.content[0]["text"]

        logger.info("LLM analysis complete. Response length: %d", len(response_text))

        # Parse JSON from response
        plan = self._parse_plan_response(response_text)
        return plan

    def _parse_plan_response(self, response_text: str) -> ExplorationPlan:
        """Parse the LLM response into an ExplorationPlan.

        Args:
            response_text: Raw text response from the LLM.

        Returns:
            Parsed ExplorationPlan object.
        """
        # Clean up potential markdown code block markers
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            plan_dict = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            logger.error("Response text: %s", text[:500])
            raise ValueError(
                f"LLM did not return valid JSON. Parse error: {e}"
            ) from e

        # Sanitize: fix null/missing fields that LLM may omit
        for group in plan_dict.get("task_groups", []):
            for task in group.get("tasks", []):
                if task.get("target") is None:
                    task["target"] = ""
                if task.get("description") is None:
                    task["description"] = ""
                if task.get("expected_effect") is None:
                    task["expected_effect"] = ""
                if task.get("value") is not None:
                    task["value"] = str(task["value"])

        try:
            plan = ExplorationPlan.model_validate(plan_dict)
            logger.info(
                "Parsed plan: %s (%d task groups)",
                plan.page_title,
                len(plan.task_groups),
            )
            return plan
        except Exception as e:
            logger.error("Failed to validate plan structure: %s", e)
            raise ValueError(
                f"LLM response does not match ExplorationPlan schema: {e}"
            ) from e

    def save_plan(self, plan: ExplorationPlan, html_filename: str) -> str:
        """Save the exploration plan as both JSON and Markdown files.

        Args:
            plan: The ExplorationPlan to save.
            html_filename: Original HTML filename (used in the output name).

        Returns:
            Path to the saved JSON plan file.
        """
        base_name = os.path.splitext(os.path.basename(html_filename))[0]

        # Save JSON
        json_path = os.path.join(self.plan_dir, f"{base_name}_plan.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(), f, indent=2, ensure_ascii=False)
        logger.info("Plan saved (JSON): %s", json_path)

        # Save Markdown
        md_path = os.path.join(self.plan_dir, f"{base_name}_plan.md")
        md_content = self._plan_to_markdown(plan)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Plan saved (Markdown): %s", md_path)

        return json_path

    @staticmethod
    def _plan_to_markdown(plan: ExplorationPlan) -> str:
        """Convert an ExplorationPlan to readable Markdown format."""
        lines = [
            f"# Exploration Plan: {plan.page_title}",
            "",
            f"**Teaching Objective**: {plan.teaching_objective}",
            "",
            f"**Interactive Elements**: {plan.interactive_elements_summary}",
            "",
            f"**Total Task Groups**: {len(plan.task_groups)} "
            f"(can be executed in parallel)",
            "",
            "---",
            "",
        ]

        for group in plan.task_groups:
            lines.extend([
                f"## Group {group.group_id}: {group.group_name}",
                "",
                f"**Test Purpose**: {group.test_purpose}",
                "",
                f"**Expected Outcome**: {group.expected_outcome}",
                "",
                "| Step | Action | Target | Value | Description | Expected Effect |",
                "|------|--------|--------|-------|-------------|-----------------|",
            ])

            for task in group.tasks:
                value_str = task.value if task.value else "-"
                lines.append(
                    f"| {task.step_id} | {task.action} | `{task.target}` | "
                    f"{value_str} | {task.description} | {task.expected_effect} |"
                )

            lines.extend(["", "---", ""])

        return "\n".join(lines)

    async def generate_plan(self, html_path: str) -> ExplorationPlan:
        """Full pipeline: read HTML → analyze → save plan.

        Args:
            html_path: Path to the HTML file to analyze.

        Returns:
            The generated ExplorationPlan.
        """
        # Set the logging context for the current task
        token = session_context.set(self.session_logger)
        try:
            logger.info("=== Planning Phase Start ===")
            logger.info("Target HTML: %s", html_path)

            # Read HTML source
            html_source = self.read_html_source(html_path)

            # Analyze with LLM
            plan = await self.analyze_html(html_source)

            # Save plan
            self.save_plan(plan, html_path)

            # Save tracker summary
            self.session_logger.set_summary(self.tracker.get_summary_dict())

            logger.info("=== Planning Phase Complete ===")
            logger.info(
                "Generated %d task groups for %s",
                len(plan.task_groups),
                plan.page_title,
            )

            return plan
        finally:
            # Reset logging context
            if 'token' in locals():
                session_context.reset(token)
