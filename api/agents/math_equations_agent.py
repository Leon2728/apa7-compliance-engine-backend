from __future__ import annotations

import re
from typing import Dict, List, Tuple

from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.rules_library import RuleLibrary
from api.rules_models import Rule


EQUATION_LINE_PATTERN = re.compile(
    r"([A-Za-zÁÉÍÓÚÑ0-9\)\]])\s*=\s*([-+*/A-Za-zÁÉÍÓÚÑ0-9])"
)

EQUATION_NUMBER_PATTERN = re.compile(r"\((\d{1,3})\)")

EQUATION_REF_PATTERN = re.compile(
    r"ECUACI[ÓO]N(?:ES)?\s*\((\d{1,3})\)", re.IGNORECASE
)


class MathEquationsAgent(BaseAgent):
    """
    Agente EQUATIONS.

    Valida aspectos básicos de ecuaciones en el documento:
      - Numeración consecutiva de ecuaciones destacadas.
      - Referencias a ecuaciones en el texto que correspondan a números existentes.
      - Ecuaciones numeradas que nunca se referencian (sugerencia).

    No intenta validar la corrección matemática de las ecuaciones, solo
    su estructura y coherencia con el texto.
    """

    agent_id = "EQUATIONS"

    def __init__(self, rule_library: RuleLibrary) -> None:
        super().__init__(rule_library)

    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        findings: List[Finding] = []

        text = document_text or ""
        lines = self._normalize_lines(text)

        # Detectamos líneas que parecen ecuaciones y sus números asociados.
        eq_lines = self._detect_equation_lines(lines)

        # Si no hay ecuaciones, no aplicamos ninguna regla.
        if not eq_lines:
            return findings

        # Números de ecuación extraídos de las líneas
        equation_numbers = [info["number"] for info in eq_lines if info["number"] is not None]
        equation_number_set = {n for n in equation_numbers if n is not None}

        # Referencias tipo "ecuación (3)" en el texto completo
        equation_refs = self._detect_equation_references(text)
        equation_ref_set = {n for n in equation_refs}

        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)

        for rule in rules:
            if rule.rule_id == "CUN-ME-001":
                findings.extend(
                    self._check_me_001_sequential_numbering(
                        rule,
                        eq_lines,
                        equation_numbers,
                    )
                )
            elif rule.rule_id == "CUN-ME-002":
                findings.extend(
                    self._check_me_002_references_exist(
                        rule,
                        equation_ref_set,
                        equation_number_set,
                    )
                )
            elif rule.rule_id == "CUN-ME-003":
                findings.extend(
                    self._check_me_003_unused_equation_numbers(
                        rule,
                        equation_number_set,
                        equation_ref_set,
                    )
                )

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_lines(text: str) -> List[str]:
        return [ln.rstrip("\n") for ln in text.replace("\r\n", "\n").split("\n")]

    def _detect_equation_lines(self, lines: List[str]) -> List[Dict[str, object]]:
        """
        Detecta líneas que parecen contener ecuaciones simples y, si es posible,
        extrae un número de ecuación entre paréntesis (n).
        """
        eq_lines: List[Dict[str, object]] = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Candidatos a ecuación: línea con signo "=" y poco texto alrededor
            if EQUATION_LINE_PATTERN.search(stripped):
                num_match = EQUATION_NUMBER_PATTERN.search(stripped)
                number = int(num_match.group(1)) if num_match else None
                eq_lines.append(
                    {
                        "line_index": idx,
                        "text": stripped,
                        "number": number,
                    }
                )
        return eq_lines

    def _detect_equation_references(self, text: str) -> List[int]:
        """
        Detecta referencias en el texto del tipo 'ecuación (3)'.
        """
        refs: List[int] = []
        for m in EQUATION_REF_PATTERN.finditer(text):
            try:
                n = int(m.group(1))
                refs.append(n)
            except ValueError:
                continue
        return refs

    # ------------------------------------------------------------------
    # Reglas CUN-ME-001 a CUN-ME-003
    # ------------------------------------------------------------------
    def _check_me_001_sequential_numbering(
        self,
        rule: Rule,
        eq_lines: List[Dict[str, object]],
        equation_numbers: List[int | None],
    ) -> List[Finding]:
        """
        CUN-ME-001:
          - Verificar que, si se numeran ecuaciones, la numeración sea consecutiva
            (1, 2, 3, ...) sin duplicados ni saltos grandes.
        """
        findings: List[Finding] = []

        nums = [n for n in equation_numbers if n is not None]
        if len(nums) <= 1:
            return findings

        sorted_unique = sorted(set(nums))
        expected = list(range(sorted_unique[0], sorted_unique[0] + len(sorted_unique)))

        if sorted_unique == expected:
            return findings

        details_parts = [
            f"numeros_detectados={sorted_unique}",
            f"numeros_esperados={expected}",
        ]
        details = "; ".join(details_parts)

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:SEQUENCE",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="equations_numbering",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=details,
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="\n".join(
                    f"Línea {info['line_index'] + 1}: {info['text']}"
                    for info in eq_lines
                    if info["number"] is not None
                ),
            )
        )

        return findings

    def _check_me_002_references_exist(
        self,
        rule: Rule,
        equation_ref_set: set[int],
        equation_number_set: set[int],
    ) -> List[Finding]:
        """
        CUN-ME-002:
          - Para cada referencia a 'ecuación (n)', verificar que exista una ecuación
            numerada con ese número.
        """
        findings: List[Finding] = []

        missing = sorted(equation_ref_set - equation_number_set)
        for n in missing:
            snippet = f"ecuación ({n})"
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:MISSING_EQ:{n}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="equations_references",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=(
                        f"Se encontró una referencia a la ecuación ({n}), "
                        "pero no se detectó ninguna ecuación numerada con ese número."
                    ),
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet=snippet,
                )
            )

        return findings

    def _check_me_003_unused_equation_numbers(
        self,
        rule: Rule,
        equation_number_set: set[int],
        equation_ref_set: set[int],
    ) -> List[Finding]:
        """
        CUN-ME-003:
          - Detectar ecuaciones numeradas que nunca se referencian en el texto.
            Normalmente es una sugerencia de mejora, no un error grave.
        """
        findings: List[Finding] = []

        unused = sorted(equation_number_set - equation_ref_set)
        for n in unused:
            snippet = f"({n})"
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:UNUSED_EQ:{n}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="equations_unused",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=(
                        f"Se detectó una ecuación numerada ({n}) que no se "
                        "referencia en el texto (por ejemplo, como 'ecuación ({n})')."
                    ),
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet=snippet,
                )
            )

        return findings
