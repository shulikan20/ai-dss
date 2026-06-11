from __future__ import annotations
import dataclasses
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from api.database.models import (
    Company,
    ExportFile,
    Feedback,
    OAuthAccount,
    QuestionnaireSession,
    Recommendation,
    RefreshToken,
    SavedTool,
    User,
)

@dataclasses.dataclass(frozen=True)
class SavedSession:
    session_id: uuid.UUID
    recommendation_id: uuid.UUID

@dataclasses.dataclass(frozen=True)
class SessionRecord:
    session_id: uuid.UUID
    recommendation_id: uuid.UUID
    tier: str
    pipeline_used: str
    llm_available: bool
    processing_time_ms: int | None
    ranked_results: list[Any]
    profile_snapshot: dict[str, Any]
    created_at: datetime

@dataclasses.dataclass(frozen=True)
class FeedbackRecord:
    feedback_id: uuid.UUID
    recommendation_id: uuid.UUID
    capability_id: str
    rating: int | None
    was_implemented: bool | None
    created_at: datetime

@dataclasses.dataclass(frozen=True)
class SavedToolRecord:
    capability_id: str
    capability_name: str | None
    saved_at: datetime

class SessionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self,
        *,
        tier: str,
        domains: list[str],
        bottleneck_text: str,
        answers: dict[str, Any],
        profile_snapshot: dict[str, Any],
        pipeline_used: str,
        llm_available: bool,
        processing_time_ms: int | None,
        ranked_results: list[Any],
        company_id: uuid.UUID | None = None,
        export_summary: str | None = None,
    ) -> SavedSession:
        session = QuestionnaireSession(
            company_id=company_id,
            tier=tier,
            domains=domains,
            bottleneck_text=bottleneck_text,
            answers=answers,
            export_summary=export_summary,
            profile_snapshot=profile_snapshot,
        )
        self._db.add(session)
        self._db.flush()

        recommendation = Recommendation(
            session_id=session.id,
            pipeline_used=pipeline_used,
            llm_available=llm_available,
            processing_time_ms=processing_time_ms,
            ranked_results=ranked_results,
        )
        self._db.add(recommendation)
        self._db.flush()

        return SavedSession(
            session_id=session.id,
            recommendation_id=recommendation.id,
        )

    def get_by_company(self, company_id: uuid.UUID) -> list[SessionRecord]:
        rows = (
            self._db.query(QuestionnaireSession, Recommendation)
            .join(Recommendation, Recommendation.session_id == QuestionnaireSession.id)
            .filter(QuestionnaireSession.company_id == company_id)
            .order_by(QuestionnaireSession.created_at.desc())
            .all()
        )
        return [
            SessionRecord(
                session_id=s.id,
                recommendation_id=r.id,
                tier=s.tier,
                pipeline_used=r.pipeline_used,
                llm_available=r.llm_available,
                processing_time_ms=r.processing_time_ms,
                ranked_results=r.ranked_results,
                profile_snapshot=s.profile_snapshot,
                created_at=s.created_at,
            )
            for s, r in rows
        ]

    def get_recommendation(self, recommendation_id: uuid.UUID) -> Recommendation | None:
        return (
            self._db.query(Recommendation)
            .filter(Recommendation.id == recommendation_id)
            .first()
        )

    def get_session(self, session_id: uuid.UUID) -> QuestionnaireSession | None:
        return (
            self._db.query(QuestionnaireSession)
            .filter(QuestionnaireSession.id == session_id)
            .first()
        )

class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self,
        *,
        recommendation_id: uuid.UUID,
        capability_id: str,
        rating: int | None = None,
        comment: str | None = None,
        was_implemented: bool | None = None,
    ) -> FeedbackRecord:
        if rating is not None and not (1 <= rating <= 5):
            raise ValueError(f"Rating must be between 1 and 5, got {rating!r}")

        fb = Feedback(
            recommendation_id=recommendation_id,
            capability_id=capability_id,
            rating=rating,
            comment=comment,
            was_implemented=was_implemented,
        )
        self._db.add(fb)
        self._db.flush()

        return FeedbackRecord(
            feedback_id=fb.id,
            recommendation_id=fb.recommendation_id,
            capability_id=fb.capability_id,
            rating=fb.rating,
            was_implemented=fb.was_implemented,
            created_at=fb.created_at,
        )

    def get_by_recommendation(self, recommendation_id: uuid.UUID) -> list[FeedbackRecord]:
        rows = (
            self._db.query(Feedback)
            .filter(Feedback.recommendation_id == recommendation_id)
            .order_by(Feedback.created_at)
            .all()
        )
        return [
            FeedbackRecord(
                feedback_id=r.id,
                recommendation_id=r.recommendation_id,
                capability_id=r.capability_id,
                rating=r.rating,
                was_implemented=r.was_implemented,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def anonymize_for_user(self, recommendation_ids: list[uuid.UUID]) -> int:
        if not recommendation_ids:
            return 0
        updated = (
            self._db.query(Feedback)
            .filter(Feedback.recommendation_id.in_(recommendation_ids))
            .update({"comment": None}, synchronize_session=False)
        )
        return updated

class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_company(
        self,
        *,
        company_name: str,
        country: str,
        user_id: uuid.UUID | None = None,
    ) -> Company:
        company = Company(
            company_name=company_name,
            country=country.upper(),
            user_id=user_id,
        )
        self._db.add(company)
        self._db.flush()
        return company

    def get_company(self, company_id: uuid.UUID) -> Company | None:
        return (
            self._db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )
    
    def get_or_create_company(
        self,
        *,
        company_name: str,
        country: str,
        user_id: uuid.UUID,
    ) -> Company:
        existing = (
            self._db.query(Company)
            .filter(
                Company.user_id == user_id,
                Company.company_name == company_name,
                Company.country == country.upper(),
            )
            .first()
        )
        if existing is not None:
            return existing
        return self.create_company(
            company_name=company_name, country=country, user_id=user_id
        )

    def create_user(self, *, email: str, password_hash: str) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
        )
        self._db.add(user)
        self._db.flush()
        return user

    def get_user_by_email(self, email: str) -> User | None:
        return (
            self._db.query(User)
            .filter(
                User.email == email.lower().strip(),
                User.deleted_at.is_(None),
            )
            .first()
        )

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return (
            self._db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )

    def soft_delete_user(self, user_id: uuid.UUID) -> None:
        user = self._db.query(User).filter(User.id == user_id).first()
        if user is None:
            return
        user.deleted_at = datetime.now(timezone.utc)
        self._db.flush()

    def get_recommendation_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        rows = (
            self._db.query(Recommendation.id)
            .join(QuestionnaireSession, Recommendation.session_id == QuestionnaireSession.id)
            .join(Company, QuestionnaireSession.company_id == Company.id)
            .filter(Company.user_id == user_id)
            .all()
        )
        return [r[0] for r in rows]

class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(rt)
        self._db.flush()
        return rt

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        now = datetime.now(timezone.utc)
        return (
            self._db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
            .first()
        )

    def revoke(self, token_hash: str) -> bool:
        rt = (
            self._db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
        if rt is None:
            return False
        rt.revoked = True
        self._db.flush()
        return True

    def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        count = (
            self._db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .update({"revoked": True}, synchronize_session=False)
        )
        return count

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        count = (
            self._db.query(RefreshToken)
            .filter(RefreshToken.expires_at <= now)
            .delete(synchronize_session=False)
        )
        return count

class ExportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_result(
        self,
        *,
        session_id: uuid.UUID | None,
        export_type: str,
        metrics: dict[str, Any] | None = None,
        pain_flags_inferred: dict[str, bool] | None = None,
        file_path: str | None = None,
    ) -> ExportFile:
        ef = ExportFile(
            session_id=session_id,
            export_type=export_type,
            metrics=metrics,
            pain_flags_inferred=pain_flags_inferred,
            file_path=file_path,
        )
        self._db.add(ef)
        self._db.flush()
        return ef
    
class OAuthAccountRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_provider(
        self, *, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        return (
            self._db.query(OAuthAccount)
            .filter(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
            .first()
        )

    def create(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        provider_user_id: str,
        email: str | None = None,
    ) -> OAuthAccount:
        oa = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )
        self._db.add(oa)
        self._db.flush()
        return oa

    def find_or_create_user(
        self,
        *,
        provider: str,
        provider_user_id: str,
        email: str | None,
    ) -> User:
        existing = self.get_by_provider(
            provider=provider, provider_user_id=provider_user_id
        )
        if existing:
            user = (
                self._db.query(User)
                .filter(User.id == existing.user_id, User.deleted_at.is_(None))
                .first()
            )
            if user:
                return user

        if email:
            user_repo = UserRepository(self._db)
            user = user_repo.get_user_by_email(email)
            if user:
                self.create(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    email=email,
                )
                return user

        user = User(
            email=(email or f"{provider}_{provider_user_id}@oauth.local").lower(),
            password_hash="",
            email_verified=True if email else False,
        )
        self._db.add(user)
        self._db.flush()

        self.create(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )
        return user
    
class SavedToolRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self,
        *,
        user_id: uuid.UUID,
        capability_id: str,
        capability_name: str | None = None,
    ) -> SavedTool:
        existing = (
            self._db.query(SavedTool)
            .filter(
                SavedTool.user_id == user_id,
                SavedTool.capability_id == capability_id,
            )
            .first()
        )
        if existing is not None:
            return existing
        saved = SavedTool(
            user_id=user_id,
            capability_id=capability_id,
            capability_name=capability_name,
        )
        self._db.add(saved)
        self._db.flush()
        return saved

    def list_for_user(self, user_id: uuid.UUID) -> list[SavedToolRecord]:
        rows = (
            self._db.query(SavedTool)
            .filter(SavedTool.user_id == user_id)
            .order_by(SavedTool.saved_at.desc())
            .all()
        )
        return [
            SavedToolRecord(
                capability_id=r.capability_id,
                capability_name=r.capability_name,
                saved_at=r.saved_at,
            )
            for r in rows
        ]

    def delete(self, *, user_id: uuid.UUID, capability_id: str) -> bool:
        deleted = (
            self._db.query(SavedTool)
            .filter(
                SavedTool.user_id == user_id,
                SavedTool.capability_id == capability_id,
            )
            .delete(synchronize_session=False)
        )
        self._db.flush()
        return bool(deleted)