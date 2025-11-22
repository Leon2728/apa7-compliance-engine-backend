from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from api.models.lint_models import LintContext, DocumentProfile, Finding
from api.rules_library import RuleLibrary


class BaseAgent(ABC):
    """
    Contrato base para todos los agentes APA7 del motor.

    Cada agente:

      - Expone un `agent_id` (ej: "GENERALSTRUCTURE", "GLOBALFORMAT").
      - Recibe:
          * document_text: texto completo del documento.
          * context: LintContext (tipo de documento, estilo, institución, etc.).
          * profile: DocumentProfile (perfil inferido por DOCUMENTPROFILE).
      - Devuelve una lista de `Finding` con los hallazgos que detecta.

    Los agentes concretos solo tienen que implementar el método `run`
    y, si lo necesitan, consumir `RuleLibrary` para obtener sus reglas.
    """

    agent_id: str

    def __init__(self, rule_library: RuleLibrary) -> None:
        self.rule_library = rule_library

    @abstractmethod
    async def run(
        self,
        document_text: str,
        context: LintContext,
        profile: DocumentProfile,
    ) -> List[Finding]:
        """
        Ejecuta el agente sobre el documento y devuelve los hallazgos encontrados.

        Este método debe ser implementado por cada agente concreto.
        """
        ...
