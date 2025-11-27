from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from api.rules_models import RuleFile, Rule


class RuleLibrary:
    """
    Carga en memoria los archivos de reglas (*.rules.json) y expone
    métodos de consulta para los agentes APA7.

    Estructura esperada en disco:

        api/
          rules/
            apa7_cun/
              references.rules.json
              general-structure.rules.json
              global-format.rules.json
              in-text-citations.rules.json
              tables-figures.rules.json
              metadata-consistency.rules.json
              scientific-design.rules.json
              document-profile.rules.json

    Cada archivo debe cumplir el esquema de RuleFile:

        {
          "profileId": "apa7_cun",
          "agentId": "REFERENCES",
          "rules": [ ... Rule ... ]
        }
    """

    def __init__(self, base_dir: Path, profile_id: str = "apa7_cun") -> None:
        """
        :param base_dir: Directorio base donde vive la carpeta `rules/`.
                         Por ejemplo: Path(__file__).parent / "rules"
        :param profile_id: Perfil de reglas a cargar (ej: "apa7_cun").
        """
        self.base_dir = base_dir
        self.profile_id = profile_id

        # Índices internos
        self._by_agent: Dict[str, RuleFile] = {}
        self._by_rule_id: Dict[str, Rule] = {}

        self._load_all()

    # ------------------------------------------------------------------
    # CARGA INTERNA
    # ------------------------------------------------------------------
    def _load_all(self) -> None:
        """
        Carga todos los archivos *.rules.json del perfil indicado.

        No lanza excepción si el directorio no existe; simplemente
        deja la librería vacía (útil en entornos de desarrollo).
        """
        profile_dir = self.base_dir / self.profile_id
        if not profile_dir.exists():
            # Podrías añadir logging aquí si lo deseas.
            return

        for path in profile_dir.glob("*.rules.json"):
            content = path.read_text(encoding="utf-8")
            rule_file = RuleFile.model_validate_json(content)

            # Indexamos por agentId
            self._by_agent[rule_file.agent_id] = rule_file

            # Indexamos cada regla por ruleId global
            for rule in rule_file.rules:
                if rule.rule_id in self._by_rule_id:
                    # TODO: loggear warning de duplicado.
                    # Por ahora, conserva la primera aparición.
                    continue
                self._by_rule_id[rule.rule_id] = rule

    # ------------------------------------------------------------------
    # API PÚBLICA PARA AGENTES / ORQUESTADOR
    # ------------------------------------------------------------------
    def get_rules_for_agent(self, agent_id: str) -> List[Rule],
        profile_variant: Optional[str] = None,
    ) -> List[Rule]:
        """
        Devuelve la lista de reglas asociadas a un agente dado.

        :param agent_id: Identificador del agente (ej: "GENERALSTRUCTURE").
        :return: Lista de Rule; lista vacía si el agente no tiene reglas.
        """
if not rule_file:
            return []

        rules = rule_file.rules

        # Modo legacy: devolver todas las reglas si no se especifica profile_variant
        if profile_variant is None:
            return rules

        # Normalizar la variante
        variant = profile_variant.lower()

        # Mapeo de profile_variant a RuleSource permitidos
        if variant == "apa7_global":
            allowed_sources = {RuleSource.APA7, RuleSource.MIXED}
        elif variant == "apa7_institutional":
            allowed_sources = {RuleSource.LOCAL, RuleSource.MIXED}
        elif variant == "apa7_both":
            allowed_sources = {RuleSource.APA7, RuleSource.LOCAL, RuleSource.MIXED}
        else:
            # Comportamiento seguro: modo legacy si viene valor inesperado
            return rules

        # Filtrar reglas por RuleSource
        return [rule for rule in rules if rule.source in allowed_sources]

    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """
        Devuelve una regla concreta por su ID global (ruleId).

        :param rule_id: Identificador único de regla (ej: "CUN-REF-001").
        :return: Rule o None si no existe.
        """
        return self._by_rule_id.get(rule_id)

    def get_all_agent_ids(self) -> List[str]:
        """
        Lista los agentId para los que hay reglas cargadas.

        Útil para endpoints de diagnóstico (/health) o tooling.
        """
        return sorted(self._by_agent.keys())

    def reload(self) -> None:
        """
        Recarga todas las reglas desde disco.

        Útil en desarrollo cuando se editan los *.rules.json sin
        reiniciar el servidor.
        """
        self._by_agent.clear()
        self._by_rule_id.clear()
        self._load_all()
