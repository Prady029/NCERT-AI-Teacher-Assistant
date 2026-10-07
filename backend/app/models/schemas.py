"""
Pydantic models for NCERT AI Teacher Assistant API.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Subject(str, Enum):
    """Supported subjects."""
    SCIENCE = "science"
    SOCIAL_SCIENCE = "social_science"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    MATHEMATICS = "mathematics"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICAL_SCIENCE = "political_science"
    ECONOMICS = "economics"
    ENGLISH = "english"
    HINDI = "hindi"


class ClassLevel(int, Enum):
    """Supported class levels."""
    CLASS_6 = 6
    CLASS_7 = 7
    CLASS_8 = 8
    CLASS_9 = 9
    CLASS_10 = 10
    CLASS_11 = 11
    CLASS_12 = 12


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class QuestionType(str, Enum):
    """Question types for exam papers."""
    MCQ = "mcq"
    VERY_SHORT_ANSWER = "very_short_answer"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    CASE_BASED = "case_based"
    ASSERTION_REASON = "assertion_reason"


class LessonPlanRequest(BaseModel):
    """Request model for lesson plan generation."""
    subject: Subject
    class_level: ClassLevel
    chapter: str
    duration_periods: int = Field(default=2, ge=1, le=10)
    learning_objectives: Optional[List[str]] = None
    student_profile: Optional[str] = "mixed_ability"
    pedagogical_model: Literal["5e", "direct_instruction", "inquiry"] = "5e"
    include_differentiation: bool = True
    include_assessment: bool = True
    language: Literal["english", "hindi"] = "english"


class QuestionPaperRequest(BaseModel):
    """Request model for question paper generation."""
    subject: Subject
    class_level: ClassLevel
    unit_or_chapters: List[str]
    total_marks: int = Field(default=30, ge=10, le=100)
    duration_minutes: int = Field(default=60, ge=30, le=180)
    difficulty_distribution: Dict[DifficultyLevel, float] = Field(
        default_factory=lambda: {
            DifficultyLevel.EASY: 0.3,
            DifficultyLevel.MEDIUM: 0.5,
            DifficultyLevel.HARD: 0.2
        }
    )
    question_type_distribution: Dict[QuestionType, int] = Field(
        default_factory=lambda: {
            QuestionType.MCQ: 5,
            QuestionType.VERY_SHORT_ANSWER: 5,
            QuestionType.SHORT_ANSWER: 4,
            QuestionType.LONG_ANSWER: 3,
            QuestionType.CASE_BASED: 1
        }
    )
    blueprint: Optional[Dict[str, Any]] = None
    language: Literal["english", "hindi"] = "english"


class LessonPlanResponse(BaseModel):
    """Response model for lesson plan."""
    lesson_plan_id: str
    subject: Subject
    class_level: ClassLevel
    chapter: str
    duration_periods: int
    learning_objectives: List[Dict[str, Any]]
    lesson_structure: Dict[str, Any]
    activities: List[Dict[str, Any]]
    differentiation_strategies: List[str]
    assessment_checkpoints: List[Dict[str, Any]]
    required_materials: List[str]
    digital_resources: List[str]
    homework_assignment: Optional[str] = None
    teacher_notes: Optional[str] = None
    generated_at: str
    curriculum_alignment: Dict[str, Any]


class QuestionPaperResponse(BaseModel):
    """Response model for question paper."""
    question_paper_id: str
    subject: Subject
    class_level: ClassLevel
    total_marks: int
    duration_minutes: int
    sections: List[Dict[str, Any]]
    marking_scheme: Dict[str, Any]
    blueprint: Dict[str, Any]
    difficulty_analysis: Dict[str, Any]
    generated_at: str


class ChapterSummaryRequest(BaseModel):
    """Request model for chapter summary."""
    subject: Subject
    class_level: ClassLevel
    chapter: str
    detail_level: Literal["brief", "standard", "detailed"] = "standard"
    include_key_concepts: bool = True
    include_formulas: bool = True
    include_diagrams: bool = False
    language: Literal["english", "hindi"] = "english"


class ChapterSummaryResponse(BaseModel):
    """Response model for chapter summary."""
    subject: Subject
    class_level: ClassLevel
    chapter: str
    summary: str
    key_concepts: List[str]
    formulas: List[Dict[str, str]]
    important_definitions: List[Dict[str, str]]
    common_misconceptions: List[str]
    real_world_applications: List[str]
    practice_questions: List[Dict[str, Any]]
    generated_at: str


class EvaluationRequest(BaseModel):
    """Request model for evaluating student responses."""
    question: str
    student_answer: str
    model_answer: str
    marks_allocated: int
    marking_criteria: Optional[List[str]] = None


class EvaluationResponse(BaseModel):
    """Response model for evaluation."""
    score: float
    max_score: int
    feedback: str
    criteria_met: List[str]
    criteria_missed: List[str]
    suggestions: List[str]


class CurriculumMappingResponse(BaseModel):
    """Response model for curriculum mapping."""
    subject: Subject
    class_level: ClassLevel
    chapters: List[Dict[str, Any]]
    learning_outcomes: Dict[str, List[str]]
    weightage: Dict[str, int]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None