from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from api.database.models import User
from src.export_analyser import validator
from src.export_analyser.hybrid import analyse as analyse_export
from src.export_analyser.models import DataInsight, ValidationResult
from src.catalog.pain_flags import PainFlags

router = APIRouter()

_MAX_BYTES = 10 * 1024 * 1024
_PAIN_FLAG_APPLY_THRESHOLD = 0.7
_VALID_FLAGS = frozenset(PainFlags.all_paths())

async def _read_capped(file: UploadFile) -> bytes:
    content = await file.read(_MAX_BYTES + 1)
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit.")
    return content

@router.post("/export/validate", response_model=ValidationResult)
async def export_validate(file: UploadFile = File(...)) -> ValidationResult:
    content = await _read_capped(file)
    return validator.validate(file.filename or "", content)

@router.post("/export/analyse", response_model=DataInsight)
async def export_analyse(
    file: UploadFile = File(...),
    language_hint: str | None = Form(default=None),
) -> DataInsight:
    content = await _read_capped(file)
    insight = analyse_export(file.filename or "", content, language_hint=language_hint)
    return insight

class ApplyRequest(BaseModel):
    insight: DataInsight
    override_questionnaire: bool = Field(
        default=False,
        description="If true, high-confidence suggested pain flags are returned "
                    "for application to the assessment (user-confirmed).",
    )

class ApplyResponse(BaseModel):
    bottleneck_enrichment: str
    data_readiness_contribution: float | None = None
    pain_flags_to_apply: dict[str, float]
    note: str

@router.post("/export/apply", response_model=ApplyResponse)
def export_apply(body: ApplyRequest, user: User = Depends(get_current_user)) -> ApplyResponse:
    ins = body.insight
    to_apply: dict[str, float] = {}
    if body.override_questionnaire:
        to_apply = {
            flag: round(conf, 2)
            for flag, conf in ins.pain_flags_suggested.items()
            if conf >= _PAIN_FLAG_APPLY_THRESHOLD and flag in _VALID_FLAGS
        }
    note = (
        f"{len(to_apply)} pain flag(s) will be added to your assessment."
        if to_apply else
        "No pain flags applied (confirm 'use detected pain points' to apply them)."
    )
    return ApplyResponse(
        bottleneck_enrichment=ins.bottleneck_enrichment,
        data_readiness_contribution=ins.data_readiness_contribution,
        pain_flags_to_apply=to_apply,
        note=note,
    )
