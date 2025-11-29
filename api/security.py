"""Módulo de seguridad para autenticación por API key."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException, status


def get_allowed_api_keys() -> list[str]:
    """
    Lee las API keys permitidas desde la variable de entorno APA7_API_KEYS.
    
    Formato esperado: claves separadas por comas.
    Ejemplo: APA7_API_KEYS="key1,key2,key3"
    
    Returns:
        Lista de API keys permitidas. Lista vacía indica modo desarrollo sin auth.
    """
    # AQUI VAN LAS API KEYS PERMITIDAS VIA VARIABLE DE ENTORNO APA7_API_KEYS
    keys_str = os.getenv("APA7_API_KEYS", "")
    if not keys_str.strip():
        return []
    
    return [key.strip() for key in keys_str.split(",") if key.strip()]


def api_key_auth(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> None:
    """
    Dependencia FastAPI para validar API key en header X-API-Key.
    
    Comportamiento:
    - Si APA7_API_KEYS está vacío → MODO DESARROLLO: no exige API key
    - Si APA7_API_KEYS tiene valores → exige que X-API-Key esté presente y sea válida
    
    Args:
        x_api_key: Valor del header X-API-Key
        
    Raises:
        HTTPException 401: Si la API key es inválida o falta en modo producción
    """
    allowed_keys = get_allowed_api_keys()
    
    # Modo desarrollo: sin API keys configuradas, permitir acceso
    if not allowed_keys:
        return
    
    # Modo producción: validar API key
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if x_api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
