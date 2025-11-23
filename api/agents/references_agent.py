from __future__ import annotations

import re
from typing import List

from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.rules_library import RuleLibrary
from api.rules_models import Rule, CheckType, RuleSource


class ReferencesAgent(BaseAgent):
    """
    Agente REFERENCES.

    Implementa validaciones aproximadas basadas en las reglas:
      - CUN-REF-001 a CUN-REF-006
    """

    agent_id = "REFERENCES"

    def __init__(self, rule_library: RuleLibrary) -> None:
        super().__init__(rule_library)

    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)
                is_international = context.profile_variant == "apa7_international"
        findings: List[Finding] = []

        text = document_text or ""
        refs_block = self._extract_references_block(text)
        ref_entries = self._extract_reference_entries(refs_block)

        for rule in rules:
                        if is_international and rule.source == RuleSource.LOCAL:
                                            continue
            if rule.rule_id == "CUN-REF-001":
                findings.extend(self._check_ref_001(rule, ref_entries))
            elif rule.rule_id == "CUN-REF-006":
                findings.extend(self._check_ref_006(rule, text, refs_block))
            # CUN-REF-002, 003, 004 y 005 se solapan con
            # la lógica del agente InTextCitations o requieren
            # análisis de tipo de fuente. Se pueden ir refinando
            # progresivamente con detecciones más específicas.
            # Por ahora, priorizamos orden y encabezado adecuado.

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_references_block(self, text: str) -> str:
        upper = text.upper()
        idx = upper.find("REFERENCIAS")
        if idx == -1:
            idx = upper.find("BIBLIOGRAFÍA")
        if idx == -1:
            return ""
        return text[idx:]

    def _extract_reference_entries(self, references_block: str) -> List[str]:
        lines = [ln.rstrip() for ln in references_block.splitlines()]
        filtered: List[str] = []
        for ln in lines:
            if not ln.strip():
                continue
            upper = ln.upper().strip()
            if upper.startswith("REFERENCIAS") or upper.startswith("BIBLIOGRAFÍA"):
                continue
            filtered.append(ln.strip())
        return filtered

    # ------------------------------------------------------------------
    # Reglas
    # ------------------------------------------------------------------
    def _check_ref_001(self, rule: Rule, ref_entries: List[str]) -> List[Finding]:
        """
        CUN-REF-001:
          - Orden alfabético por apellido del primer autor.
        """
        findings: List[Finding] = []
        if not ref_entries:
            return findings

        # Extraemos la "clave de orden": primera palabra de cada entrada
        keys = []
        for entry in ref_entries:
            # Primera palabra no vacía
            parts = entry.split()
            if not parts:
                continue
            keys.append(parts[0].upper())

        sorted_keys = sorted(keys)
        if keys == sorted_keys:
            # Ya está ordenado
            return findings

        details = (
            "El orden actual de las referencias no es alfabético. "
            f"Orden detectado: {keys}; orden esperado: {sorted_keys}"
        )

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:ORDER",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="references_order",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=details,
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section="REFERENCIAS",
                ),
                snippet="\n".join(ref_entries[:3]),
            )
        )
        return findings

    def _check_ref_006(
        self,
        rule: Rule,
        full_text: str,
        refs_block: str,
    ) -> List[Finding]:
        """
        CUN-REF-006:
          - Encabezado adecuado de la sección de referencias ('REFERENCIAS').
        """
        findings: List[Finding] = []

        upper = full_text.upper()
        has_referencias = "REFERENCIAS" in upper
        has_bibliografia = "BIBLIOGRAFÍA" in upper

        if has_referencias:
            return findings

        if not (has_referencias or has_bibliografia):
            # No hay sección de referencias explícita
            return findings

        # Hay 'Bibliografía' pero no 'Referencias'
        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:HEADER",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="references_header",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "Se detectó un encabezado de 'Bibliografía' pero no 'REFERENCIAS'. "
                    "La guía CUN prefiere el uso de 'REFERENCIAS' como encabezado estándar."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet=refs_block.splitlines()[0] if refs_block else "",
            )
        )

        return findings
