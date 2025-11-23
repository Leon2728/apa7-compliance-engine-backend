from __future__ import annotations

import asyncio
from datetime import datetime
from time import perf_counter
from typing import List

from api.agents.base_agent import BaseAgent
from api.agents.document_profile_agent import DocumentProfileAgent
from api.agents.math_equations_agent import MathEquationsAgent
from api.agents.general_structure_agent import GeneralStructureAgent
from api.agents.tables_figures_agent import TablesFiguresAgent
from api.agents.in_text_citations_agent import InTextCitationsAgent
from api.agents.references_agent import ReferencesAgent
from api.models.lint_models import LintRequest, LintResponse, LintSummary
from api.rules_library import RuleLibrary
from api.rules_models import Severity


class LintOrchestrator:
    """
    Main orchestrator of the APA7 compliance engine.

    Flow:
        1) Run DOCUMENTPROFILE to infer the document profile and related findings.
        2) Run the rest of the agents in parallel (currently GENERALSTRUCTURE).
        3) Aggregate all findings and return a uniform LintResponse.
    """

    def __init__(self, rule_library: RuleLibrary) -> None:
        self.rule_library = rule_library

        # Special agent (does NOT implement BaseAgent): returns (profile, findings)
        self.document_profile_agent = DocumentProfileAgent(rule_library)

        # Agents that implement BaseAgent.run(...)
        self.agents: List[BaseAgent] = [
            GeneralStructureAgent(rule_library),
            TablesFiguresAgent(rule_library),
            InTextCitationsAgent(rule_library),
            ReferencesAgent(rule_library),
                        MathEquationsAgent(rule_library),
        ]

    async def lint_document(self, request: LintRequest) -> LintResponse:
        start_time = perf_counter()
        text = request.text

        # 1. Analyze profile (sequential)
        profile, profile_findings = await self.document_profile_agent.run(text)

        # Context for other agents
        context = request.context  # has page_count, etc.

        # 2. Run other agents in parallel
        # Agent filtering logic
        requested_agents: set[str] | None = None
        if request.options and request.options.agents:
            requested_agents = set(request.options.agents)

        agents_to_run = self.agents
        if requested_agents:
            agents_to_run = [agent for agent in self.agents if agent.agent_id in requested_agents]

        # Gather tasks
        tasks = []
        for agent in agents_to_run:
            tasks.append(agent.run(text, context, profile))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Aggregate findings
        all_findings = list(profile_findings)

        for res in results_list:
            if isinstance(res, list):
                all_findings.extend(res)
            else:
                # If an exception occurred, we could log it or add a system finding.
                # For now, just print/ignore
                print(f"Agent error: {res}")

        # Calculate stats
        error_count = sum(1 for f in all_findings if f.severity == Severity.ERROR)
        warning_count = sum(1 for f in all_findings if f.severity == Severity.WARNING)
        info_count = sum(1 for f in all_findings if f.severity == Severity.INFO)
        # suggestion/typo? APA7 generally maps to these 3.

        # Sort findings by location (if possible)
        # A simple sort key: (page or 0, line or 0, start_offset or 0)
        def sort_key(f):
            loc = f.location
            return (
                loc.page if loc and loc.page else 0,
                loc.line if loc and loc.line else 0,
                loc.start_offset if loc and loc.start_offset else 0,
            )

        all_findings.sort(key=sort_key)

        duration = perf_counter() - start_time

        summary = LintSummary(
            total_findings=len(all_findings),
            errors=error_count,
            warnings=warning_count,
            info=info_count,
            compliance_score=self._calculate_score(error_count, warning_count),
            processing_time_ms=int(duration * 1000),
            timestamp=datetime.utcnow().isoformat(),
        )

        return LintResponse(
            request_id=request.request_id,
            summary=summary,
            profile=profile,
            findings=all_findings,
        )

    def _calculate_score(self, errors: int, warnings: int) -> float:
        """
        Simple scoring logic:
        Start at 100.
        Each error -5
        Each warning -2
        Min 0.
        """
        score = 100.0
        score -= errors * 5.0
        score -= warnings * 2.0
        return max(0.0, score)
