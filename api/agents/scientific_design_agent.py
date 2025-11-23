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
from api.rules_models import Rule


RE_SECTION_HEADER = re.compile(r"^[A-ZÁÉÍÓÚÑ ]{3,}$")


def _normalize_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.replace("\r\n", "\n").split("\n")]


class ScientificDesignAgent(BaseAgent):
    """
    Agente SCIENTIFICDESIGN.

    Aplica reglas sobre la estructura de trabajos estrictamente científicos:
    artículos, informes de investigación y tesis/trabajos de grado.

    Solo se activa cuando el perfil indica un tipo de documento de investigación:
      - document_type in {"articulo_cientifico", "informe_investigacion", "tesis_trabajo_grado"}.
    """

    agent_id = "SCIENTIFICDESIGN"

    def __init__(self, rule_library: RuleLibrary) -> None:
        super().__init__(rule_library)

    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        findings: List[Finding] = []

        if profile.document_type not in {
            "articulo_cientifico",
            "informe_investigacion",
            "tesis_trabajo_grado",
        }:
            # No aplicamos estas reglas a ACAs ni a otros tipos de documento.
            return findings

        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)
        text = document_text or ""
        lines = _normalize_lines(text)
        upper_lines = [ln.upper() for ln in lines]

        section_indices = self._detect_section_headers(upper_lines)

        for rule in rules:
            if rule.rule_id == "CUN-SD-001":
                findings.extend(
                    self._check_sd_001_problem_and_objectives(
                        rule, text, upper_lines
                    )
                )
            elif rule.rule_id == "CUN-SD-002":
                findings.extend(self._check_sd_002_method_section(rule, section_indices))
            elif rule.rule_id == "CUN-SD-003":
                findings.extend(
                    self._check_sd_003_results_and_discussion(rule, section_indices)
                )
            elif rule.rule_id == "CUN-SD-004":
                findings.extend(
                    self._check_sd_004_coherent_imryd_order(rule, section_indices)
                )
            elif rule.rule_id == "CUN-SD-005":
                findings.extend(
                    self._check_sd_005_objectives_vs_conclusions(
                        rule, text, upper_lines
                    )
                )
            elif rule.rule_id == "CUN-SD-006":
                findings.extend(self._check_sd_006_limitations(rule, upper_lines))

        return findings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _detect_section_headers(self, upper_lines: List[str]) -> dict[str, int]:
        """
        Devuelve un diccionario aproximado de encabezados importantes
        a su primera línea (índice).
        """
        headers: dict[str, int] = {}
        for idx, ln in enumerate(upper_lines):
            if not ln:
                continue

            # Encabezados candidatos (líneas en mayúsculas sin punto final)
            if RE_SECTION_HEADER.match(ln):
                norm = ln.strip()

                # Normalizamos algunas variantes frecuentes
                if "MÉTODO" in norm or "METODOLOG" in norm:
                    headers.setdefault("METODO", idx)
                elif "RESULTADOS" in norm:
                    headers.setdefault("RESULTADOS", idx)
                elif "DISCUSIÓN" in norm or "ANÁLISIS Y DISCUSIÓN" in norm:
                    headers.setdefault("DISCUSION", idx)
                elif "CONCLUSIONES" in norm:
                    headers.setdefault("CONCLUSIONES", idx)
                elif "INTRODUCCIÓN" in norm:
                    headers.setdefault("INTRODUCCION", idx)
                elif "MARCO TEÓRICO" in norm or "MARCO REFERENCIAL" in norm:
                    headers.setdefault("MARCO_TEORICO", idx)

        return headers

    # ------------------------------------------------------------------
    # Reglas CUN-SD-001 a CUN-SD-006
    # ------------------------------------------------------------------
    def _check_sd_001_problem_and_objectives(
        self,
        rule: Rule,
        text: str,
        upper_lines: List[str],
    ) -> List[Finding]:
        """
        CUN-SD-001:
          - Verificar que exista al menos una referencia clara a:
            'problema de investigación' u 'objetivo general' / 'objetivos'.
        """
        findings: List[Finding] = []

        has_problem = any("PROBLEMA DE INVESTIGACIÓN" in ln for ln in upper_lines)
        has_objective = any("OBJETIVO GENERAL" in ln or "OBJETIVOS" in ln for ln in upper_lines)

        if has_problem or has_objective:
            return findings

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:NO_PROBLEM_OBJECTIVES",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "No se detectaron encabezados ni frases que indiquen claramente "
                    "el problema de investigación o los objetivos del estudio."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="\n".join(upper_lines[:20]),
            )
        )
        return findings

    def _check_sd_002_method_section(
        self,
        rule: Rule,
        section_indices: dict[str, int],
    ) -> List[Finding]:
        """
        CUN-SD-002:
          - Exigir presencia de una sección de 'Método' o 'Metodología'.
        """
        findings: List[Finding] = []

        if "METODO" in section_indices:
            return findings

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:NO_METHOD",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "No se identificó una sección con encabezado 'MÉTODO' "
                    "o 'METODOLOGÍA'."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )
        )
        return findings

    def _check_sd_003_results_and_discussion(
        self,
        rule: Rule,
        section_indices: dict[str, int],
    ) -> List[Finding]:
        """
        CUN-SD-003:
          - Exigir presencia de secciones 'Resultados' y 'Discusión'
            (o equivalente 'Análisis y Discusión').
        """
        findings: List[Finding] = []

        has_results = "RESULTADOS" in section_indices
        has_discussion = "DISCUSION" in section_indices

        if has_results and has_discussion:
            return findings

        missing_parts = []
        if not has_results:
            missing_parts.append("RESULTADOS")
        if not has_discussion:
            missing_parts.append("DISCUSIÓN")

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:MISSING_SECTIONS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "No se identificaron las siguientes secciones de informe científico: "
                    + ", ".join(missing_parts)
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )
        )
        return findings

    def _check_sd_004_coherent_imryd_order(
        self,
        rule: Rule,
        section_indices: dict[str, int],
    ) -> List[Finding]:
        """
        CUN-SD-004:
          - Verificar un orden razonable de secciones tipo IMRyD:
            Introducción / Marco teórico → Método → Resultados → Discusión → Conclusiones.
        """
        findings: List[Finding] = []

        # Si faltan muchas secciones, no forzamos este check.
        needed_keys = {"METODO", "RESULTADOS", "DISCUSION", "CONCLUSIONES"}
        present = {k for k in needed_keys if k in section_indices}
        if len(present) < 3:
            return findings

        idx = section_indices
        order_ok = True

        # Cheques aproximados de orden creciente
        pairs = [
            ("INTRODUCCION", "METODO"),
            ("MARCO_TEORICO", "METODO"),
            ("METODO", "RESULTADOS"),
            ("RESULTADOS", "DISCUSION"),
            ("DISCUSION", "CONCLUSIONES"),
        ]
        for first, second in pairs:
            if first in idx and second in idx and idx[first] > idx[second]:
                order_ok = False
                break

        if order_ok:
            return findings

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:ORDER",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "El orden de las secciones principales del informe de investigación "
                    "no sigue la secuencia típica (Introducción/Marco teórico → Método "
                    "→ Resultados → Discusión → Conclusiones)."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )
        )
        return findings

    def _check_sd_005_objectives_vs_conclusions(
        self,
        rule: Rule,
        text: str,
        upper_lines: List[str],
    ) -> List[Finding]:
        """
        CUN-SD-005:
          - Verificación aproximada de que se mencionan 'objetivos' en el cuerpo
            y 'conclusiones' al final. Si una de las dos partes falta, se avisa.
        """
        findings: List[Finding] = []

        has_objectives = any("OBJETIVO GENERAL" in ln or "OBJETIVOS ESPECÍFICOS" in ln for ln in upper_lines)
        has_conclusions = any("CONCLUSIONES" in ln for ln in upper_lines)

        if has_objectives and has_conclusions:
            return findings

        missing_parts = []
        if not has_objectives:
            missing_parts.append("objetivos")
        if not has_conclusions:
            missing_parts.append("conclusiones")

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:OBJECTIVES_CONCLUSIONS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "En el diseño científico se espera identificar objetivos y conclusiones. "
                    "En este documento no se detectaron claramente: " + ", ".join(missing_parts)
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="\n".join(upper_lines[-20:]),
            )
        )
        return findings

    def _check_sd_006_limitations(
        self,
        rule: Rule,
        upper_lines: List[str],
    ) -> List[Finding]:
        """
        CUN-SD-006:
          - Sugerencia de mencionar limitaciones del estudio, si corresponde.
            No es un error grave (normalmente 'suggestion').
        """
        findings: List[Finding] = []

        has_limitations = any("LIMITACIONES" in ln or "LIMITES DEL ESTUDIO" in ln for ln in upper_lines)
        if has_limitations:
            return findings

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:NO_LIMITATIONS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="scientific_design",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "No se identificó una sección o mención explícita de las limitaciones del estudio; "
                    "es recomendable señalar alcances y límites del trabajo de investigación."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )
        )
        return findings
