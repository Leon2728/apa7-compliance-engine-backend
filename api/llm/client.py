from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Modelo de mensaje para conversaciones con LLM.
    
    Attributes:
        role: "system", "user" o "assistant"
        content: Contenido del mensaje
    """
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    """
    Respuesta estandarizada del cliente LLM.
    
    Attributes:
        content: Texto de la primera choice
        raw: Respuesta completa del proveedor (dict opcional)
    """
    content: str = Field(..., description="Response text from first choice")
    raw: Optional[Dict[str, Any]] = Field(None, description="Complete provider response")


class BaseLLMClient(ABC):
    """
    Clase abstracta para clientes LLM.
    Todos los proveedores deben implementar este contrato.
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> LLMResponse:
        """
        Envía una conversación al LLM y obtiene una respuesta.
        
        Args:
            messages: Lista de ChatMessage con el historial de conversación
            temperature: Creatividad de la respuesta (0.0-2.0)
            max_tokens: Número máximo de tokens en la respuesta
            **kwargs: Parámetros adicionales específicos del proveedor
            
        Returns:
            LLMResponse con content y raw
            
        Raises:
            RuntimeError: Si falta API key o la llamada falla
        """
        pass
