"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-04

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # --- classes ---
    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(10), nullable=False),
        sa.Column("knowledge_template", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_classes_teacher_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classes")),
        sa.UniqueConstraint("invite_code", name=op.f("uq_classes_invite_code")),
    )
    op.create_index(op.f("ix_classes_teacher_id"), "classes", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_classes_invite_code"), "classes", ["invite_code"], unique=True)

    # --- class_students ---
    op.create_table(
        "class_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_class_students_class_id_classes")),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], name=op.f("fk_class_students_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_class_students")),
        sa.UniqueConstraint("class_id", "student_id", name=op.f("uq_class_students_class_id")),
    )
    op.create_index(op.f("ix_class_students_class_id"), "class_students", ["class_id"], unique=False)
    op.create_index(op.f("ix_class_students_student_id"), "class_students", ["student_id"], unique=False)

    # --- ai_knowledge ---
    op.create_table(
        "ai_knowledge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("knowledge_data", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_ai_knowledge_class_id_classes")),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], name=op.f("fk_ai_knowledge_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_knowledge")),
        sa.UniqueConstraint("student_id", "class_id", name=op.f("uq_ai_knowledge_student_id")),
    )
    op.create_index(op.f("ix_ai_knowledge_student_id"), "ai_knowledge", ["student_id"], unique=False)
    op.create_index(op.f("ix_ai_knowledge_class_id"), "ai_knowledge", ["class_id"], unique=False)

    # --- knowledge_change_logs ---
    op.create_table(
        "knowledge_change_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("knowledge_id", sa.Integer(), nullable=False),
        sa.Column("target_item_id", sa.String(50), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_knowledge_change_logs_actor_user_id_users")),
        sa.ForeignKeyConstraint(["knowledge_id"], ["ai_knowledge.id"], name=op.f("fk_knowledge_change_logs_knowledge_id_ai_knowledge")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_change_logs")),
    )
    op.create_index(op.f("ix_knowledge_change_logs_knowledge_id"), "knowledge_change_logs", ["knowledge_id"], unique=False)
    op.create_index(op.f("ix_knowledge_change_logs_target_item_id"), "knowledge_change_logs", ["target_item_id"], unique=False)
    op.create_index(op.f("ix_knowledge_change_logs_actor_user_id"), "knowledge_change_logs", ["actor_user_id"], unique=False)

    # --- chat_sessions ---
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("session_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_chat_sessions_class_id_classes")),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], name=op.f("fk_chat_sessions_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
    )
    op.create_index(op.f("ix_chat_sessions_student_id"), "chat_sessions", ["student_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_class_id"), "chat_sessions", ["class_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_session_type"), "chat_sessions", ["session_type"], unique=False)

    # --- chat_messages ---
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("knowledge_extracted", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], name=op.f("fk_chat_messages_session_id_chat_sessions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False)

    # --- session_summaries ---
    op.create_table(
        "session_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("summary_content", sa.String(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], name=op.f("fk_session_summaries_session_id_chat_sessions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_summaries")),
    )
    op.create_index(op.f("ix_session_summaries_session_id"), "session_summaries", ["session_id"], unique=False)

    # --- test_papers ---
    op.create_table(
        "test_papers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_test_papers_class_id_classes")),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], name=op.f("fk_test_papers_teacher_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_papers")),
    )
    op.create_index(op.f("ix_test_papers_class_id"), "test_papers", ["class_id"], unique=False)
    op.create_index(op.f("ix_test_papers_teacher_id"), "test_papers", ["teacher_id"], unique=False)

    # --- test_questions ---
    op.create_table(
        "test_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paper_id", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(), nullable=False),
        sa.Column("option_a", sa.String(), nullable=False),
        sa.Column("option_b", sa.String(), nullable=False),
        sa.Column("option_c", sa.String(), nullable=False),
        sa.Column("option_d", sa.String(), nullable=False),
        sa.Column("correct_answer", sa.CHAR(1), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["test_papers.id"], name=op.f("fk_test_questions_paper_id_test_papers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_questions")),
    )
    op.create_index(op.f("ix_test_questions_paper_id"), "test_questions", ["paper_id"], unique=False)

    # --- test_runs ---
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paper_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("progress_completed", sa.Integer(), nullable=False),
        sa.Column("progress_total", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], name=op.f("fk_test_runs_class_id_classes")),
        sa.ForeignKeyConstraint(["paper_id"], ["test_papers.id"], name=op.f("fk_test_runs_paper_id_test_papers")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_runs")),
    )
    op.create_index(op.f("ix_test_runs_paper_id"), "test_runs", ["paper_id"], unique=False)
    op.create_index(op.f("ix_test_runs_class_id"), "test_runs", ["class_id"], unique=False)
    op.create_index(op.f("ix_test_runs_status"), "test_runs", ["status"], unique=False)

    # --- test_results ---
    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paper_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("tested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["test_papers.id"], name=op.f("fk_test_results_paper_id_test_papers")),
        sa.ForeignKeyConstraint(["run_id"], ["test_runs.id"], name=op.f("fk_test_results_run_id_test_runs")),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], name=op.f("fk_test_results_student_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test_results")),
    )
    op.create_index(op.f("ix_test_results_paper_id"), "test_results", ["paper_id"], unique=False)
    op.create_index(op.f("ix_test_results_student_id"), "test_results", ["student_id"], unique=False)
    op.create_index(op.f("ix_test_results_run_id"), "test_results", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_table("test_results")
    op.drop_table("test_runs")
    op.drop_table("test_questions")
    op.drop_table("test_papers")
    op.drop_table("session_summaries")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("knowledge_change_logs")
    op.drop_table("ai_knowledge")
    op.drop_table("class_students")
    op.drop_table("classes")
    op.drop_table("users")
