from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False)

    teaching_classes = relationship("ClassRoom", back_populates="teacher")
    student_classes = relationship("ClassStudent", back_populates="student")
    chat_sessions = relationship("ChatSession", back_populates="student")
    knowledge_records = relationship("AIKnowledge", back_populates="student")
    created_papers = relationship("TestPaper", back_populates="teacher")

