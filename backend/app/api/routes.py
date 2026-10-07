"""HTTP endpoints for curriculum resources and AI generation."""

import secrets

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.models.schemas import (
    ChapterSummaryRequest,
    ChapterSummaryResponse,
    EvaluationRequest,
    EvaluationResponse,
    HealthResponse,
    LessonPlanRequest,
    LessonPlanResponse,
    QuestionPaperRequest,
    QuestionPaperResponse,
)
from app.services.generation_service import (
    GenerationError,
    create_chapter_summary,
    create_lesson_plan,
    create_question_paper,
    evaluate_response,
)
from app.services.llm_service import llm_service
from app.services.rag_service import ncert_loader, rag_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report API and optional dependency configuration status."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        services={
            "llm": "configured" if llm_service.list_available_providers() else "not_configured",
            "rag": "configured" if settings.google_api_key else "not_configured",
        },
    )


@router.post("/lesson-plans", response_model=LessonPlanResponse)
async def generate_lesson_plan(request: LessonPlanRequest) -> LessonPlanResponse:
    """Generate a draft lesson plan. Teacher review is required before use."""
    try:
        return LessonPlanResponse.model_validate(await create_lesson_plan(request))
    except (GenerationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/question-papers", response_model=QuestionPaperResponse)
async def generate_question_paper(request: QuestionPaperRequest) -> QuestionPaperResponse:
    """Generate a draft question paper and marking scheme."""
    try:
        return QuestionPaperResponse.model_validate(await create_question_paper(request))
    except (GenerationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/chapter-summaries", response_model=ChapterSummaryResponse)
async def generate_chapter_summary(request: ChapterSummaryRequest) -> ChapterSummaryResponse:
    """Generate a chapter summary grounded in indexed textbook passages."""
    try:
        return ChapterSummaryResponse.model_validate(await create_chapter_summary(request))
    except (GenerationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_student_response(request: EvaluationRequest) -> EvaluationResponse:
    """Produce a formative, draft assessment of a response."""
    try:
        return EvaluationResponse.model_validate(await evaluate_response(request))
    except (GenerationError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/curriculum/{subject}/{class_level}")
async def get_curriculum(subject: str, class_level: int):
    """Return locally maintained curriculum metadata, if available."""
    from app.models.schemas import ClassLevel, Subject

    try:
        subject_enum = Subject(subject)
        class_enum = ClassLevel(class_level)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Unsupported subject or class") from exc
    return ncert_loader.load_curriculum_map(subject_enum, class_enum)


@router.post("/admin/index-textbooks")
async def index_textbooks(
    subject: str,
    class_level: int,
    x_indexing_api_key: str = Header(default=""),
):
    """Index local textbook text; requires a separately configured secret."""
    if not settings.indexing_api_key:
        raise HTTPException(status_code=503, detail="Textbook indexing is not configured")
    if not secrets.compare_digest(x_indexing_api_key, settings.indexing_api_key):
        raise HTTPException(status_code=403, detail="Invalid indexing key")
    from app.models.schemas import ClassLevel, Subject

    try:
        subject_enum = Subject(subject)
        class_enum = ClassLevel(class_level)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported subject or class") from exc
    try:
        docs = ncert_loader.prepare_rag_documents(subject_enum, class_enum)
        if not docs:
            raise HTTPException(status_code=404, detail="No local chapter text found")
        count = await rag_service.add_documents(docs)
        return {"indexed_chunks": count}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
