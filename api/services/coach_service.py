"""Coach service with LLM integration for APA7 compliance."""
import json
import logging
from typing import Optional

from api.llm.client import BaseLLMClient, ChatMessage, LLMResponse
from api.models.coach import CoachRequest, CoachResponse

logger = logging.getLogger(__name__)


class CoachService:
    """Service layer for coaching functionality with LLM integration."""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        """Initialize coach service.

        Args:
            llm_client: Optional LLM client for AI-powered coaching.
                       If None, fallback responses will be used.
        """
        self.llm_client = llm_client

    async def handle(self, request: CoachRequest) -> CoachResponse:
        """Handle coach request using LLM if available.

        Args:
            request: CoachRequest with mode and context

        Returns:
            CoachResponse with coaching guidance
        """
        try:
            if self.llm_client is None:
                logger.debug("LLM client not available, returning fallback response")
                return self._get_fallback_response(request)

            # Build prompt based on mode
            prompt_text = self._build_prompt(request)
            if not prompt_text:
                return self._get_fallback_response(request)

            # Call LLM
            messages = [
                ChatMessage(role="system", content="Eres un asistente experto en cumplimiento APA7."),
                ChatMessage(role="user", content=prompt_text),
            ]
            llm_response: LLMResponse = await self.llm_client.chat(messages)

            # Parse LLM response
            return self._parse_llm_response(llm_response, request)

        except Exception as e:
            logger.error(f"Error in coach service: {str(e)}")
            return self._get_fallback_response(request)

    def _build_prompt(self, request: CoachRequest) -> str:
        """Build prompt for LLM based on request mode.

        Args:
            request: CoachRequest with mode and context

        Returns:
            Prompt string for LLM
        """
        if request.mode == "PLAN_SECTION":
            return f"""Analiza el siguiente documento y genera un plan de cumplimiento APA7:

Documento:
{request.context.get('document_content', '')}

Sección: {request.context.get('section', '')}

Responde en JSON con: outline, guidance, next_actions"""
        return None

    def _parse_llm_response(self, llm_response: LLMResponse, request: CoachRequest) -> CoachResponse:
        """Parse LLM response into CoachResponse.

        Args:
            llm_response: Response from LLM
            request: Original request

        Returns:
            CoachResponse
        """
        try:
            content = llm_response.content or "{}"
            data = json.loads(content)
            return CoachResponse(
                mode=request.mode,
                outline=data.get("outline", []),
                guidance=data.get("guidance", ""),
                next_actions=data.get("next_actions", []),
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {str(e)}")
            return self._get_fallback_response(request)

    def _get_fallback_response(self, request: CoachRequest) -> CoachResponse:
        """Return fallback response when LLM is unavailable.

        Args:
            request: CoachRequest

        Returns:
            CoachResponse with generic guidance
        """
        return CoachResponse(
            mode=request.mode,
            outline=["Estructura básica"],
            guidance="Consulta las guías APA7 oficiales para formato detallado.",
            next_actions=["Revisar documento", "Aplicar formato"],
        )
