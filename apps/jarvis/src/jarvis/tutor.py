"""Canonical Tutor state and deterministic learner-evidence evaluation."""

import hashlib
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from jarvis.db import (
    Database,
    LearningObjective,
    LearningSource,
    MasteryEvidence,
    ReviewTask,
    TutorAttempt,
    TutorLesson,
    TutorQuiz,
    audit,
    now,
)
from jarvis.policy import Actor
from jarvis.tutor_schema import (
    LearnerAttemptCreate,
    LearningObjectiveCreate,
    LessonCreate,
    QuizCreate,
)

REVIEW_INTERVALS = (1, 3, 7, 14, 30)


class TutorDenied(ValueError):
    pass


class TutorConflict(ValueError):
    pass


@dataclass(frozen=True)
class TutorScope:
    actor: Actor

    def require(self, capability: str) -> None:
        if capability not in self.actor.capabilities:
            raise TutorDenied(f"Missing capability: {capability}")


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def normalize_answer(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def answer_hash(value: str) -> str:
    return hashlib.sha256(normalize_answer(value).encode()).hexdigest()


class TutorService:
    def __init__(self, database: Database, clock=now):
        self.db = database
        self.clock = clock

    async def _objective(self, session, scope: TutorScope, objective_id: str, *, lock=False):
        statement = select(LearningObjective).where(
            LearningObjective.id == objective_id,
            LearningObjective.owner_id == scope.actor.id,
        )
        if lock:
            statement = statement.with_for_update()
        objective = await session.scalar(statement)
        if objective is None:
            raise KeyError("Learning objective not found")
        return objective

    async def _source_views(self, session, scope: TutorScope, objective_id: str) -> list[dict]:
        rows = list(
            await session.scalars(
                select(LearningSource)
                .where(
                    LearningSource.objective_id == objective_id,
                    LearningSource.owner_id == scope.actor.id,
                )
                .order_by(LearningSource.created_at, LearningSource.id)
            )
        )
        return [
            {
                "id": row.id,
                "kind": row.kind,
                "locator": row.locator,
                "quote": row.quote,
                "content_hash": row.content_hash,
                "trust": "UNTRUSTED_SOURCE_DATA",
            }
            for row in rows
        ]

    async def _objective_view(self, session, scope: TutorScope, objective) -> dict:
        evidence = (
            await session.get(MasteryEvidence, objective.mastery_evidence_id)
            if objective.mastery_evidence_id
            else None
        )
        return {
            "id": objective.id,
            "title": objective.title,
            "description": objective.description,
            "status": objective.status,
            "mastery_required_quizzes": objective.mastery_required_quizzes,
            "mastery_min_score": objective.mastery_min_score,
            "sources": await self._source_views(session, scope, objective.id),
            "mastery_evidence": (
                {
                    "id": evidence.id,
                    "attempt_ids": evidence.attempt_ids,
                    "distinct_quizzes": evidence.distinct_quizzes,
                    "score": evidence.score,
                    "evaluator": evidence.evaluator,
                    "created_at": evidence.created_at.isoformat(),
                }
                if evidence
                else None
            ),
            "mastered_at": objective.mastered_at.isoformat() if objective.mastered_at else None,
            "created_at": objective.created_at.isoformat(),
            "updated_at": objective.updated_at.isoformat(),
        }

    async def create_objective(self, scope: TutorScope, body: LearningObjectiveCreate) -> dict:
        scope.require("tutor.write")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            objective = LearningObjective(
                owner_id=scope.actor.id,
                title=body.title,
                description=body.description,
                mastery_required_quizzes=body.mastery_required_quizzes,
                mastery_min_score=body.mastery_min_score,
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(objective)
            await session.flush()
            for source in body.sources:
                session.add(
                    LearningSource(
                        objective_id=objective.id,
                        owner_id=scope.actor.id,
                        kind=source.kind.value,
                        locator=source.locator,
                        quote=source.quote,
                        content_hash=hashlib.sha256(source.quote.encode()).hexdigest(),
                        created_at=timestamp,
                    )
                )
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "tutor.objective_created",
                {"objective_id": objective.id, "source_count": len(body.sources)},
            )
            return await self._objective_view(session, scope, objective)

    async def list_objectives(self, scope: TutorScope) -> list[dict]:
        scope.require("tutor.read")
        async with self.db.sessions() as session:
            rows = list(
                await session.scalars(
                    select(LearningObjective)
                    .where(LearningObjective.owner_id == scope.actor.id)
                    .order_by(LearningObjective.updated_at.desc())
                    .limit(100)
                )
            )
            return [await self._objective_view(session, scope, row) for row in rows]

    async def inspect_objective(self, scope: TutorScope, objective_id: str) -> dict:
        scope.require("tutor.read")
        async with self.db.sessions() as session:
            return await self._objective_view(
                session, scope, await self._objective(session, scope, objective_id)
            )

    async def _validate_sources(
        self, session, scope: TutorScope, objective_id: str, source_ids: list[str]
    ) -> None:
        found = set(
            await session.scalars(
                select(LearningSource.id).where(
                    LearningSource.objective_id == objective_id,
                    LearningSource.owner_id == scope.actor.id,
                    LearningSource.id.in_(source_ids),
                )
            )
        )
        if found != set(source_ids):
            raise TutorConflict("Every cited source must belong to the learning objective")

    async def create_lesson(
        self,
        scope: TutorScope,
        objective_id: str,
        body: LessonCreate,
        *,
        origin: str = "HUMAN_API",
        run_id: str | None = None,
    ) -> dict:
        scope.require("tutor.write")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            objective = await self._objective(session, scope, objective_id)
            if objective.status == "ARCHIVED":
                raise TutorConflict("Archived learning objectives are read-only")
            await self._validate_sources(session, scope, objective_id, body.source_ids)
            lesson = TutorLesson(
                objective_id=objective_id,
                owner_id=scope.actor.id,
                kind=body.kind.value,
                title=body.title,
                content=body.content,
                source_ids=body.source_ids,
                origin=origin,
                created_at=timestamp,
            )
            session.add(lesson)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "tutor.lesson_created",
                {"objective_id": objective_id, "lesson_id": lesson.id, "origin": origin},
                run_id,
            )
            return self._lesson_view(lesson)

    @staticmethod
    def _lesson_view(lesson: TutorLesson) -> dict:
        return {
            "id": lesson.id,
            "objective_id": lesson.objective_id,
            "kind": lesson.kind,
            "title": lesson.title,
            "content": lesson.content,
            "source_ids": lesson.source_ids,
            "origin": lesson.origin,
            "created_at": lesson.created_at.isoformat(),
        }

    async def create_quiz(
        self,
        scope: TutorScope,
        objective_id: str,
        body: QuizCreate,
        *,
        origin: str = "HUMAN_API",
        run_id: str | None = None,
    ) -> dict:
        scope.require("tutor.write")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            objective = await self._objective(session, scope, objective_id)
            if objective.status == "ARCHIVED":
                raise TutorConflict("Archived learning objectives are read-only")
            await self._validate_sources(session, scope, objective_id, body.source_ids)
            hashes = sorted({answer_hash(answer) for answer in body.accepted_answers})
            quiz = TutorQuiz(
                objective_id=objective_id,
                owner_id=scope.actor.id,
                prompt=body.prompt,
                answer_hashes=hashes,
                source_ids=body.source_ids,
                origin=origin,
                created_at=timestamp,
            )
            session.add(quiz)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "tutor.quiz_created",
                {"objective_id": objective_id, "quiz_id": quiz.id, "origin": origin},
                run_id,
            )
            return self._quiz_view(quiz)

    @staticmethod
    def _quiz_view(quiz: TutorQuiz) -> dict:
        return {
            "id": quiz.id,
            "objective_id": quiz.objective_id,
            "prompt": quiz.prompt,
            "source_ids": quiz.source_ids,
            "origin": quiz.origin,
            "evaluation": "DETERMINISTIC_EXACT_NORMALIZED_V1",
            "created_at": quiz.created_at.isoformat(),
        }

    async def context(self, scope: TutorScope, objective_id: str) -> dict:
        scope.require("tutor.read")
        async with self.db.sessions() as session:
            objective = await self._objective(session, scope, objective_id)
            lessons = list(
                await session.scalars(
                    select(TutorLesson)
                    .where(
                        TutorLesson.objective_id == objective_id,
                        TutorLesson.owner_id == scope.actor.id,
                    )
                    .order_by(TutorLesson.created_at, TutorLesson.id)
                    .limit(50)
                )
            )
            quizzes = list(
                await session.scalars(
                    select(TutorQuiz)
                    .where(
                        TutorQuiz.objective_id == objective_id,
                        TutorQuiz.owner_id == scope.actor.id,
                    )
                    .order_by(TutorQuiz.created_at, TutorQuiz.id)
                    .limit(50)
                )
            )
            return {
                "trust": "UNTRUSTED_LEARNING_DATA",
                "objective": await self._objective_view(session, scope, objective),
                "lessons": [self._lesson_view(row) for row in lessons],
                "quizzes": [self._quiz_view(row) for row in quizzes],
            }

    @staticmethod
    def _attempt_view(attempt: TutorAttempt) -> dict:
        return {
            "id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "objective_id": attempt.objective_id,
            "submission_id": attempt.submission_id,
            "correct": attempt.correct,
            "score": attempt.score,
            "evaluator": attempt.evaluator,
            "origin": attempt.origin,
            "attempt_number": attempt.attempt_number,
            "evaluated_at": attempt.evaluated_at.isoformat(),
        }

    async def _apply_mastery(self, session, scope: TutorScope, objective) -> MasteryEvidence | None:
        attempts = list(
            await session.scalars(
                select(TutorAttempt)
                .where(
                    TutorAttempt.objective_id == objective.id,
                    TutorAttempt.owner_id == scope.actor.id,
                    TutorAttempt.origin == "HUMAN_API",
                )
                .order_by(
                    TutorAttempt.evaluated_at,
                    TutorAttempt.attempt_number,
                    TutorAttempt.id,
                )
            )
        )
        latest: dict[str, TutorAttempt] = {}
        for attempt in attempts:
            latest[attempt.quiz_id] = attempt
        correct = [attempt for attempt in latest.values() if attempt.correct]
        score = round(len(correct) * 100 / len(latest)) if latest else 0
        if (
            objective.status != "MASTERED"
            and len(correct) >= objective.mastery_required_quizzes
            and score >= objective.mastery_min_score
        ):
            timestamp = self.clock()
            evidence = MasteryEvidence(
                objective_id=objective.id,
                owner_id=scope.actor.id,
                attempt_ids=[attempt.id for attempt in correct],
                distinct_quizzes=len(correct),
                score=score,
                evaluator="DETERMINISTIC_V1",
                created_at=timestamp,
            )
            session.add(evidence)
            await session.flush()
            objective.status = "MASTERED"
            objective.mastery_evidence_id = evidence.id
            objective.mastered_at = timestamp
            objective.updated_at = timestamp
            session.add(
                ReviewTask(
                    objective_id=objective.id,
                    owner_id=scope.actor.id,
                    sequence=1,
                    interval_days=REVIEW_INTERVALS[0],
                    due_at=timestamp + timedelta(days=REVIEW_INTERVALS[0]),
                    status="SCHEDULED",
                    created_at=timestamp,
                )
            )
            audit(
                session,
                scope.actor.id,
                "tutor.mastery_recorded",
                {
                    "objective_id": objective.id,
                    "evidence_id": evidence.id,
                    "attempt_ids": evidence.attempt_ids,
                    "score": score,
                },
            )
            return evidence
        return None

    async def submit_attempt(
        self, scope: TutorScope, quiz_id: str, body: LearnerAttemptCreate
    ) -> dict:
        scope.require("tutor.attempt")
        timestamp = self.clock()
        supplied_hash = answer_hash(body.answer)
        async with self.db.sessions.begin() as session:
            quiz = await session.scalar(
                select(TutorQuiz).where(
                    TutorQuiz.id == quiz_id,
                    TutorQuiz.owner_id == scope.actor.id,
                )
            )
            if quiz is None:
                raise KeyError("Quiz not found")
            objective = await self._objective(session, scope, quiz.objective_id, lock=True)
            existing = await session.scalar(
                select(TutorAttempt).where(
                    TutorAttempt.owner_id == scope.actor.id,
                    TutorAttempt.quiz_id == quiz_id,
                    TutorAttempt.submission_id == body.submission_id,
                )
            )
            if existing is not None:
                if existing.answer_hash != supplied_hash:
                    raise TutorConflict("Submission ID was already used for a different answer")
                return {
                    **self._attempt_view(existing),
                    "idempotent_replay": True,
                    "objective_status": objective.status,
                    "mastery_evidence_id": objective.mastery_evidence_id,
                }
            attempt_number = 1 + int(
                await session.scalar(
                    select(func.count(TutorAttempt.id)).where(
                        TutorAttempt.owner_id == scope.actor.id,
                        TutorAttempt.quiz_id == quiz_id,
                    )
                )
                or 0
            )
            attempt = TutorAttempt(
                quiz_id=quiz.id,
                objective_id=quiz.objective_id,
                owner_id=scope.actor.id,
                submission_id=body.submission_id,
                answer_hash=supplied_hash,
                correct=supplied_hash in quiz.answer_hashes,
                score=100 if supplied_hash in quiz.answer_hashes else 0,
                evaluator="DETERMINISTIC_V1",
                origin="HUMAN_API",
                attempt_number=attempt_number,
                evaluated_at=timestamp,
            )
            session.add(attempt)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "tutor.attempt_evaluated",
                {
                    "objective_id": objective.id,
                    "quiz_id": quiz.id,
                    "attempt_id": attempt.id,
                    "correct": attempt.correct,
                },
            )
            await self._apply_mastery(session, scope, objective)
            await session.flush()
            return {
                **self._attempt_view(attempt),
                "idempotent_replay": False,
                "objective_status": objective.status,
                "mastery_evidence_id": objective.mastery_evidence_id,
            }

    async def list_attempts(self, scope: TutorScope, objective_id: str) -> list[dict]:
        scope.require("tutor.read")
        async with self.db.sessions() as session:
            await self._objective(session, scope, objective_id)
            rows = list(
                await session.scalars(
                    select(TutorAttempt)
                    .where(
                        TutorAttempt.objective_id == objective_id,
                        TutorAttempt.owner_id == scope.actor.id,
                    )
                    .order_by(TutorAttempt.evaluated_at, TutorAttempt.id)
                    .limit(200)
                )
            )
            return [self._attempt_view(row) for row in rows]

    @staticmethod
    def _review_view(task: ReviewTask) -> dict:
        return {
            "id": task.id,
            "objective_id": task.objective_id,
            "sequence": task.sequence,
            "interval_days": task.interval_days,
            "due_at": task.due_at.isoformat(),
            "status": task.status,
            "evidence_attempt_id": task.evidence_attempt_id,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def due_reviews(self, scope: TutorScope, due_before: datetime) -> list[dict]:
        scope.require("tutor.read")
        rows = []
        async with self.db.sessions() as session:
            rows = list(
                await session.scalars(
                    select(ReviewTask)
                    .where(
                        ReviewTask.owner_id == scope.actor.id,
                        ReviewTask.status == "SCHEDULED",
                        ReviewTask.due_at <= utc(due_before),
                    )
                    .order_by(ReviewTask.due_at, ReviewTask.id)
                    .limit(100)
                )
            )
        return [self._review_view(row) for row in rows]

    async def complete_review(self, scope: TutorScope, task_id: str, attempt_id: str) -> dict:
        scope.require("tutor.attempt")
        timestamp = self.clock()
        async with self.db.sessions.begin() as session:
            task = await session.scalar(
                select(ReviewTask)
                .where(ReviewTask.id == task_id, ReviewTask.owner_id == scope.actor.id)
                .with_for_update()
            )
            if task is None:
                raise KeyError("Review task not found")
            if task.status != "SCHEDULED":
                raise TutorConflict("Review task is already completed")
            if utc(task.due_at) > timestamp:
                raise TutorConflict("Review task is not due yet")
            attempt = await session.scalar(
                select(TutorAttempt).where(
                    TutorAttempt.id == attempt_id,
                    TutorAttempt.owner_id == scope.actor.id,
                    TutorAttempt.objective_id == task.objective_id,
                    TutorAttempt.correct.is_(True),
                    TutorAttempt.origin == "HUMAN_API",
                )
            )
            if attempt is None or utc(attempt.evaluated_at) < utc(task.due_at):
                raise TutorConflict("A correct human attempt made after the due time is required")
            task.status = "COMPLETED"
            task.evidence_attempt_id = attempt.id
            task.completed_at = timestamp
            next_sequence = task.sequence + 1
            interval = REVIEW_INTERVALS[min(next_sequence - 1, len(REVIEW_INTERVALS) - 1)]
            next_task = ReviewTask(
                objective_id=task.objective_id,
                owner_id=scope.actor.id,
                sequence=next_sequence,
                interval_days=interval,
                due_at=timestamp + timedelta(days=interval),
                status="SCHEDULED",
                created_at=timestamp,
            )
            session.add(next_task)
            await session.flush()
            audit(
                session,
                scope.actor.id,
                "tutor.review_completed",
                {
                    "task_id": task.id,
                    "attempt_id": attempt.id,
                    "next_task_id": next_task.id,
                },
            )
            return {
                "completed": self._review_view(task),
                "next": self._review_view(next_task),
            }
