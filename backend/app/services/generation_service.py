"""Curriculum-aware content generation and validation."""

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from pydantic import ValidationError

from app.models.schemas import (
    ChapterSummaryRequest,
    ChapterSummaryResponse,
    EvaluationRequest,
    EvaluationResponse,
    LessonPlanRequest,
    LessonPlanResponse,
    QuestionPaperRequest,
    QuestionPaperResponse,
)
from app.services.llm_service import llm_service
from app.services.prompt_templates import get_prompt
from app.services.rag_service import rag_service


class GenerationError(RuntimeError):
    """Raised when generation fails or cannot be validated."""


def _json_schema(model: Any) -> Dict[str, Any]:
    return model.model_json_schema()


async def _generate(prompt_name: str, request: Any, response_model: Any, **extra: Any) -> Dict[str, Any]:
    values = request.model_dump(mode="json")
    values.update(extra)
    periods = values.get("duration_periods", 1)
    values["duration"] = periods
    values["total_minutes"] = periods * 40
    # Allocate a 40-minute period across the 5E stages. The prompt template
    # expects stage timings in minutes, independent of period count.
    stage_minutes = values["total_minutes"]
    values.update({
        "engage_time": round(stage_minutes * 0.10),
        "explore_time": round(stage_minutes * 0.25),
        "explain_time": round(stage_minutes * 0.25),
        "elaborate_time": round(stage_minutes * 0.25),
        "evaluate_time": stage_minutes - round(stage_minutes * 0.85),
    })

    # RAG is optional at development time. State explicitly when no indexed
    # textbook sources are available so generation is never represented as
    # textbook-grounded without evidence.
    try:
        context = await rag_service.retrieve_for_prompt(
            prompt_name,
            subject=values.get("subject"),
            class_level=values.get("class_level"),
            chapter=values.get("chapter"),
        )
    except Exception:
        context = "No NCERT source passages are indexed. Do not claim textbook verification or invent page citations."
    prompt = get_prompt(prompt_name, **values)
    user_prompt = (
        f"Curriculum source material (use this as grounding; do not invent NCERT quotations):\n"
        f"{context}\n\n{prompt['user']}"
    )
    combined = f"{prompt['system']}\n\n{user_prompt}"
    try:
        result = await llm_service.generate_structured(
            combined,
            _json_schema(response_model),
            temperature=0.3,
        )
        return response_model.model_validate(result).model_dump(mode="json")
    except (ValidationError, ValueError, RuntimeError) as exc:
        raise GenerationError(f"Generated content could not be validated: {exc}") from exc


async def create_lesson_plan(request: LessonPlanRequest) -> Dict[str, Any]:
    prompt_name = "lesson_plan_5e" if request.pedagogical_model == "5e" else "lesson_plan_5e"
    result = await _generate(prompt_name, request, LessonPlanResponse)
    result.update({
        "lesson_plan_id": str(uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": request.subject.value,
        "class_level": request.class_level.value,
        "chapter": request.chapter,
        "duration_periods": request.duration_periods,
    })
    return LessonPlanResponse.model_validate(result).model_dump(mode="json")


async def create_question_paper(request: QuestionPaperRequest) -> Dict[str, Any]:
    difficulty = request.difficulty_distribution
    total = sum(float(v) for v in difficulty.values()) or 1.0
    result = await _generate(
        "question_paper",
        request,
        QuestionPaperResponse,
        chapters=", ".join(request.unit_or_chapters),
        easy_pct=round(100 * difficulty.get("easy", 0) / total),
        medium_pct=round(100 * difficulty.get("medium", 0) / total),
        hard_pct=round(100 * difficulty.get("hard", 0) / total),
        type_distribution="\n".join(
            f"- {kind}: {count}" for kind, count in request.question_type_distribution.items()
        ),
    )
    result.update({
        "question_paper_id": str(uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": request.subject.value,
        "class_level": request.class_level.value,
        "total_marks": request.total_marks,
        "duration_minutes": request.duration_minutes,
    })
    return QuestionPaperResponse.model_validate(result).model_dump(mode="json")


async def create_chapter_summary(request: ChapterSummaryRequest) -> Dict[str, Any]:
    result = await _generate("chapter_summary", request, ChapterSummaryResponse)
    result.update({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "subject": request.subject.value,
        "class_level": request.class_level.value,
        "chapter": request.chapter,
    })
    return ChapterSummaryResponse.model_validate(result).model_dump(mode="json")


async def evaluate_response(request: EvaluationRequest) -> Dict[str, Any]:
    prompt = get_prompt(
        "evaluation",
        question=request.question,
        marks=request.marks_allocated,
        model_answer=request.model_answer,
        student_answer=request.student_answer,
        criteria="; ".join(request.marking_criteria or []),
    )
    result = await llm_service.generate_structured(
        f"{prompt['system']}\n\n{prompt['user']}",
        _json_schema(EvaluationResponse),
        temperature=0.1,
    )
    validated = EvaluationResponse.model_validate(result)
    if validated.max_score != request.marks_allocated:
        raise GenerationError("Evaluator returned a max_score different from marks_allocated")
    if not 0 <= validated.score <= request.marks_allocated:
        raise GenerationError("Evaluator returned a score outside the allowed range")
    return validated.model_dump(mode="json")
