from fastapi import APIRouter,Depends
import os
from typing import Optional

from api.config import get_settings
from api.services.coach_service import CoachService
from api.llm.client import BaseLLMClient
from api.models.coach import (
    CoachRequest,
    CoachResponse,
    CoachMode,
    CoachProfile,
    PaperProfile,
    FeedbackItem,
    CoachContext,
)

router = APIRouter(prefix="/coach", tags=["coach"])

def get_coach_service() -> CoachService:
    """Get coach service with optional LLM client."""
    settings = get_settings()
    llm_client: Optional[BaseLLMClient] = None
    
    if settings.LLM_ENABLED:
        try:
            from api.llm.providers import OpenAILLMClient
            llm_client = OpenAILLMClient()
        except Exception:
            pass
    
    return CoachService(llm_client=llm_client)


@router.post("", response_model=CoachResponse)
async def coach_endpoint(request: CoachReques, service: CoachService = Depends(get_coach_service))) -> CoachResponse:
    """
    Endpoint principal de coach academico.

    Soporta:
    - Perfiles:
        - apa7_global  -> APA 7 internacional
        - cun          -> APA 7 + adaptaciones CUN
    - Modos:
        - PLAN_SECTION
        - REVIEW_SECTION
        - CLARIFY_INSTRUCTIONS
    """

    if request.mode == CoachMode.PLAN_SECTION:
        return await _handle_plan_section(request)

    if request.mode == CoachMode.REVIEW_SECTION:
        if not request.student_text:
            raise HTTPException(
                status_code=400,
                detail="student_text es obligatorio para REVIEW_SECTION",
            )
        return await _handle_review_section(request)

    if request.mode == CoachMode.CLARIFY_INSTRUCTIONS:
        return await _handle_clarify_instructions(request)

    raise HTTPException(status_code=400, detail="Modo no soportado")


# --------- Construccion de prompts / personalidad del coach --------- #


def build_system_prompt(profile: CoachProfile, paper_profile: PaperProfile) -> str:
    """
    SYSTEM prompt base que define el rol del coach segun:
    - perfil de norma (APA7 global vs CUN)
    - tipo de documento (student paper vs professional paper)
    """
    base: str

    if profile == CoachProfile.APA7_GLOBAL:
        base = (
            "Eres un COACH ACADEMICO especializado en la 7a edicion del "
            "Publication Manual of the American Psychological Association (APA 7, 2019).\n"
        )
    else:
        base = (
            "Eres un COACH ACADEMICO especializado en la Corporacion Unificada Nacional "
            "de Educacion Superior (CUN) y en normas APA 7a edicion.\n"
            "Primero respetas el estandar APA 7 internacional y luego aplicas "
            "las adaptaciones CUN cuando existan.\n"
        )

    if paper_profile == PaperProfile.STUDENT_PAPER:
        base += (
            "Estas trabajando con un TRABAJO DE ESTUDIANTE (student paper). "
            "Debes:\n"
            "- Priorizar elementos propios de trabajos de curso (portada, curso, docente, fecha, etc.).\n"
            "- Ser pedagogico y explicar la norma APA 7 de forma clara.\n"
            "- Cuidar citas, referencias, estructura basica y tono academico.\n"
        )
    else:
        base += (
            "Estas trabajando con un MANUSCRITO PROFESIONAL (professional paper). "
            "Debes:\n"
            "- Priorizar estructuras tipo articulo de revista (introduccion, metodo, resultados, discusion).\n"
            "- Ser mas estricto con formato de secciones, tablas, figuras y referencias.\n"
        )

    base += (
        "Tu funcion NO es escribir el trabajo completo, sino ayudar a planear secciones, "
        "detectar problemas de forma (APA) y dar feedback para que el autor mejore su propio texto.\n"
        "Responde SIEMPRE en ESPANOL.\n"
        "Evita dar parrafos completos listos para entregar; centra tu respuesta en esquemas, "
        "consejos, fortalezas, mejoras y proximos pasos.\n"
    )

    return base


def _context_block(ctx: CoachContext) -> str:
    """Construye un bloque de contexto textual a partir del CoachContext."""
    return f"""
[CONTEXTO DEL DOCUMENTO]

- Perfil de documento (APA): {ctx.paper_profile.value}
- Autor: {ctx.author_role or "N/D"}
- Audiencia: {ctx.audience_role or "N/D"}
- Perfiles de validacion activos: {", ".join(ctx.validation_profiles) or "N/D"}
- Curso: {ctx.course or "N/D"}
- Programa: {ctx.program or "N/D"}
- Semestre: {ctx.semester or "N/D"}
- Institucion: {ctx.institution or "N/D"}
- Tema central: {ctx.topic or "N/D"}

INSTRUCCIONES DEL DOCENTE / ACA:
---
{ctx.aca_instructions or "Sin instrucciones especificas."}
---

GUIAS INSTITUCIONALES:
---
{ctx.local_guidelines or "No se proporcionaron guias institucionales adicionales."}
---
"""


# --------- Handlers por modo --------- #


async def _handle_plan_section(request: CoachRequest) -> CoachResponse:
    ctx = request.context
    system_prompt = build_system_prompt(request.profile, ctx.paper_profile)

    user_prompt = _context_block(ctx) + """
TAREA DEL COACH (PLAN_SECTION):

El estudiante quiere PLANEAR una seccion de su documento (por ejemplo, introduccion, marco teorico,
conclusiones, etc.). Tu trabajo es ayudarle a organizar sus ideas, NO escribir la seccion completa.

1. Propon un ESQUEMA (OUTLINE) de 3 a 5 puntos para la seccion.
   - Cada punto debe describir brevemente el contenido de un parrafo o bloque.
2. Da de 3 a 6 CONSEJOS (GUIDANCE) para que el escriba la seccion con sus propias palabras,
   cumpliendo la norma APA 7 y, si corresponde, las guias institucionales.
3. Sugiere de 2 a 4 PROXIMOS PASOS (NEXT_ACTIONS) concretos que pueda hacer despues de leer tu respuesta.

NO redactes la seccion completa lista para entregar.
"""

    outline = [
        "Parrafo 1: Presentar el contexto general del tema en el curso.",
        "Parrafo 2: Explicar el proposito especifico de la actividad o trabajo.",
        "Parrafo 3: Describir el enfoque o estrategia que se utilizara.",
        "Parrafo 4: Mencionar brevemente la estructura del documento.",
    ]
    guidance = [
        "Usa un tono academico claro, evitando expresiones coloquiales.",
        "Si mencionas autores o estudios, incluye citas en formato APA 7.",
        "Conecta el tema del trabajo con los objetivos del curso o del programa.",
    ]
    next_actions = [
        "Escribe un primer borrador siguiendo el esquema propuesto.",
        "Revisa si el borrador responde a lo que pide el ACA o la guia del docente.",
        "Si lo deseas, usa el modo REVIEW_SECTION del coach para recibir feedback sobre tu borrador.",
    ]

    return CoachResponse(
        success=True,
        profile=request.profile,
        mode=request.mode,
        outline=outline,
        guidance=guidance,
        next_actions=next_actions,
    )


async def _handle_review_section(request: CoachRequest) -> CoachResponse:
    ctx = request.context
    text = request.student_text or ""
    system_prompt = build_system_prompt(request.profile, ctx.paper_profile)

    user_prompt = _context_block(ctx) + f"""
TAREA DEL COACH (REVIEW_SECTION):

A continuacion tienes un texto escrito por el estudiante. Tu funcion es dar FEEDBACK, no reescribirlo.

TEXTO DEL ESTUDIANTE:
---
{text}
---

1. Identifica FORTALEZAS (STRENGTHS) del texto.
2. Identifica MEJORAS (IMPROVEMENTS) necesarias:
   - claridad,
   - tono academico,
   - uso de citas/referencias APA 7,
   - alineacion con el ACA / guias institucionales.
3. Da una lista de CONSEJOS GENERALES (GUIDANCE).
4. Propon PROXIMOS PASOS (NEXT_ACTIONS) concretos.

NO devuelvas un texto alternativo completo listo para entregar.
"""

    strengths = [
        "El texto se mantiene enfocado en el tema central.",
        "La redaccion es comprensible y sigue un hilo logico.",
    ]
    improvements = [
        "Podrias hacer mas explicita la conexion con los objetivos del trabajo.",
        "Seria util anadir al menos una cita en formato APA 7 si mencionas ideas de otros autores.",
    ]
    guidance = [
        "Revisa cada parrafo y verifica si responde a lo que pide el ACA.",
        "Comprueba que cualquier afirmacion basada en la literatura tenga su cita correspondiente.",
    ]
    next_actions = [
        "Reescribe un segundo borrador aplicando al menos dos mejoras.",
        "Revisa la guia APA 7 para asegurarte de que las citas y referencias son correctas.",
    ]

    feedback_items = (
        [FeedbackItem(type="strength", message=m) for m in strengths]
        + [FeedbackItem(type="improvement", message=m) for m in improvements]
    )

    return CoachResponse(
        success=True,
        profile=request.profile,
        mode=request.mode,
        feedback=feedback_items,
        guidance=guidance,
        next_actions=next_actions,
    )


async def _handle_clarify_instructions(request: CoachRequest) -> CoachResponse:
    ctx = request.context
    system_prompt = build_system_prompt(request.profile, ctx.paper_profile)

    user_prompt = _context_block(ctx) + f"""
TAREA DEL COACH (CLARIFY_INSTRUCTIONS):

El objetivo es que el estudiante entienda mejor que le pide el ACA / guia del docente.

1. Explica en lenguaje sencillo que productos o entregables requiere la actividad.
2. Senala los puntos CLAVE que no debe olvidar (formato, estructura, normas APA, plazos, etc.).
3. Si hay una pregunta concreta del estudiante, respondela claramente:

PREGUNTA DEL ESTUDIANTE (si existe):
---
{request.student_question or "Sin pregunta especifica."}
---

4. Propon 2 a 4 PROXIMOS PASOS (NEXT_ACTIONS) para avanzar con el trabajo.
"""

    clarifications = [
        "El ACA te pide que desarrolles un producto escrito donde apliques los conceptos del curso.",
        "Es importante que sigas la estructura propuesta (por ejemplo: introduccion, desarrollo, conclusiones, referencias).",
        "Si el documento menciona normas APA 7, deberas usarlas para citas y referencias.",
    ]
    guidance = [
        "Subraya en el ACA las palabras clave como 'producto final', 'formato', 'rubrica' o 'criterios de evaluacion'.",
        "Haz una lista de los entregables concretos que te piden (documento, graficas, codigo, etc.).",
    ]
    next_actions = [
        "Define que parte del trabajo vas a completar hoy (por ejemplo, solo la introduccion).",
        "Usa el modo PLAN_SECTION del coach para obtener un esquema de esa parte antes de escribir.",
    ]

    return CoachResponse(
        success=True,
        profile=request.profile,
        mode=request.mode,
        clarifications=clarifications,
        guidance=guidance,
        next_actions=next_actions,
    )
