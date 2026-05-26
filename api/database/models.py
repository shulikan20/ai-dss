from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    companies: Mapped[list[Company]] = relationship(
        "Company", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} active={self.deleted_at is None}>"

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_token_hash", "token_hash"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user={self.user_id} revoked={self.revoked}>"

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped[User | None] = relationship("User", back_populates="companies")
    sessions: Mapped[list[QuestionnaireSession]] = relationship(
        "QuestionnaireSession", back_populates="company", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_companies_user_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.company_name!r} country={self.country}>"

class QuestionnaireSession(Base):
    __tablename__ = "questionnaire_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    domains: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    bottleneck_text: Mapped[str] = mapped_column(Text, nullable=False)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    export_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    company: Mapped[Company | None] = relationship("Company", back_populates="sessions")
    recommendations: Mapped[list[Recommendation]] = relationship(
        "Recommendation", back_populates="session", cascade="all, delete-orphan"
    )
    export_files: Mapped[list[ExportFile]] = relationship(
        "ExportFile", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sessions_company_id", "company_id"),
        Index("ix_sessions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<QuestionnaireSession id={self.id} tier={self.tier!r}>"

class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_used: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    llm_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ranked_results: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session: Mapped[QuestionnaireSession] = relationship(
        "QuestionnaireSession", back_populates="recommendations"
    )
    feedback: Mapped[list[Feedback]] = relationship(
        "Feedback", back_populates="recommendation", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_recommendations_session_id", "session_id"),)

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} pipeline={self.pipeline_used!r}>"

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
    )
    capability_id: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[int | None] = mapped_column(
        SmallInteger,
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_feedback_rating"),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    was_implemented: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    recommendation: Mapped[Recommendation] = relationship(
        "Recommendation", back_populates="feedback"
    )

    __table_args__ = (
        Index("ix_feedback_recommendation_id", "recommendation_id"),
        Index("ix_feedback_capability_id", "capability_id"),
    )

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} cap={self.capability_id!r} rating={self.rating}>"

class ExportFile(Base):
    __tablename__ = "export_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    export_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    pain_flags_inferred: Mapped[dict[str, bool] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session: Mapped[QuestionnaireSession | None] = relationship(
        "QuestionnaireSession", back_populates="export_files"
    )

    def __repr__(self) -> str:
        return f"<ExportFile id={self.id} type={self.export_type!r}>"