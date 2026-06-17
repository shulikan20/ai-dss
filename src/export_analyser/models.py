from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

class FileFormat(str, Enum):
    csv = "csv"
    tsv = "tsv"
    xlsx = "xlsx"
    xls = "xls"
    json = "json"
    jsonl = "jsonl"
    pdf_text = "pdf_text"
    pdf_image = "pdf_image"
    image = "image"
    unknown = "unknown"

class DataType(str, Enum):
    orders = "orders"
    crm_leads = "crm_leads"
    support_tickets = "support_tickets"
    analytics = "analytics"
    inventory = "inventory"
    unknown = "unknown"

class ReadKind(str, Enum):
    tabular = "tabular"
    text = "text"
    image = "image"
    none = "none"

@dataclass
class ReadResult:
    fmt: FileFormat
    kind: ReadKind
    columns: list[str] = field(default_factory=list)
    records: list[dict] = field(default_factory=list)
    n_rows: int = 0
    text: str | None = None
    image_page_count: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.kind is not ReadKind.none

class ValidationResult(BaseModel):
    can_analyze: bool
    format_detected: FileFormat
    data_type_hint: DataType | None = None
    reason: str
    suggested_action: str | None = None

class MetricSet(BaseModel):
    total_records: int | None = None
    date_range_months: int | None = None
    channels: list[str] = Field(default_factory=list)
    avg_response_time_hours: float | None = None
    open_items: int | None = None
    closed_items: int | None = None
    peak_month: str | None = None
    seasonality_cv: float | None = None
    avg_order_value: float | None = None
    fulfillment_null_pct: float | None = None
    model_config = {"extra": "allow"}

class ColumnMap(BaseModel):
    platform: str | None = None
    data_type: DataType = DataType.unknown
    mapping: dict[str, str] = Field(default_factory=dict)
    confidence: float = 0.0
    method: str | None = None

class DataInsight(BaseModel):
    analyzable: bool
    validation_message: str = ""
    format_detected: FileFormat
    data_type: DataType = DataType.unknown
    data_type_confidence: float = 0.0
    metrics: MetricSet = Field(default_factory=MetricSet)
    bottleneck_enrichment: str = ""
    pain_flags_suggested: dict[str, float] = Field(default_factory=dict)
    data_readiness_contribution: float | None = None
    parse_confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)
