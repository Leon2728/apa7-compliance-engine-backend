from __future__ import annotations

import asyncio
from datetime import datetime
from time import perf_counter
from typing import List

from api.agents.base_agent import BaseAgent
from api.agents.document_profile_agent import DocumentProfileAgent
from api.agents.general_structure_agent import GeneralStructureAgent
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
            # Later you'll add: GlobalFormatAgent, InTextCitationsAgent, etc.
        ]

    async def run(self, request: LintRequest) -> LintResponse:
        start = perf_counter()

        # 1) Infer document profile
        profile, profile_findings = await self.document_profile_agent.analyze(
            document_text=request.document_text,
            context=request.context,
        )

        # 2) Run all agents in parallel
        tasks = [
            agent.run(
                document_text=request.document_text,
                context=request.context,
                profile=profile,
            )
            for agent in self.agents
        ]
        results = await asyncio.gather(*tasks)

        agent_findings = [f for sublist in results for f in sublist]
        all_findings = profile_findings + agent_findings

        # 3) Summary
        summary = LintSummary(
            error_count=sum(1 for f in all_findings if f.severity == Severity.error),
            warning_count=sum(1 for f in all_findings if f.severity == Severity.warning),
            suggestion_count=sum(
                1 for f in all_findings if f.severity == Severity.suggestion
            ),
        )

        elapsed_ms = (perf_counter() - start) * 1000.0

        response = LintResponse(
            success=True,
            findings=all_findings,
            summary=summary,
            agents_run=["DOCUMENTPROFILE"] + [a.agent_id for a in self.agents],
            elapsed_ms=elapsed_ms,
            profile=profile,
            timestamp=datetime.utcnow(),
        )

        return response
