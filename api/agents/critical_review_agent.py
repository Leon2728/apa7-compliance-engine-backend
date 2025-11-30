from __future__ import annotations
from typing import Optional
from api.models.lint_models import (
    LintContext,
    DocumentProfile,
    Finding,
    CriticalReviewSummary,
    IssuesByCategory,
    TopIssue,
    PolicyComplianceSummary,
    ResolvedGuidelines,
)
from api.rules_library import RuleLibrary


class CriticalReviewAgent:
    """
    Meta-agente que revisa críticamente los hallazgos (findings) del documento
    y genera un resumen ejecutivo orientado a acción.
    
    NO analiza el texto crudo, sino que:
    - Consume todos los findings
    - Utiliza el perfil del documento (DocumentProfile)
    - Considera las guías aplicadas (ResolvedGuidelines)
    - Integra el resultado de policy_compliance (si está disponible)
    
    Produce un CriticalReviewSummary con:
    - Estado principal (OK, NEEDS_IMPROVEMENT, CRITICAL)
    - Issues agrupados por categoría
    - Top issues (máximo 5)
    - Orden sugerido de correcciones
    """
    
    agent_id = "critical_review"
    
    # Prioridad hardcodeada de categorías
    CATEGORY_PRIORITY = [
        "structure",
        "citations",
        "references",
        "math_format",
        "math_equations",
        "code_format",
        "code_blocks",
        "academic_style",
        "format",
        "layout",
        "metadata",
    ]
    
    def __init__(self, rule_library: RuleLibrary) -> None:
        self.rule_library = rule_library
    
    def run(
        self,
        context: LintContext,
        profile: DocumentProfile,
        guidelines: Optional[ResolvedGuidelines],
        findings: list[Finding],
        policy_compliance: Optional[PolicyComplianceSummary] = None,
    ) -> CriticalReviewSummary:
        """
        Ejecuta la revisión crítica y retorna un resumen estructurado.
        """
        
        # 1. Agrupar findings por categoría
        issues_by_category = self._group_issues_by_category(findings)
        
        # 2. Construir top issues (máx 5)
        top_issues = self._extract_top_issues(issues_by_category, findings)
        
        # 3. Calcular main_status
        main_status = self._calculate_main_status(
            issues_by_category,
            policy_compliance,
        )
        
        # 4. Definir suggested_fix_order
        suggested_fix_order = self._compute_fix_order(
            issues_by_category,
            findings,
        )
        
        # 5. Generar notas (opcional)
        notes = self._generate_notes(
            profile,
            policy_compliance,
            main_status,
        )
        
        return CriticalReviewSummary(
            main_status=main_status,
            issues_by_category=issues_by_category,
            top_issues=top_issues,
            suggested_fix_order=suggested_fix_order,
            notes=notes,
        )
    
    def _group_issues_by_category(self, findings: list[Finding]) -> list[IssuesByCategory]:
        """
        Agrupa findings por categoría y cuenta errores, warnings, sugerencias.
        """
        category_map: dict[str, dict[str, int]] = {}
        
        for finding in findings:
            cat = finding.category
            if cat not in category_map:
                category_map[cat] = {
                    "error_count": 0,
                    "warning_count": 0,
                    "suggestion_count": 0,
                }
            
            sev_str = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity).lower()
            
            if "error" in sev_str:
                category_map[cat]["error_count"] += 1
            elif "warning" in sev_str or "warn" in sev_str:
                category_map[cat]["warning_count"] += 1
            else:
                category_map[cat]["suggestion_count"] += 1
        
        issues_list = []
        for category, counts in category_map.items():
            issues_list.append(
                IssuesByCategory(
                    category=category,
                    error_count=counts["error_count"],
                    warning_count=counts["warning_count"],
                    suggestion_count=counts["suggestion_count"],
                )
            )
        
        return issues_list
    
    def _extract_top_issues(
        self,
        issues_by_category: list[IssuesByCategory],
        findings: list[Finding],
    ) -> list[TopIssue]:
        """
        Extrae los 3-5 top issues más importantes.
        """
        top_issues = []
        
        # Ordenar categorías por cantidad de errores
        sorted_categories = sorted(
            issues_by_category,
            key=lambda x: (x.error_count, x.warning_count),
            reverse=True,
        )
        
        # Tomar máximo 5 categorías
        for ibc in sorted_categories[:5]:
            if ibc.error_count == 0 and ibc.warning_count == 0 and ibc.suggestion_count == 0:
                continue
            
            # Determinar severidad predominante
            if ibc.error_count > 0:
                severity = "error"
            elif ibc.warning_count > 0:
                severity = "warning"
            else:
                severity = "suggestion"
            
            # Obtener un mensaje genérico
            message = self._get_category_message(ibc.category)
            
            # Sugerencia genérica
            suggested_action = self._get_category_action(ibc.category)
            
            total_issues = ibc.error_count + ibc.warning_count + ibc.suggestion_count
            
            top_issues.append(
                TopIssue(
                    issue_type=ibc.category,
                    severity=severity,
                    message=message,
                    count=total_issues,
                    suggested_action=suggested_action,
                )
            )
        
        return top_issues
    
    def _calculate_main_status(
        self,
        issues_by_category: list[IssuesByCategory],
        policy_compliance: Optional[PolicyComplianceSummary],
    ) -> str:
        """
        Calcula el estado principal (OK, NEEDS_IMPROVEMENT, CRITICAL).
        """
        total_errors = sum(ibc.error_count for ibc in issues_by_category)
        
        if policy_compliance is not None:
            score = policy_compliance.score
            
            if score < 60 or total_errors > 20:
                return "CRITICAL"
            elif score < 85 or total_errors > 5:
                return "NEEDS_IMPROVEMENT"
            else:
                return "OK"
        else:
            # Fallback solo por errores
            if total_errors > 20:
                return "CRITICAL"
            elif total_errors > 5:
                return "NEEDS_IMPROVEMENT"
            else:
                return "OK"
    
    def _compute_fix_order(
        self,
        issues_by_category: list[IssuesByCategory],
        findings: list[Finding],
    ) -> list[str]:
        """
        Determina el orden recomendado para corregir issues.
        """
        # Obtener categorías que tienen findings
        categories_with_findings = {ibc.category for ibc in issues_by_category}
        
        # Aplicar prioridad
        fix_order = []
        for cat in self.CATEGORY_PRIORITY:
            if cat in categories_with_findings:
                fix_order.append(cat)
        
        # Añadir categorías no previstas
        for ibc in issues_by_category:
            if ibc.category not in fix_order:
                fix_order.append(ibc.category)
        
        return fix_order
    
    def _get_category_message(self, category: str) -> str:
        """
        Retorna un mensaje genérico para una categoría.
        """
        messages = {
            "structure": "Problemas en la estructura del documento",
            "citations": "Inconsistencias en las citas",
            "references": "Errores en la lista de referencias",
            "math_format": "Formateo incorrecto de ecuaciones",
            "math_equations": "Errores en ecuaciones matemáticas",
            "code_format": "Formateo incorrecto de código",
            "code_blocks": "Problemas en bloques de código",
            "academic_style": "Estilo académico incorrecto",
            "format": "Problemas de formato general",
            "layout": "Problemas de maquetación",
            "metadata": "Inconsistencias en metadatos",
        }
        return messages.get(category, f"Problemas en {category}")
    
    def _get_category_action(self, category: str) -> str:
        """
        Retorna una acción sugerida para una categoría.
        """
        actions = {
            "structure": "Revisa la estructura del documento y asegura que contenga todas las secciones requeridas en el orden correcto.",
            "citations": "Verifica que todas las citas en texto sigan el formato APA7 correcto.",
            "references": "Revisa la lista de referencias para asegurar que cumple con el formato APA7.",
            "math_format": "Corrige el formateo de todas las ecuaciones matemáticas según APA7.",
            "math_equations": "Verifica la correcta escritura y numeración de ecuaciones.",
            "code_format": "Asegura que el código sigue las convenciones de formato establecidas.",
            "code_blocks": "Verifica que los bloques de código estén correctamente formateados.",
            "academic_style": "Mejora el estilo académico del documento.",
            "format": "Corrige los problemas de formato general del documento.",
            "layout": "Ajusta la maquetación del documento según los estándares requeridos.",
            "metadata": "Actualiza los metadatos del documento para asegurar consistencia.",
        }
        return actions.get(category, f"Corrige los problemas en {category}.")
    
    def _generate_notes(
        self,
        profile: DocumentProfile,
        policy_compliance: Optional[PolicyComplianceSummary],
        main_status: str,
    ) -> Optional[str]:
        """
        Genera notas contextuales del documento.
        """
        notes = []
        
        if profile and profile.confidence > 0:
            notes.append(f"Confianza en perfil: {profile.confidence*100:.0f}%")
        
        if policy_compliance:
            notes.append(f"Cumplimiento de política: {policy_compliance.score}%")
        
        if main_status == "CRITICAL":
            notes.append("El documento requiere revisión crítica urgente.")
        
        return " | ".join(notes) if notes else None
