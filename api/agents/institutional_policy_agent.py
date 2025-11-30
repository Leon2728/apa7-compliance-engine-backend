from __future__ import annotations
from typing import Optional
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    PolicyComplianceSummary,
)
from api.rules_library import RuleLibrary


class InstitutionalPolicyAgent:
    """
    Agente que evaluá la conformidad del documento con políticas institucionales.
    Calcula un score (0-100) basado en los findings de todos los agentes.
    """
    
    agent_id = "institutional_policy"
    
    def __init__(self, rule_library: RuleLibrary) -> None:
        self.rule_library = rule_library
    
    def run(
        self,
        context: LintContext,
        profile: DocumentProfile,
        findings: list[Finding],
    ) -> PolicyComplianceSummary:
        """
        Ejecuta la evaluación de conformidad con políticas institucionales.
        """
        
        # Definir políticas aplicables
        policy_type = self._determine_policy_type(context, profile)
        
        # Evaluar policies
        passed_policies = self._evaluate_passed_policies(findings, policy_type)
        failed_policies = self._evaluate_failed_policies(findings, policy_type)
        
        # Calcular score
        score = self._calculate_policy_score(
            passed_policies,
            failed_policies,
            findings,
        )
        
        # Generar notas
        notes = self._generate_notes(policy_type, passed_policies, failed_policies)
        
        return PolicyComplianceSummary(
            score=score,
            policy_type=policy_type,
            passed_policies=passed_policies,
            failed_policies=failed_policies,
            notes=notes,
        )
    
    def _determine_policy_type(self, context: LintContext, profile: DocumentProfile) -> str:
        """
        Determina el tipo de política institucional aplicable.
        """
        institution = context.institution or profile.institution or "unknown"
        return f"institutional_apa7_{institution.lower()}"
    
    def _evaluate_passed_policies(self, findings: list[Finding], policy_type: str) -> list[str]:
        """
        Retorna políticas que se cumplieron (pocas/sin errores críticos).
        """
        critical_categories = {"structure", "citations", "references"}
        passed = []
        
        for cat in critical_categories:
            errors_in_cat = sum(
                1 for f in findings
                if f.category == cat and "error" in str(f.severity).lower()
            )
            if errors_in_cat == 0:
                passed.append(f"compliance_{cat}")
        
        return passed
    
    def _evaluate_failed_policies(self, findings: list[Finding], policy_type: str) -> list[str]:
        """
        Retorna políticas que NO se cumplieron (errores críticos).
        """
        critical_categories = {"structure", "citations", "references"}
        failed = []
        
        for cat in critical_categories:
            errors_in_cat = sum(
                1 for f in findings
                if f.category == cat and "error" in str(f.severity).lower()
            )
            if errors_in_cat > 0:
                failed.append(f"compliance_{cat}_{errors_in_cat}_errors")
        
        return failed
    
    def _calculate_policy_score(self,  passed: list[str], failed: list[str], findings: list[Finding]) -> float:
        """
        Calcula un score 0-100.
        - Score base: 100
        - Cada error: -5
        - Cada warning: -2
        - Mínimo: 0
        """
        score = 100.0
        
        error_count = sum(1 for f in findings if "error" in str(f.severity).lower())
        warning_count = sum(1 for f in findings if "warning" in str(f.severity).lower())
        
        score -= error_count * 5
        score -= warning_count * 2
        
        return max(0.0, score)
    
    def _generate_notes(self, policy_type: str, passed: list[str], failed: list[str]) -> Optional[str]:
        """
        Genera notas sobre cumplimiento de políticas.
        """
        if not passed and not failed:
            return None
        
        parts = [f"Política: {policy_type}"]
        
        if passed:
            parts.append(f"Cumplidas: {len(passed)}")
        
        if failed:
            parts.append(f"Incumplidas: {len(failed)}")
        
        return " | ".join(parts)
