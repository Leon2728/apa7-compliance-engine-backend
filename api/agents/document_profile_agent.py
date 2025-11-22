from __future__ import annotations

import re
from typing import List, Tuple

from api.models.lint_models import (
    DocumentProfile,
    Finding,
    FindingLocation,
    LintContext,
)
from api.rules_library import RuleLibrary
from api.rules_models import Severity


class DocumentProfileAgent:
    """
    Agente DOCUMENTPROFILE.

    Su función principal es:
      - Inferir un perfil básico del documento:
          * idioma predominante
          * tipo (si viene en el contexto)
          * institución, estilo
      - Generar hallazgos relacionados con el perfil
        (por ejemplo: discrepancia de idioma declarado vs detectado).

    Este agente es especial:
      - NO sigue el contrato BaseAgent.run(), porque su salida incluye
        un DocumentProfile explícito.
      - Por eso expone el método `analyze(...) -> (profile, findings)`.
    """

    agent_id = "DOCUMENTPROFILE"

    def __init__(self, rule_library: RuleLibrary) -> None:
        self.rule_library = rule_library

    async def analyze(
        self,
        document_text: str,
        context: LintContext,
    ) -> Tuple[DocumentProfile, List[Finding]]:
        """
        Analiza el documento para inferir un perfil básico y
        devuelve:
          - DocumentProfile inferido
          - Lista de Finding relacionados con el perfil
        """
        text_sample = document_text[:5000] if document_text else ""

        # -------------------------------
        # Heurística muy simple de idioma
        # -------------------------------
        es_tokens = len(
            re.findall(
                r"\b(el|la|de|que|y|en|los|las|un|una|para|por)\b",
                text_sample,
                flags=re.IGNORECASE,
            )
        )
        en_tokens = len(
            re.findall(
                r"\b(the|of|and|in|for|to|with|a|an|on)\b",
                text_sample,
                flags=re.IGNORECASE,
            )
        )

        if es_tokens > en_tokens:
            inferred_lang = "es"
        elif en_tokens > es_tokens:
            inferred_lang = "en"
        else:
            # Si no está claro, usamos lo que venga en el contexto
            inferred_lang = context.language or "es"

        # Tipo de documento: de momento usamos el declarado
        inferred_type = context.document_type

        raw_tags: List[str] = []
        if re.search(r"\bmetodolog[ií]a\b", text_sample, flags=re.IGNORECASE):
            raw_tags.append("has_method_section")
        if re.search(r"\bresultados\b", text_sample, flags=re.IGNORECASE):
            raw_tags.append("has_results_section")
        if re.search(r"\bconclusiones\b", text_sample, flags=re.IGNORECASE):
            raw_tags.append("has_conclusions_section")

        confidence = 0.4
        if inferred_type:
            confidence += 0.3
        if raw_tags:
            confidence += 0.2
        if inferred_lang == context.language:
            confidence += 0.1

        profile = DocumentProfile(
            inferred_type=inferred_type,
            language=inferred_lang,
            style=context.style,
            institution=context.institution,
            confidence=min(confidence, 1.0),
            raw_tags=raw_tags,
        )

        findings: List[Finding] = []

        # Hallazgo: idioma detectado difiere del declarado
        if inferred_lang != context.language:
            findings.append(
                Finding(
                    id="DOCUMENTPROFILE:LANG-MISMATCH",
                    agent_id=self.agent_id,
                    rule_id=None,
                    severity=Severity.warning,
                    category="document_profile",
                    message=(
                        "El idioma detectado en el texto no coincide con el "
                        "idioma declarado en el contexto."
                    ),
                    suggestion=(
                        "Verifica que el idioma del documento sea consistente o ajusta "
                        "el idioma declarado en el contexto de análisis."
                    ),
                    details=(
                        f"Idioma detectado: {inferred_lang}. "
                        f"Idioma declarado: {context.language}."
                    ),
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=None,
                        end_offset=None,
                        section=None,
                    ),
                    snippet=text_sample[:300],
                )
            )

        return profile, findings
