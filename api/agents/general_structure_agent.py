from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.rules_library import RuleLibrary
from api.rules_models import CheckType, Rule, Severity, DetectionScope, RuleSource
from api.llm.rule_runner import LLMRuleRunner


class GeneralStructureAgent(BaseAgent):
    """
    Agente GENERALSTRUCTURE.

    Ahora soporta:
    - Reglas regex a nivel documento.
    - Reglas regex con scope="section" aplicadas solo dentro de secciones objetivo.
    - Reglas estructurales (checkType="structural") basadas en presencia/orden de secciones.

    Las reglas semantic se siguen dejando para una capa posterior más robusta,
    pero ya podemos aprovechar sectionTargets y scope para muchas validaciones
    de estructura básica.
    """

    agent_id = "GENERALSTRUCTURE"

    def __init__(self, rule_library: RuleLibrary, llm_rule_runner: Optional[LLMRuleRunner] = None) -> None:        super().__init__(rule_library)
        super().__init__(rule_library)
        self.llm_rule_runner = llm_rule_runner    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)
                is_international = context.profile_variant == "apa7_international"
        findings: List[Finding] = []

        if not document_text:
            # Documento vacío: todas las reglas estructurales/regex fallan de facto.
            for rule in rules:
                            if is_international and rule.source == RuleSource.LOCAL:
                                                continue
                findings.append(self._build_finding_empty_doc(rule))
            return findings

        lines = document_text.splitlines()
        section_index = self._detect_sections(lines)

        for rule in rules:
            # No exigimos "Palabras clave" en actividades de curso (ACA)
            if rule.rule_id == "CUN-GS-002" and profile.document_type == "actividad_curso":
                continue

            # 1) Reglas estructurales: orden/presencia de secciones
            if rule.check_type == CheckType.structural:
                violated = self._check_structural_rule(rule, section_index)
                if violated:
                    findings.append(
                        self._build_finding_generic(
                            rule=rule,
                            details=(
                                "No se cumple la estructura esperada de secciones "
                                "según la regla. Revisa la presencia y el orden de las secciones objetivo."
                            ),
                            snippet=document_text[:300],
                        )
                    )
                continue

            # 2) Reglas regex (document o section)
            if rule.check_type == CheckType.regex:
                scope = rule.detection_hints.scope
                if scope == DetectionScope.section:
                    violated = self._check_regex_section_scope(
                        rule=rule,
                        lines=lines,
                        section_index=section_index,
                    )
                else:
                    violated = self._check_regex_document_scope(
                        rule=rule,
                        document_text=document_text,
                    )

                if violated:
                    findings.append(
                        self._build_finding_generic(
                            rule=rule,
                            details=(
                                "No se encontró ningún patrón esperado de la regla en el ámbito indicado "
                                "(documento o sección). Revisa la presencia, nombre y contenido de la sección."
                            ),
                            snippet=document_text[:300],
                        )
                    )
                continue

            # 3) Reglas semantic: por ahora NO generamos findings automáticos
            # (requiere análisis más profundo). Se dejan para una fase de
            # implementación con spaCy / modelos lingüísticos.
            # Aquí simplemente las ignoramos para no introducir ruido.
            if rule.check_type == CheckType.semantic:
                continue
        # 4) Reglas llm_semantic: usar LLMRuleRunner si está disponible
        if rule.check_type == CheckType.llm_semantic:
            if self.llm_rule_runner is not None:
                llm_findings = await self.llm_rule_runner.run_llm_rule(
                    rule=rule,
                    document_text=document_text,
                    context=context,
                    profile=profile,
                )
                findings.extend(llm_findings)
            # Si no hay llm_rule_runner, simplemente skippeamos sin error
            continue
        return findings

    # ------------------------------------------------------------------
    # Helpers de detección de secciones
    # ------------------------------------------------------------------
    def _detect_sections(self, lines: List[str]) -> Dict[str, int]:
        """
        Detecta posibles encabezados de sección basados en líneas
        que están en MAYÚSCULAS o que empiezan en columna 0 y son cortas.

        Devuelve un dict: nombre_normalizado -> índice de línea.
        """
        sections: Dict[str, int] = {}
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Heurística: línea en mayúsculas o muy "encabezado"
            if stripped.isupper() or (len(stripped) < 60 and not stripped.endswith(".")):
                key = stripped.upper()
                # Registramos solo la primera aparición
                sections.setdefault(key, idx)

        return sections

    # ------------------------------------------------------------------
    # Chequeos estructurales
    # ------------------------------------------------------------------
    def _check_structural_rule(
        self,
        rule: Rule,
        section_index: Dict[str, int],
    ) -> bool:
        """
        Devuelve True si la regla estructural se considera VIOLADA.

        Lógica simple:
        - Si la regla tiene sectionTargets, verificamos:
            * que todas existan (presencia).
            * que aparezcan en orden creciente de línea (si hay >1).
        """
        section_targets = rule.detection_hints.section_targets or []
        if not section_targets:
            # Sin secciones objetivo, no podemos evaluar esta regla aún.
            return False

        missing = []
        positions: List[int] = []
        for target in section_targets:
            key = target.upper()
            if key not in section_index:
                missing.append(target)
            else:
                positions.append(section_index[key])

        if missing:
            # Falta al menos una sección requerida → violación
            return True

        # Si todas están, verificamos orden (creciente)
        if any(earlier > later for earlier, later in zip(positions, positions[1:])):
            return True

        return False

    # ------------------------------------------------------------------
    # Chequeos regex: documento completo
    # ------------------------------------------------------------------
    def _check_regex_document_scope(self, rule: Rule, document_text: str) -> bool:
        """
        Devuelve True si la regla regex a nivel documento se considera VIOLADA.
        Es decir: si NINGÚN patrón de detection_hints.regex aparece.
        """
        patterns = rule.detection_hints.regex or []
        if not patterns:
            return False

        for pattern in patterns:
            try:
                if re.search(pattern, document_text, flags=re.MULTILINE):
                    return False  # se cumple
            except re.error:
                continue

        return True  # no se encontró ningún patrón

    # ------------------------------------------------------------------
    # Chequeos regex: scope = "section"
    # ------------------------------------------------------------------
    def _check_regex_section_scope(
        self,
        rule: Rule,
        lines: List[str],
        section_index: Dict[str, int],
    ) -> bool:
        """
        Devuelve True si la regla regex con scope=section se considera VIOLADA.

        Lógica:
        - Identificamos las secciones objetivo (sectionTargets).
        - Extraemos el bloque de texto de cada sección hasta la siguiente sección.
        - Buscamos los patrones regex dentro de esos bloques.
        - Si en ninguna sección objetivo se encuentra ningún patrón → violación.
        """
        section_targets = rule.detection_hints.section_targets or []
        patterns = rule.detection_hints.regex or []

        if not section_targets or not patterns:
            return False

        # Obtenemos las posiciones ordenadas de todas las secciones detectadas
        sorted_sections = sorted(
            section_index.items(),
            key=lambda kv: kv[1],
        )

        # Función auxiliar para extraer bloque de una sección
        def get_section_block(start_line: int) -> str:
            for _, idx in sorted_sections:
                if idx > start_line:
                    end_line = idx
                    break
            else:
                end_line = len(lines)

            return "\n".join(lines[start_line:end_line])

        # Revisamos cada sección objetivo
        for target in section_targets:
            key = target.upper()
            if key not in section_index:
                # Si secciones requeridas faltan, la parte estructural ya lo marcará;
                # aquí solo nos centramos en el contenido cuando sí existe.
                continue

            start_line = section_index[key]
            block = get_section_block(start_line)

            for pattern in patterns:
                try:
                    if re.search(pattern, block, flags=re.MULTILINE):
                        return False  # se cumple en al menos una sección objetivo
                except re.error:
                    continue

        # Si llegamos aquí, no se encontró ningún patrón en ninguna sección objetivo
        return True

    # ------------------------------------------------------------------
    # Builders de findings
    # ------------------------------------------------------------------
    def _build_finding_empty_doc(self, rule: Rule) -> Finding:
        return Finding(
            id=f"{self.agent_id}:{rule.rule_id}",
            agent_id=self.agent_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            category="general_structure",
            message=rule.description,
            suggestion=rule.auto_fix_hint,
            details=(
                "El documento está vacío o no contiene texto suficiente para "
                "verificar la estructura general."
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

    def _build_finding_generic(
        self,
        rule: Rule,
        details: str,
        snippet: str,
    ) -> Finding:
        return Finding(
            id=f"{self.agent_id}:{rule.rule_id}",
            agent_id=self.agent_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            category="general_structure",
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
            snippet=snippet,
        )
