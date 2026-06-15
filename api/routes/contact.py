from __future__ import annotations

import logging
import os
import smtplib
import time
from email.message import EmailMessage
from typing import Literal
import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.database.repository import ContactRequestRepository

logger = logging.getLogger(__name__)
router = APIRouter()

_RATE_LIMIT = 3
_RATE_WINDOW_SEC = 3600
_RATE_BUCKET: dict[str, list[float]] = {}


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    stamps = [t for t in _RATE_BUCKET.get(ip, []) if now - t < _RATE_WINDOW_SEC]
    if len(stamps) >= _RATE_LIMIT:
        _RATE_BUCKET[ip] = stamps
        return False
    stamps.append(now)
    _RATE_BUCKET[ip] = stamps
    return True

class ContactSubmission(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    email: EmailStr
    domain: str | None = Field(default=None, max_length=100)
    message: str = Field(min_length=10, max_length=5000)
    budget_range: Literal[
        "under_5k", "5k_20k", "over_20k", "prefer_not_to_say"
    ] | None = None
    consent: bool

    @field_validator("consent")
    @classmethod
    def consent_must_be_given(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Consent to be contacted is required.")
        return v


class ContactResponse(BaseModel):
    detail: str

def _send_contact_email(submission: ContactSubmission) -> bool:
    to_addr = os.environ.get("CONTACT_EMAIL")
    smtp_host = os.environ.get("SMTP_HOST")
    if not to_addr or not smtp_host:
        logger.info("Contact email not configured (CONTACT_EMAIL/SMTP_HOST unset)")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"[AI-DSS] New inquiry from {submission.name}"
    msg["From"] = os.environ.get("SMTP_FROM", "no-reply@ai-dss.local")
    msg["To"] = to_addr
    msg.set_content(
        f"Name: {submission.name}\n"
        f"Company: {submission.company or '—'}\n"
        f"Email: {submission.email}\n"
        f"Domain: {submission.domain or '—'}\n"
        f"Budget: {submission.budget_range or '—'}\n\n"
        f"{submission.message}\n"
    )

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    with smtplib.SMTP(smtp_host, port, timeout=10) as smtp:
        smtp.starttls()
        if user and password:
            smtp.login(user, password)
        smtp.send_message(msg)
    return True


def _fire_crm_webhook(submission: ContactSubmission) -> None:
    url = os.environ.get("CONTACT_WEBHOOK_URL")
    if not url:
        return
    try:
        http_requests.post(url, json=submission.model_dump(), timeout=5)
    except Exception:
        logger.exception("Contact webhook delivery failed (submission is stored)")


@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a consulting inquiry (Work With Us)",
)
def submit_contact(
    request: Request,
    body: ContactSubmission,
    db: Session = Depends(get_db),
) -> ContactResponse:
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many contact requests. Please try again later.",
        )

    ContactRequestRepository(db).save(
        name=body.name,
        company=body.company,
        email=body.email,
        domain=body.domain,
        message=body.message,
        budget_range=body.budget_range,
        client_ip=client_ip,
    )

    try:
        _send_contact_email(body)
    except Exception:
        logger.exception("Contact email failed (submission is stored)")
    _fire_crm_webhook(body)

    logger.info("Contact request stored from %s <%s>", body.name, body.email)
    return ContactResponse(
        detail="Thanks — your inquiry was received. We will get back to you shortly."
    )
