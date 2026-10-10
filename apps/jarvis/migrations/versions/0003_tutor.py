"""Canonical Tutor objectives, learner evidence, mastery and reviews."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "learning_objectives",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("mastery_required_quizzes", sa.Integer, nullable=False),
        sa.Column("mastery_min_score", sa.Integer, nullable=False),
        sa.Column("mastery_evidence_id", sa.String(36), nullable=True),
        sa.Column("mastered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE','MASTERED','ARCHIVED')", name="ck_learning_objective_status"
        ),
        sa.CheckConstraint(
            "mastery_required_quizzes >= 1 AND mastery_required_quizzes <= 10",
            name="ck_learning_objective_required_quizzes",
        ),
        sa.CheckConstraint(
            "mastery_min_score >= 50 AND mastery_min_score <= 100",
            name="ck_learning_objective_min_score",
        ),
    )
    op.create_index("ix_learning_objectives_owner_id", "learning_objectives", ["owner_id"])
    op.create_index(
        "ix_learning_objective_owner_status",
        "learning_objectives",
        ["owner_id", "status", "updated_at"],
    )
    op.create_table(
        "learning_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "objective_id",
            sa.String(36),
            sa.ForeignKey("learning_objectives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("locator", sa.String(300), nullable=False),
        sa.Column("quote", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_learning_sources_objective_id", "learning_sources", ["objective_id"])
    op.create_index("ix_learning_sources_owner_id", "learning_sources", ["owner_id"])
    op.create_table(
        "tutor_lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "objective_id",
            sa.String(36),
            sa.ForeignKey("learning_objectives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source_ids", sa.JSON, nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('EXPLANATION','WORKED_EXAMPLE','SOCRATIC')", name="ck_tutor_lesson_kind"
        ),
        sa.CheckConstraint("origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_tutor_lesson_origin"),
    )
    op.create_index("ix_tutor_lessons_objective_id", "tutor_lessons", ["objective_id"])
    op.create_index("ix_tutor_lessons_owner_id", "tutor_lessons", ["owner_id"])
    op.create_table(
        "tutor_quizzes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "objective_id",
            sa.String(36),
            sa.ForeignKey("learning_objectives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("answer_hashes", sa.JSON, nullable=False),
        sa.Column("source_ids", sa.JSON, nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("origin IN ('HUMAN_API','MODEL_TOOL')", name="ck_tutor_quiz_origin"),
    )
    op.create_index("ix_tutor_quizzes_objective_id", "tutor_quizzes", ["objective_id"])
    op.create_index("ix_tutor_quizzes_owner_id", "tutor_quizzes", ["owner_id"])
    op.create_table(
        "tutor_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("quiz_id", sa.String(36), sa.ForeignKey("tutor_quizzes.id"), nullable=False),
        sa.Column(
            "objective_id", sa.String(36), sa.ForeignKey("learning_objectives.id"), nullable=False
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("submission_id", sa.String(80), nullable=False),
        sa.Column("answer_hash", sa.String(64), nullable=False),
        sa.Column("correct", sa.Boolean, nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("evaluator", sa.String(32), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("attempt_number", sa.Integer, nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "quiz_id", "submission_id"),
        sa.CheckConstraint("origin = 'HUMAN_API'", name="ck_tutor_attempt_origin"),
        sa.CheckConstraint("score IN (0,100)", name="ck_tutor_attempt_score"),
    )
    for column in ["quiz_id", "objective_id", "owner_id"]:
        op.create_index(f"ix_tutor_attempts_{column}", "tutor_attempts", [column])
    op.create_table(
        "mastery_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "objective_id", sa.String(36), sa.ForeignKey("learning_objectives.id"), nullable=False
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("attempt_ids", sa.JSON, nullable=False),
        sa.Column("distinct_quizzes", sa.Integer, nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("evaluator", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("objective_id"),
    )
    op.create_index("ix_mastery_evidence_objective_id", "mastery_evidence", ["objective_id"])
    op.create_index("ix_mastery_evidence_owner_id", "mastery_evidence", ["owner_id"])
    op.create_table(
        "review_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "objective_id", sa.String(36), sa.ForeignKey("learning_objectives.id"), nullable=False
        ),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("interval_days", sa.Integer, nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("evidence_attempt_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("objective_id", "sequence"),
        sa.CheckConstraint("status IN ('SCHEDULED','COMPLETED')", name="ck_review_task_status"),
        sa.CheckConstraint("sequence >= 1", name="ck_review_task_sequence"),
        sa.CheckConstraint("interval_days >= 1", name="ck_review_task_interval"),
    )
    for column in ["objective_id", "owner_id", "due_at"]:
        op.create_index(f"ix_review_tasks_{column}", "review_tasks", [column])


def downgrade():
    op.drop_table("review_tasks")
    op.drop_table("mastery_evidence")
    op.drop_table("tutor_attempts")
    op.drop_table("tutor_quizzes")
    op.drop_table("tutor_lessons")
    op.drop_table("learning_sources")
    op.drop_table("learning_objectives")
