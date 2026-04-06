from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType, TimestampMixin


class ClassRoom(Base, TimestampMixin):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    invite_code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    knowledge_template: Mapped[dict] = mapped_column(JSONType, nullable=False)

    teacher = relationship("User", back_populates="teaching_classes")
    students = relationship("ClassStudent", back_populates="classroom", cascade="all, delete-orphan")
    knowledge_records = relationship("AIKnowledge", back_populates="classroom", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="classroom", cascade="all, delete-orphan")
    papers = relationship("TestPaper", back_populates="classroom", cascade="all, delete-orphan")
    runs = relationship("TestRun", back_populates="classroom", cascade="all, delete-orphan")


class ClassStudent(Base):
    __tablename__ = "class_students"
    __table_args__ = (UniqueConstraint("class_id", "student_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    classroom = relationship("ClassRoom", back_populates="students")
    student = relationship("User", back_populates="student_classes")
