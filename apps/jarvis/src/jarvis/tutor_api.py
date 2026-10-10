"""Authenticated Tutor API. Attempt endpoints are the human evidence boundary."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from jarvis.policy import Actor
from jarvis.tutor import TutorConflict, TutorScope, TutorService
from jarvis.tutor_schema import (
    LearnerAttemptCreate,
    LearningObjectiveCreate,
    LessonCreate,
    QuizCreate,
    ReviewComplete,
)


def tutor_router(tutor: TutorService, actor: Actor, dependencies: list) -> APIRouter:
    router = APIRouter(prefix="/api/tutor", tags=["tutor"], dependencies=dependencies)

    def scope() -> TutorScope:
        return TutorScope(actor)

    @router.post("/objectives", status_code=201)
    async def create_objective(body: LearningObjectiveCreate):
        return await tutor.create_objective(scope(), body)

    @router.get("/objectives")
    async def list_objectives():
        return await tutor.list_objectives(scope())

    @router.get("/objectives/{objective_id}")
    async def inspect_objective(objective_id: str):
        return await tutor.inspect_objective(scope(), objective_id)

    @router.get("/objectives/{objective_id}/context")
    async def objective_context(objective_id: str):
        return await tutor.context(scope(), objective_id)

    @router.post("/objectives/{objective_id}/lessons", status_code=201)
    async def create_lesson(objective_id: str, body: LessonCreate):
        return await tutor.create_lesson(scope(), objective_id, body)

    @router.post("/objectives/{objective_id}/quizzes", status_code=201)
    async def create_quiz(objective_id: str, body: QuizCreate):
        return await tutor.create_quiz(scope(), objective_id, body)

    @router.get("/objectives/{objective_id}/attempts")
    async def attempts(objective_id: str):
        return await tutor.list_attempts(scope(), objective_id)

    @router.post("/quizzes/{quiz_id}/attempts", status_code=201)
    async def submit_attempt(quiz_id: str, body: LearnerAttemptCreate):
        # No equivalent model tool exists. The server stamps HUMAN_API and grades it.
        return await tutor.submit_attempt(scope(), quiz_id, body)

    @router.get("/reviews")
    async def reviews(due_before: Annotated[datetime, Query()]):
        if due_before.tzinfo is None or due_before.utcoffset() is None:
            raise TutorConflict("Review query time must include a timezone")
        return await tutor.due_reviews(scope(), due_before)

    @router.post("/reviews/{task_id}/complete")
    async def complete_review(task_id: str, body: ReviewComplete):
        return await tutor.complete_review(scope(), task_id, body.attempt_id)

    return router
