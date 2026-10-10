"""Strict Tutor inputs. Learner evidence fields are intentionally server-owned."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator

from jarvis.domain import StrictModel

ID_PATTERN = r"^[a-zA-Z0-9_-]{1,80}$"


class LearningSourceKind(StrEnum):
    DOCUMENT = "DOCUMENT"
    USER_NOTE = "USER_NOTE"
    GRAPHIFY = "GRAPHIFY"
    CONVERSATION = "CONVERSATION"


class LearningSourceInput(StrictModel):
    kind: LearningSourceKind
    locator: str = Field(min_length=1, max_length=300)
    quote: str = Field(min_length=1, max_length=2000)


class LearningObjectiveCreate(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=4000)
    mastery_required_quizzes: int = Field(default=2, ge=1, le=10)
    mastery_min_score: int = Field(default=80, ge=50, le=100)
    sources: list[LearningSourceInput] = Field(min_length=1, max_length=8)


class LessonKind(StrEnum):
    EXPLANATION = "EXPLANATION"
    WORKED_EXAMPLE = "WORKED_EXAMPLE"
    SOCRATIC = "SOCRATIC"


class LessonCreate(StrictModel):
    kind: LessonKind
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=8000)
    source_ids: list[str] = Field(min_length=1, max_length=8)

    @field_validator("source_ids")
    @classmethod
    def distinct_sources(cls, value):
        if len(value) != len(set(value)) or any(len(item) > 36 for item in value):
            raise ValueError("Lesson source IDs must be distinct bounded identifiers")
        return value


class QuizCreate(StrictModel):
    prompt: str = Field(min_length=1, max_length=4000)
    accepted_answers: list[str] = Field(min_length=1, max_length=8)
    source_ids: list[str] = Field(min_length=1, max_length=8)

    @field_validator("accepted_answers")
    @classmethod
    def bounded_answers(cls, value):
        if any(not answer.strip() or len(answer) > 1000 for answer in value):
            raise ValueError("Quiz answers must be non-empty and at most 1000 characters")
        return value

    @field_validator("source_ids")
    @classmethod
    def distinct_sources(cls, value):
        return LessonCreate.distinct_sources(value)


class LearnerAttemptCreate(StrictModel):
    submission_id: str = Field(pattern=ID_PATTERN)
    answer: str = Field(min_length=1, max_length=4000)


class ReviewComplete(StrictModel):
    attempt_id: str = Field(min_length=1, max_length=36)


class TutorContextInput(StrictModel):
    objective_id: str = Field(min_length=1, max_length=36)


class TutorLessonInput(LessonCreate):
    objective_id: str = Field(min_length=1, max_length=36)


class TutorQuizInput(QuizCreate):
    objective_id: str = Field(min_length=1, max_length=36)


class ReviewQuery(StrictModel):
    due_before: datetime

    @field_validator("due_before")
    @classmethod
    def aware_datetime(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Review query time must include a timezone")
        return value
