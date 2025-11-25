from typing import Optional
import json
import logging
from pathlib import Path

from api.models.coach import (
    CoachRequest,
    CoachResponse,
    CoachMode,
)
from api.models.profile_models import DocumentProfileAnalysis

logger = logging.getLogger(__name__)


class CoachService:
    """
    Servicio que proporciona lógica de coach académico.
    
    Este servicio orquesta las operaciones de coach, delegando en
    métodos especializados por modo (PLAN_SECTION, REVIEW_SECTION,
    CLARIFY_INSTRUCTIONS, DETECT_PROFILE).
    
    Para DETECT_PROFILE utiliza un cliente LLM externo.
    """
    
    def __init__(self, llm_client: Optional['BaseLLMClient'] = None):
        """
        Inicializa el CoachService.
        
        Args:
            llm_client: Cliente LLM opcional para invocar modelos de lenguaje.
        """
        self.llm_client = llm_client
        self._load_prompts()
    
    def _load_prompts(self):
        """
        Carga los prompts del sistema desde los archivos de plantilla.
        """
        self.detect_profile_prompt_path = (
            Path(__file__).parent.parent / "llm" / "prompts" / "profile" / "detect_profile_es.md"
        )
    
    async def handle(self, request: CoachRequest) -> CoachResponse:
        """
        Maneja un request del coach según su modo.
        
        Args:
            request: CoachRequest con el modo y datos necesarios.
        
        Returns:
            CoachResponse con los resultados según el modo solicitado.
        
        Raises:
            HTTPException: Si el modo no es soportado o falta información requerida.
        """
        if request.mode == CoachMode.DETECT_PROFILE:
            if not request.document_text:
                raise ValueError(
                    "document_text es obligatorio para DETECT_PROFILE"
                )
            return await self._handle_detect_profile(request)
        
        # Para otros modos, levantamos excepción
        raise ValueError(f"Modo no soportado por CoachService: {request.mode}")
    
    async def _handle_detect_profile(self, request: CoachRequest) -> CoachResponse:
        """
        Implementa la lógica de DETECT_PROFILE usando LLM.
        
        Lee la plantilla de prompt desde detect_profile_es.md,
        invoca el cliente LLM con el texto del documento,
        parsea la respuesta JSON y retorna un CoachResponse con
        profile_analysis poblada.
        
        Args:
            request: CoachRequest con document_text poblado.
        
        Returns:
            CoachResponse con profile_analysis como DocumentProfileAnalysis.
        """
        if not self.llm_client:
            logger.warning(
                "LLM client no disponible para DETECT_PROFILE. "
                "Retornando respuesta de fallback."
            )
            return CoachResponse(
                success=False,
                profile=request.profile,
                mode=request.mode,
                error="LLM client no configurado",
            )
        
        try:
            # 1. Leer la plantilla de prompt
            prompt_template = await self._load_prompt_template()
            
            # 2. Construir el prompt final reemplazando {{DOCUMENT_TEXT}}
            user_prompt = prompt_template.replace(
                "{{DOCUMENT_TEXT}}",
                request.document_text,
            )
            
            # 3. Invocar el LLM
            llm_response = await self.llm_client.generate(
                system_prompt="Eres un experto en clasificación de documentos académicos en formato APA7.",
                user_prompt=user_prompt,
                temperature=0.1,  # Bajo para más consistencia
                max_tokens=1000,
            )
            
            # 4. Parsear la respuesta JSON
            profile_data = json.loads(llm_response)
            
            # 5. Crear DocumentProfileAnalysis
            profile_analysis = DocumentProfileAnalysis(
                isAcademic=profile_data.get("isAcademic", False),
                apaKind=profile_data.get("apaKind", "unknown"),
                documentType=profile_data.get("documentType"),
                level=profile_data.get("level"),
                mode=profile_data.get("mode"),
                confidence=profile_data.get("confidence", 0.0),
                suggestedProfileId=profile_data.get("suggestedProfileId"),
                reasons=profile_data.get("reasons", []),
            )
            
            # 6. Retornar CoachResponse con profile_analysis
            return CoachResponse(
                success=True,
                profile=request.profile,
                mode=request.mode,
                profile_analysis=profile_analysis,
            )
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando respuesta JSON del LLM: {e}")
            return CoachResponse(
                success=False,
                profile=request.profile,
                mode=request.mode,
                error=f"Respuesta LLM inválida: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error en _handle_detect_profile: {e}", exc_info=True)
            return CoachResponse(
                success=False,
                profile=request.profile,
                mode=request.mode,
                error=str(e),
            )
    
    async def _load_prompt_template(self) -> str:
        """
        Carga el contenido de la plantilla de prompt desde el archivo.
        
        Returns:
            String con el contenido completo del prompt template.
        
        Raises:
            FileNotFoundError: Si el archivo de prompt no existe.
        """
        try:
            with open(self.detect_profile_prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(
                f"Prompt template no encontrado en {self.detect_profile_prompt_path}"
            )
            raise
