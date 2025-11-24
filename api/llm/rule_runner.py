"""LLMRuleRunner - Ejecutor de reglas semánticas con LLM."""

import json
import logging
from typing import Optional, List

from api.rules_models import Rule

logger = logging.getLogger(__name__)


class LLMRuleRunner:
    """Ejecuta reglas LLM (checkType='llm_semantic')."""
    
    def __init__(self, llm_client):
        """Inicializa el runner con un cliente LLM."""
        self.llm_client = llm_client
    
    async def run_llm_rule(
        self,
        rule: Rule,
        document_text: str,
        **kwargs
    ) -> List:
        """Ejecuta una regla LLM sobre el texto del documento.
        
        Args:
            rule: Regla con configuración LLM
            document_text: Texto del documento a evaluar
            **kwargs: Contexto adicional (context, profile, etc.)
        
        Returns:
            Lista de Finding objects
        """
        
        # Si no hay configuración LLM o está deshabilitada
        if not rule.llm_config or not rule.llm_config.enabled:
            return []
        
        # Si no hay cliente LLM disponible
        if not self.llm_client:
            logger.debug(f"LLM no disponible para regla {rule.rule_id}")
            return []
        
        try:
            # Truncar el texto
            text_to_evaluate = document_text[:rule.llm_config.max_chars]
            
            # Construir system prompt
            system_prompt = self._build_system_prompt(rule)
            
            # Construir user prompt
            user_prompt = self._build_user_prompt(rule, text_to_evaluate)
            
            # Llamar a LLM
            response = await self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parsear respuesta JSON
            findings = self._parse_llm_response(response, rule)
            return findings
            
        except Exception as e:
            logger.error(f"Error ejecutando regla LLM {rule.rule_id}: {e}")
            return []
    
    def _build_system_prompt(self, rule: Rule) -> str:
        """Construye el system prompt para la evaluación."""
        forbidden = "\n".join(f"- {b}" for b in rule.llm_config.forbidden_behaviors)
        allowed = "\n".join(f"- {s}" for s in rule.llm_config.allowed_suggestion_types)
        
        return f"""Eres un evaluador experto de cumplimiento APA7.
Tu tarea: Evaluar si el siguiente contenido cumple con la regla {rule.rule_id}.

REGLA: {rule.title}
DESCRIPCIÓN: {rule.description}
SEVERIDAD: {rule.severity}

COMPORTAMIENTOS PROHIBIDOS:
{forbidden}

TIPOS DE SUGERENCIAS PERMITIDAS:
{allowed}

FORMATO DE RESPUESTA: {rule.llm_config.output_format}

Responde SIEMPRE en formato JSON válido con esta estructura:
{{
  "findings": [
    {{
      "complies": boolean,
      "message": "string",
      "details": "string",
      "snippet": "string",
      "suggestion": "string",
      "offset_start": number,
      "offset_end": number
    }}
  ]
}}
"""
    
    def _build_user_prompt(self, rule: Rule, text_to_evaluate: str) -> str:
        """Construye el user prompt."""
        return f"""Evalúa el siguiente contenido según la regla {rule.rule_id}:

{text_to_evaluate}
"""
    
    def _parse_llm_response(self, response, rule: Rule) -> List:
        """Parsea la respuesta JSON del LLM."""
        findings = []
        
        try:
            # Extraer el content del response
            content = response.content if hasattr(response, 'content') else str(response)
            result = json.loads(content)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Respuesta LLM no es JSON válido para regla {rule.rule_id}: {e}")
            return []
        
        # Convertir items a diccionarios Finding-compatibles
        for item in result.get("findings", []):
            finding_dict = {
                "rule_id": rule.rule_id,
                "severity": rule.severity,
                "message": item.get("message", ""),
                "details": item.get("details", ""),
                "snippet": item.get("snippet", ""),
                "suggestion": item.get("suggestion"),
                "location": {
                    "offset_start": item.get("offset_start", 0),
                    "offset_end": item.get("offset_end", 0)
                }
            }
            findings.append(finding_dict)
        
        return findings
