from __future__ import annotations

from dataclasses import dataclass, field

from ..models import ColumnMap, DataType, ReadKind, ReadResult
from . import fingerprinter, type_classifier, value_inferrer

@dataclass
class ClassicalResult:
    data_type: DataType
    data_type_confidence: float
    column_map: ColumnMap
    value_roles: dict[str, str] = field(default_factory=dict)
    fields_present: set[str] = field(default_factory=set)

def analyse_classical(read: ReadResult) -> ClassicalResult:
    if read.kind is not ReadKind.tabular or not read.columns:
        return ClassicalResult(
            data_type=DataType.unknown, data_type_confidence=0.0,
            column_map=ColumnMap(data_type=DataType.unknown, method="CA-classical"),
        )

    fp = fingerprinter.fingerprint(read.columns)
    roles = value_inferrer.infer_roles(read.records, read.columns)
    data_type, confidence = type_classifier.classify(
        fp.fields_present, roles, read.n_rows
    )

    core = _CORE_FIELDS.get(data_type, set())
    named_core = len(fp.fields_present & core)
    map_conf = round(named_core / len(core), 3) if core else 0.0

    column_map = ColumnMap(
        data_type=data_type,
        mapping=dict(fp.mapping),
        confidence=map_conf,
        method="CA-classical",
    )
    return ClassicalResult(
        data_type=data_type,
        data_type_confidence=confidence,
        column_map=column_map,
        value_roles=roles,
        fields_present=fp.fields_present,
    )

_CORE_FIELDS = {
    DataType.orders: {"date", "amount", "status", "channel", "product_name"},
    DataType.support_tickets: {"created_at", "first_response_at", "status", "subject"},
    DataType.crm_leads: {"lead_name", "stage", "channel"},
    DataType.inventory: {"product_name", "stock_quantity"},
    DataType.analytics: {"date", "amount"},
}
