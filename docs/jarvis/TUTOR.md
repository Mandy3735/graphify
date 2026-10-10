# Tutor workflow — phase 7

The 0.4.0 backend implements a persisted, source-grounded Tutor workflow. Tutor
state is canonical application data in PostgreSQL and remains separate from
personal memory and Graphify's code graph.

## Authority and evidence boundary

The configured actor needs `tutor.read`, `tutor.write` and `tutor.attempt` as
appropriate. Every query filters by the server-bound actor before returning
objectives, sources, lessons, quizzes, attempts, mastery evidence or reviews.
API and model bodies cannot choose an actor or add capabilities.

The model has three TUTOR-only tools: `tutor.context`, `tutor.create_lesson` and
`tutor.create_quiz`. Each is bound to the active run's learning objective. There
is no model tool for submitting an attempt, assigning a score, recording mastery
or completing a review. Source text, lessons and quiz prompts are labeled
untrusted data and cannot grant authority.

Learner responses enter only through the authenticated
`POST /api/tutor/quizzes/{quiz_id}/attempts` endpoint. The server stamps every
attempt `HUMAN_API`, normalizes Unicode/case/whitespace, hashes the response and
performs deterministic exact-answer evaluation. Request bodies cannot supply
correctness, score, evaluator, origin or mastery. Accepted answers are stored as
hashes and are omitted from quiz/context responses.

## Canonical workflow

1. Create an objective with one or more bounded source excerpts. Each excerpt
   retains kind, locator, quote and SHA-256 content hash.
2. Create explanations, worked examples or Socratic prompts citing source IDs
   belonging to that objective.
3. Create quizzes citing those same objective-owned sources. The current
   deterministic evaluator is intentionally narrow; answers requiring semantic
   or expert judgment remain future work.
4. Submit learner attempts with a client-generated submission ID. Replaying the
   same ID and answer returns the original attempt; changing the answer conflicts.
   Retries receive increasing attempt numbers.
5. Mastery uses the latest human attempt for each distinct quiz. It is recorded
   once only when both the configured distinct-correct count and minimum score are
   met. The immutable evidence row retains exact attempt IDs and evaluator version.
6. Mastery schedules a one-day review. A review can be completed only after it is
   due and only with a correct human attempt made at or after that due time.
   Follow-up intervals are 3, 7, 14 and then 30 days.

Concurrent PostgreSQL attempts lock the objective before recomputing mastery.
Unique submission and objective/evidence constraints prevent duplicate attempts,
mastery records and review sequence entries. Audit events retain identifiers and
evaluation outcomes without learner response text or accepted answers.

## API surface

- `POST/GET /api/tutor/objectives`
- `GET /api/tutor/objectives/{id}` and `/context`
- `POST /api/tutor/objectives/{id}/lessons`
- `POST /api/tutor/objectives/{id}/quizzes`
- `POST /api/tutor/quizzes/{id}/attempts`
- `GET /api/tutor/objectives/{id}/attempts`
- `GET /api/tutor/reviews?due_before=<timezone-aware timestamp>`
- `POST /api/tutor/reviews/{id}/complete`

Migration 0003 creates dedicated objective/source/lesson/quiz/attempt/mastery/review
tables. It does not alter personal memory or the preserved Graphify subsystem.

## Current limits

This checkpoint supports deterministic short-answer quizzes. It does not claim
semantic grading, rubric moderation, plagiarism detection, classroom sharing,
course imports, a Tutor UI or notification delivery. A bearer-token holder is the
human evidence channel in this single-user prototype; production identity/session
hardening remains required. Review tasks are persisted and queryable but no watcher
or outbound reminder is enabled.
