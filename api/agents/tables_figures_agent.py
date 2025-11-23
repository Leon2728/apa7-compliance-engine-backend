from __future__ import annotations

from typing import List, Optional

from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.models.layout_models import DocumentLayout
from api.rules_library import RuleLibrary
from api.rules_models import Rule, CheckType, RuleSource


class TablesFiguresAgent(BaseAgent):
    """
    Agente TABLESFIGURES.

    Usa el layout pasado en LintContext.layout (DocumentLayout) para validar:

      - Estilo de líneas en tablas (sin verticales, pocas horizontales internas).
      - Tamaño de imágenes/figuras (rango mínimo/máximo en cm).

    IMPORTANTE:
      - Este agente asume que el frontend ha construido DocumentLayout
        a partir del archivo DOCX/ODT (por ejemplo con python-docx).
    """

    agent_id = "TABLESFIGURES"

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

        layout: Optional[DocumentLayout] = context.layout
        if layout is None:
            # Sin layout, no podemos evaluar estas reglas de diseño.
            return findings

        for rule in rules:
                        if is_international and rule.source == RuleSource.LOCAL:
                                            continue
            if rule.check_type != CheckType.semantic:
                # Este agente se centra en reglas semánticas basadas en layout.
                continue

            if rule.rule_id == "CUN-TF-007":
                findings.extend(self._check_table_borders(rule, layout))
            elif rule.rule_id == "CUN-TF-008":
                findings.extend(self._check_image_sizes(rule, layout))

        return findings

    # ------------------------------------------------------------------
    # Validación de líneas de tablas
    # ------------------------------------------------------------------
    def _check_table_borders(self, rule: Rule, layout: DocumentLayout) -> List[Finding]:
        findings: List[Finding] = []

        for table in layout.tables:
            b = table.borders

            # APA: sin líneas verticales y pocas horizontales internas
            has_verticals = b.has_vertical_inner_borders or b.has_vertical_outer_borders
            too_many_hlines = b.horizontal_internal_lines_count > 3

            if not (has_verticals or too_many_hlines):
                continue

            label = table.label or f"Tabla {table.index + 1}"

            details_parts = []
            if has_verticals:
                details_parts.append("la tabla tiene líneas verticales")
            if too_many_hlines:
                details_parts.append(
                    f"la tabla tiene {b.horizontal_internal_lines_count} "
                    "líneas horizontales internas"
                )

            details = "; ".join(details_parts)

            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:TABLE-{table.index}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="tables_format",
                    message=f"{rule.description} ({label}).",
                    suggestion=rule.auto_fix_hint,
                    details=details,
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet=label,
                )
            )

        return findings

    # ------------------------------------------------------------------
    # Validación de tamaños de imágenes
    # ------------------------------------------------------------------
    def _check_image_sizes(self, rule: Rule, layout: DocumentLayout) -> List[Finding]:
        findings: List[Finding] = []

        # Rango razonable de ejemplo (ajustable según guía CUN):
        min_width_cm = 4.0
        max_width_cm = 17.0  # algo menor que el ancho útil de una página A4
        min_height_cm = 3.0

        for img in layout.images:
            too_small = img.width_cm < min_width_cm or img.height_cm < min_height_cm
            too_large = img.width_cm > max_width_cm

            if not (too_small or too_large):
                continue

            label = img.label or f"Figura {img.index + 1}"

            details_parts = [
                f"tamaño detectado: {img.width_cm:.1f}×{img.height_cm:.1f} cm"
            ]
            if too_small:
                details_parts.append("la figura es demasiado pequeña para ser legible")
            if too_large:
                details_parts.append("la figura puede exceder los márgenes de la página")

            details = "; ".join(details_parts)

            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:IMG-{img.index}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="figures_format",
                    message=f"{rule.description} ({label}).",
                    suggestion=rule.auto_fix_hint,
                    details=details,
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet=label,
                )
            )

        return findings
