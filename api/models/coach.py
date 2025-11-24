from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class CoachProfile(str, Enum):
    """
    Perfil de norma que usará el coach:
    - apa7_global: APA 7ª edición internacional (2019/2020)
    - cun: APA 7 + adaptaciones institucionales CUN
    (a futuro puedes añadir más instituciones)
    """
    APA7_GLOBAL = "apa7_global"
    CUN = "cun"


class CoachMode(str, Enum):
    """
    Modo de operación del coach:
    - PLAN_SECTION: ayuda a planear una sección (esquema + consejos)
    - REVIEW_SECTION: da feedback sobre texto ya escrito
    - CLARIFY_INSTRUCTIONS: explica el ACA / guía del docente
    """
    PLAN_SECTION = "PLAN_SECTION"
    REVIEW_SECTION = "REVIEW_SECTION"
    CLARIFY_INSTRUCTIONS = "CLARIFY_INSTRUCTIONS"


class PaperProfile(str, Enum):
    """
    Perfil de documento según APA 7:
    - student_paper: trabajo de estudiante
    - professional_paper: manuscrito profesional (artículo, informe)
    """
    STUDENT_PAPER = "student_paper"
    PROFESSIONAL_PAPER = "professional_paper"


class AuthorRole(str, Enum):
    ESTUDIANTE_INDIVIDUAL = "estudiante_individual"
    ESTUDIANTES_EQUIPO = "estudiantes_equipo"
    DOCENTE = "docente"
    INSTITUCION = "institucion"
    OTRO = "otro"


class AudienceRole(str, Enum):
    DOCENTE = "docente"
    ESTUDIANTES = "estudiantes"
    COMUNIDAD_ACADEMICA = "comunidad_academica"
    PUBLICO_GENERAL = "publico_general"
    OTRO = "otro"


class CoachContext(BaseModel):
    """
    Contexto académico que acompaña la petición al coach.
    Parte de esto viene del modal del frontend (docType, audience, workScope, perfiles…)
    """
    # Perfil de documento según APA
    paper_profile: PaperProfile = PaperProfile.STUDENT_PAPER

    # Quién escribe y para quién (derivado de audience + group/individual)
    author_role: Optional[AuthorRole] = None
    audience_role: Optional[AudienceRole] = None

    # Perfiles de validación activos (ej: ["apa7_cun", "apa7_global_2020"])
    validation_profiles: List[str] = []

    # Metadatos opcionales del curso/actividad
    course: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[str] = None
    institution: Optional[str] = None
    topic: Optional[str] = None  # tema central del trabajo/ACA

    # Textos de referencia del docente/institución
    aca_instructions: Optional[str] = None       # texto del ACA / consigna
    local_guidelines: Optional[str] = None       # resumen de guía CUN / institucional
    # si quieres, podrías añadir institutional_guides: List[str]


class CoachRequest(BaseModel):
    """
    Request principal para el endpoint /coach
    """
    profile: CoachProfile
    mode: CoachMode
    context: CoachContext

    # Texto del estudiante a revisar (solo para REVIEW_SECTION)
    student_text: Optional[str] = None

    # Pregunta del estudiante sobre el ACA (para CLARIFY_INSTRUCTIONS)
    student_question: Optional[str] = None


class FeedbackItem(BaseModel):
    type: str      # "strength" | "improvement"
    message: str


class CoachResponse(BaseModel):
    """
    Respuesta genérica del coach, independiente del modo.
    Solo se rellenan los campos que apliquen según el modo.
    """
    success: bool = True
    profile: CoachProfile
    mode: CoachMode

    # PLAN_SECTION
    outline: List[str] = []          # esquema de la sección
    guidance: List[str] = []         # consejos generales

    # REVIEW_SECTION
    feedback: List[FeedbackItem] = []    # fortalezas + mejoras

    # CLARIFY_INSTRUCTIONS
    clarifications: List[str] = []   # explicación de ACA / guías

    # Común a todos los modos
    next_actions: List[str] = []     # pasos concretos a seguir
