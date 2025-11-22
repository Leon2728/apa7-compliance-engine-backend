from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

from api.agents.base_agent import BaseAgent
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    FindingLocation,
)
from api.rules_library import RuleLibrary
from api.rules_models import Rule, CheckType


CITATION_PARENTHETICAL_PATTERN = re.compile(
    r"\(([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+),\s*(\d{4})\)"
)

CITATION_NARRATIVE_PATTERN = re.compile(
    r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+)\s*\((\d{4})\)"
)

CITATION_BAD_NO_COMMA_PATTERN = re.compile(
    r"\(([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+)\s+(\d{4})\)"
)

CITATION_BAD_NARRATIVE_COMMAS_PATTERN = re.compile(
    r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+),\s*(\d{4}),"
)

CITATION_THREE_AUTHORS_FULL_PATTERN = re.compile(
    r"\(([A-ZÁÉÍÓÚÑ][^()]+?&[^()]+?),\s*(\d{4})\)"
)


class InTextCitationsAgent(BaseAgent):
    """
    Agente INTEXTCITATIONS.

    Implementa comprobaciones básicas basadas en las reglas:
      - CUN-IC-001 a CUN-IC-006

    No intenta resolver todos los casos límite, pero proporciona una
    validación razonable para trabajos típicos de la CUN.
    """

    agent_id = "INTEXTCITATIONS"

    def __init__(self, rule_library: RuleLibrary) -> None:
        super().__init__(rule_library)

    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        rules: List[Rule] = self.rule_library.get_rules_for_agent(self.agent_id)
        findings: List[Finding] = []

        # Normalizamos texto para análisis simple
        text = document_text or ""
        upper_text = text.upper()

        for rule in rules:
            # Usamos rule_id para decidir la lógica de detección;
            # checkType se respeta pero no limita aquí.
            if rule.rule_id == "CUN-IC-001":
                findings.extend(self._check_ic_001(rule, text, upper_text))
            elif rule.rule_id == "CUN-IC-002":
                findings.extend(self._check_ic_002(rule, text))
            elif rule.rule_id == "CUN-IC-003":
                findings.extend(self._check_ic_003(rule, text))
            elif rule.rule_id == "CUN-IC-004":
                findings.extend(self._check_ic_004(rule, text))
            elif rule.rule_id == "CUN-IC-005":
                findings.extend(self._check_ic_005(rule, text))
            elif rule.rule_id == "CUN-IC-006":
                findings.extend(self._check_ic_006(rule, text))

        return findings

    # ------------------------------------------------------------------
    # Helpers de extracción
    # ------------------------------------------------------------------
    def _extract_references_block(self, text: str) -> str:
        """
        Extrae el bloque de texto a partir de 'REFERENCIAS' o 'BIBLIOGRAFÍA'.
        Si no se encuentra, devuelve cadena vacía.
        """
        upper = text.upper()
        idx = upper.find("REFERENCIAS")
        if idx == -1:
            idx = upper.find("BIBLIOGRAFÍA")
        if idx == -1:
            return ""
        return text[idx:]

    def _extract_reference_entries(self, references_block: str) -> List[str]:
        """
        Divide el bloque de referencias en entradas aproximadas, línea a línea.
        No es perfecto, pero funciona para la mayoría de listas simples.
        """
        lines = [ln.strip() for ln in references_block.splitlines()]
        # Filtrar encabezado y líneas vacías
        filtered: List[str] = []
        for ln in lines:
            if not ln:
                continue
            upper_ln = ln.upper()
            if upper_ln.startswith("REFERENCIAS") or upper_ln.startswith("BIBLIOGRAFÍA"):
                continue
            filtered.append(ln)
        return filtered

    def _extract_cited_author_year_pairs(self, text: str) -> Set[Tuple[str, str]]:
        pairs: Set[Tuple[str, str]] = set()

        for m in CITATION_PARENTHETICAL_PATTERN.finditer(text):
            author = m.group(1).strip()
            year = m.group(2).strip()
            pairs.add((author.upper(), year))

        for m in CITATION_NARRATIVE_PATTERN.finditer(text):
            author = m.group(1).strip()
            year = m.group(2).strip()
            pairs.add((author.upper(), year))

        return pairs

    def _extract_reference_author_year_pairs(
        self,
        reference_entries: List[str],
    ) -> Set[Tuple[str, str]]:
        """
        Extrae pares (apellido, año) a partir de líneas de referencias
        con patrón básico 'Apellido, ... (YYYY)'.
        """
        pairs: Set[Tuple[str, str]] = set()
        pattern = re.compile(
            r"^([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\- ]+?),.*\((\d{4})\)"
        )
        for entry in reference_entries:
            m = pattern.search(entry)
            if not m:
                continue
            author = m.group(1).strip()
            year = m.group(2).strip()
            pairs.add((author.upper(), year))
        return pairs

    # ------------------------------------------------------------------
    # Reglas CUN-IC-001 a CUN-IC-006
    # ------------------------------------------------------------------
    def _check_ic_001(
        self,
        rule: Rule,
        text: str,
        upper_text: str,
    ) -> List[Finding]:
        """
        CUN-IC-001:
          - Si hay sección de Referencias/Bibliografía
          - y no hay NINGUNA cita (autor, año)
          => error global.
        """
        findings: List[Finding] = []

        has_references = "REFERENCIAS" in upper_text or "BIBLIOGRAFÍA" in upper_text
        if not has_references:
            return findings

        has_any_citation = bool(CITATION_PARENTHETICAL_PATTERN.search(text)) or bool(
            CITATION_NARRATIVE_PATTERN.search(text)
        )
        if has_any_citation:
            return findings

        findings.append(
            Finding(
                id=f"{self.agent_id}:{rule.rule_id}:NO_CITATIONS",
                agent_id=self.agent_id,
                rule_id=rule.rule_id,
                severity=rule.severity,
                category="in_text_citations",
                message=rule.description,
                suggestion=rule.auto_fix_hint,
                details=(
                    "Se detectó una sección de referencias, pero no se encontraron "
                    "citas en el texto con patrón autor-año."
                ),
                location=FindingLocation(
                    line=None,
                    column=None,
                    start_offset=None,
                    end_offset=None,
                    section=None,
                ),
                snippet="REFERENCIAS ...",
            )
        )

        return findings

    def _check_ic_002(self, rule: Rule, text: str) -> List[Finding]:
        """
        CUN-IC-002:
          - Detectar citas parentéticas sin coma: (Apellido 2020)
        """
        findings: List[Finding] = []
        for m in CITATION_BAD_NO_COMMA_PATTERN.finditer(text):
            snippet = m.group(0)
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:NO_COMMA:{m.start()}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="in_text_citations_format",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details="Cita parentética sin coma entre apellido y año.",
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=m.start(),
                        end_offset=m.end(),
                        section=None,
                    ),
                    snippet=snippet,
                )
            )
        return findings

    def _check_ic_003(self, rule: Rule, text: str) -> List[Finding]:
        """
        CUN-IC-003:
          - Detectar citas narrativas con formato 'Apellido, 2020,' en lugar de 'Apellido (2020)'.
        """
        findings: List[Finding] = []
        for m in CITATION_BAD_NARRATIVE_COMMAS_PATTERN.finditer(text):
            snippet = m.group(0)
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:NARRATIVE_COMMAS:{m.start()}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="in_text_citations_format",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details="Cita narrativa con año separado por comas en lugar de paréntesis.",
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=m.start(),
                        end_offset=m.end(),
                        section=None,
                    ),
                    snippet=snippet,
                )
            )
        return findings

    def _check_ic_004(self, rule: Rule, text: str) -> List[Finding]:
        """
        CUN-IC-004:
          - Detectar citas con tres o más autores listados completos y proponer uso de 'et al.'.
        """
        findings: List[Finding] = []
        for m in CITATION_THREE_AUTHORS_FULL_PATTERN.finditer(text):
            snippet = m.group(0)
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:THREE_AUTHORS:{m.start()}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="in_text_citations_authors",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=(
                        "Cita con tres o más autores listados completos; APA 7 "
                        "recomienda usar solo el primer autor seguido de 'et al.'."
                    ),
                    location=FindingLocation(
                        line=None,
                        column=None,
                        start_offset=m.start(),
                        end_offset=m.end(),
                        section=None,
                    ),
                    snippet=snippet,
                )
            )
        return findings

    def _check_ic_005(self, rule: Rule, text: str) -> List[Finding]:
        """
        CUN-IC-005:
          - Citas que no tienen referencia correspondiente.
          - Esta comprobación es aproximada y depende de la extracción
            básica de apellido y año en referencias.
        """
        findings: List[Finding] = []

        refs_block = self._extract_references_block(text)
        if not refs_block:
            return findings

        reference_entries = self._extract_reference_entries(refs_block)
        ref_pairs = self._extract_reference_author_year_pairs(reference_entries)
        cited_pairs = self._extract_cited_author_year_pairs(text)

        # Pares citados que no están en referencias
        missing_refs = cited_pairs - ref_pairs
        for author, year in sorted(missing_refs):
            snippet = f"({author.title()}, {year})"
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:MISSING_REF:{author}:{year}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="in_text_citations_references",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=(
                        f"Se encontró una cita a {author.title()} ({year}) "
                        "que no tiene entrada correspondiente en la lista de referencias."
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

    def _check_ic_006(self, rule: Rule, text: str) -> List[Finding]:
        """
        CUN-IC-006:
          - Referencias incluidas en la lista que nunca se citan.
        """
        findings: List[Finding] = []

        refs_block = self._extract_references_block(text)
        if not refs_block:
            return findings

        reference_entries = self._extract_reference_entries(refs_block)
        ref_pairs = self._extract_reference_author_year_pairs(reference_entries)
        cited_pairs = self._extract_cited_author_year_pairs(text)

        # Referencias sin cita
        unused_refs = ref_pairs - cited_pairs
        for author, year in sorted(unused_refs):
            snippet = f"{author.title()} ({year})"
            findings.append(
                Finding(
                    id=f"{self.agent_id}:{rule.rule_id}:UNUSED_REF:{author}:{year}",
                    agent_id=self.agent_id,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    category="references_unused",
                    message=rule.description,
                    suggestion=rule.auto_fix_hint,
                    details=(
                        f"La obra de {author.title()} ({year}) aparece en la lista "
                        "de referencias pero no se cita en el texto."
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
