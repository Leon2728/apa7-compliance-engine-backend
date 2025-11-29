"""Manejadores de excepciones centralizados para respuestas de error consistentes."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Maneja errores de validación (ValueError) devolviendo HTTP 400.
    
    Args:
        request: Request de FastAPI
        exc: Excepción ValueError capturada
        
    Returns:
        JSONResponse con código 400 y detalles del error
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "code": "VALIDATION_ERROR",
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Maneja excepciones no controladas devolviendo HTTP 500.
    
    Loguea la traza completa internamente pero no la expone al cliente.
    
    Args:
        request: Request de FastAPI
        exc: Excepción no controlada
        
    Returns:
        JSONResponse con código 500 y mensaje genérico
    """
    logger.exception("Unhandled exception occurred", exc_info=exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )
