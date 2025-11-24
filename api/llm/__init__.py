"""
Módulo LLM de bajo nivel: abstracciones y clientes para integrar LLM.

Este módulo proporciona:
- BaseLLMClient: clase abstracta para clientes LLM
- OpenAILLMClient: implementación con OpenAI AsyncOpenAI
- Modelos de datos: ChatMessage, LLMResponse
"""

from api.llm.client import BaseLLMClient, ChatMessage, LLMResponse
from api.llm.providers import OpenAILLMClient

__all__ = ["BaseLLMClient", "ChatMessage", "LLMResponse", "OpenAILLMClient"]
