import os
import logging
from typing import List
from openai import AsyncOpenAI
from api.llm.client import BaseLLMClient, ChatMessage, LLMResponse

logger = logging.getLogger(__name__)


class OpenAILLMClient(BaseLLMClient):
    """
    Cliente LLM usando OpenAI AsyncOpenAI SDK (>= 1.0.0).
    
    Lee credenciales desde variables de entorno:
    - OPENAI_API_KEY: API key (obligatoria si se usa)
    - OPENAI_MODEL: Modelo a usar (default: gpt-4-turbo)
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Inicializa el cliente OpenAI.
        
        Args:
            api_key: API key. Si es None, la lee de OPENAI_API_KEY
            model: Modelo. Si es None, la lee de OPENAI_MODEL o usa default
            
        Raises:
            RuntimeError: Si no hay API key disponible
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no definida. "
                "Define la variable de entorno o pasa api_key como argumento."
            )
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """
        Envía mensajes a OpenAI y devuelve la respuesta.
        
        Args:
            messages: Lista de ChatMessage
            temperature: Creatividad (default 0.2 para coach)
            max_tokens: Límite de tokens (default 1024)
            **kwargs: Parámetros adicionales para OpenAI
            
        Returns:
            LLMResponse con content y raw
            
        Raises:
            RuntimeError: Si la llamada a OpenAI falla
        """
        try:
            # Convertir ChatMessage a dict para OpenAI
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            
            # Extraer contenido de la primera choice
            content = response.choices[0].message.content
            
            # Devolver respuesta estandarizada
            return LLMResponse(
                content=content,
                raw=response.model_dump(),
            )
        except Exception as e:
            logger.error(f"Error en OpenAILLMClient.chat: {str(e)}")
            raise RuntimeError(f"Falló la llamada a OpenAI: {str(e)}") from e
