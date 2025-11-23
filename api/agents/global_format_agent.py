from __future__ import annotations

from typing import List

from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.rules_library import RuleLibrary
from api.rules_models import Rule, RuleSource


class GlobalFormatAgent(BaseAgent):
    """
    Agente GLOBALFORMAT.

    Valida formato global del documento usando context.metadata.
    Incluye validación de:
    - Fuente y tamaño de letra (CUN-GF-001)
    - Interlineado (CUN-GF-002)
    - Márgenes de página (CUN-GF-003)

    Respeta el filtro profile_variant para omitir reglas LOCAL
    cuando profile_variant == "apa7_international".
    """

    agent_id = "GLOBALFORMAT"

    def __init__(self, rule_library: RuleLibrary) -> None:
        super().__init__(rule_library)

    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        """Ejecuta las validaciones de formato global."""
        findings: List[Finding] = []

        # Si no hay metadata, no podemos validar nada
        if not context.metadata:
            return findings

        # Obtener reglas para este agente
        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)
        
        # Determinar si es perfil internacional
        is_international = context.profile_variant == "apa7_international"

        # Procesar cada regla
        for rule in rules:
            # Omitir reglas LOCAL si es perfil internacional
            if is_international and rule.source == RuleSource.LOCAL:
                continue

            # Validar según el tipo de regla
            if rule.rule_id == "CUN-GF-001":
                finding = self._validate_font(rule, context.metadata)
                if finding:
                    findings.append(finding)

            elif rule.rule_id == "CUN-GF-002":
                finding = self._validate_line_spacing(rule, context.metadata)
                if finding:
                    findings.append(finding)

            elif rule.rule_id == "CUN-GF-003":
                finding = self._validate_margins(rule, context.metadata)
                if finding:
                    findings.append(finding)

        return findings

    def _validate_font(self, rule: Rule, metadata: dict) -> Finding | None:
        """
        Valida CUN-GF-001: fuente y tamaño.
        
        Acepta:
        - font_family: "Times New Roman" o "Arial"
        - font_size: entre 11 y 12 (float)
        """
        font_family = metadata.get("font_family")
        font_size = metadata.get("font_size")

        issues = []

        # Validar familia de fuente
        if font_family:
            allowed_fonts = ["Times New Roman", "Arial"]
            if font_family not in allowed_fonts:
                issues.append(f"font_family='{font_family}' (debe ser 'Times New Roman' o 'Arial')")
        else:
            issues.append("font_family no especificada")

        # Validar tamaño de fuente
        if font_size is not None:
            try:
                size = float(font_size)
                if not (11.0 <= size <= 12.0):
                    issues.append(f"font_size={size} (debe estar entre 11 y 12)")
            except (ValueError, TypeError):
                issues.append(f"font_size='{font_size}' (valor inválido)")
        else:
            issues.append("font_size no especificado")

        if issues:
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:FONT",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=", ".join(issues),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )
        return None

    def _validate_line_spacing(self, rule: Rule, metadata: dict) -> Finding | None:
        """
        Valida CUN-GF-002: interlineado.
        
        Acepta:
        - line_spacing: ~2.0 (rango [1.8, 2.2])
        """
        line_spacing = metadata.get("line_spacing")

        if line_spacing is None:
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:SPACING",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details="line_spacing no especificado",
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )

        try:
            spacing = float(line_spacing)
            if not (1.8 <= spacing <= 2.2):
                return Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:SPACING",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="global_format",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=f"line_spacing={spacing} (debe estar entre 1.8 y 2.2)",
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet="",
                )
        except (ValueError, TypeError):
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:SPACING",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=f"line_spacing='{line_spacing}' (valor inválido)",
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )

        return None

    def _validate_margins(self, rule: Rule, metadata: dict) -> Finding | None:
        """
        Valida CUN-GF-003: márgenes de página.
        
        Acepta:
        - page_margins: dict con top_cm, bottom_cm, left_cm, right_cm
        - valores en rango [2.3, 2.7]
        """
        page_margins = metadata.get("page_margins")

        if not page_margins:
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:MARGINS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details="page_margins no especificados",
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )

        if not isinstance(page_margins, dict):
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:MARGINS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=f"page_margins debe ser un diccionario, recibido: {type(page_margins).__name__}",
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )

        # Validar cada margen
        required_margins = ["top_cm", "bottom_cm", "left_cm", "right_cm"]
        issues = []

        for margin_key in required_margins:
            margin_value = page_margins.get(margin_key)
            
            if margin_value is None:
                issues.append(f"{margin_key} no especificado")
                continue

            try:
                margin = float(margin_value)
                if not (2.3 <= margin <= 2.7):
                    issues.append(f"{margin_key}={margin}cm (debe estar entre 2.3 y 2.7)")
            except (ValueError, TypeError):
                issues.append(f"{margin_key}='{margin_value}' (valor inválido)")

        if issues:
            return Finding(
                id=f"{self.agent_id}:{rule.rule_id}:MARGINS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="global_format",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=", ".join(issues),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="",
            )

        return None
