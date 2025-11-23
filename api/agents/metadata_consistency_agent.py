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
from api.rules_models import Rule


class MetadataConsistencyAgent(BaseAgent):
    """
    Agente METADATACONSISTENCY.

    Valida la coherencia básica entre:
      - el contexto declarado en la petición (LintContext),
      - el perfil detectado (DocumentProfile),
      - y algunos elementos que deberían aparecer en el texto del documento
        (por ejemplo, el nombre de la institución).

    No intenta validar el contenido académico, solo la consistencia de metadatos.
    """

    agent_id = "METADATACONSISTENCY"

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
        lower_text = text.lower()

        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)

        for rule in rules:
            if rule.rule_id == "CUN-MD-001":
                findings.extend(
                    self._check_md_001_document_type_consistency(rule, context, profile)
                )
            elif rule.rule_id == "CUN-MD-002":
                findings.extend(
                    self._check_md_002_institution_presence(rule, context, lower_text)
                )
            elif rule.rule_id == "CUN-MD-003":
                findings.extend(
                    self._check_md_003_language_consistency(rule, context, profile)
                )

        return findings

    # ------------------------------------------------------------------
    # Reglas CUN-MD-001 a CUN-MD-003
    # ------------------------------------------------------------------
    def _check_md_001_document_type_consistency(
        self,
        rule: Rule,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        """
        CUN-MD-001:
          - Verificar que el document_type declarado en el contexto coincida
            con el document_type detectado en el perfil.
        """
        findings: List[Finding] = []

        ctx_type = getattr(context, "document_type", None)
        prof_type = getattr(profile, "document_type", None)

        if not ctx_type or not prof_type:
            return findings

        if ctx_type == prof_type:
            return findings

        details = (
            f"document_type en contexto='{ctx_type}', "
            f"document_type detectado en perfil='{prof_type}'."
        )

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:DOC_TYPE_MISMATCH",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="metadata_consistency",
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
                snippet="",
            )
        )
        return findings

    def _check_md_002_institution_presence(
        self,
        rule: Rule,
        context: LintContext,
        lower_text: str,
    ) -> List[Finding]:
        """
        CUN-MD-002:
          - Verificar que el nombre de la institución declarado en el contexto
            aparezca al menos una vez en el texto del documento.
        """
        findings: List[Finding] = []

        institution = (context.institution or "").strip()
        if not institution:
            return findings

        inst_lower = institution.lower()
        if inst_lower in lower_text:
            return findings

        details = (
            "No se encontró el nombre de la institución declarado en el contexto "
            f"('{institution}') dentro del texto del documento."
        )

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:INSTITUTION_MISSING",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="metadata_consistency",
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
                snippet=lower_text[:300],
            )
        )
        return findings

    def _check_md_003_language_consistency(
        self,
        rule: Rule,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        """
        CUN-MD-003:
          - Verificar que el idioma declarado en el contexto coincida con
            el idioma detectado en el perfil (si está disponible).
        """
        findings: List[Finding] = []

        ctx_lang = getattr(context, "language", None)
        prof_lang = getattr(profile, "language", None)

        if not ctx_lang or not prof_lang:
            return findings

        if ctx_lang == prof_lang:
            return findings

        details = (
            f"language en contexto='{ctx_lang}', "
            f"language detectado en perfil='{prof_lang}'."
        )

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:LANGUAGE_MISMATCH",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="metadata_consistency",
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
                snippet="",
            )
        )
        return findings
