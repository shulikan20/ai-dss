from __future__ import annotations

from .. import enrichment as enr
from .. import format_reader, metrics as metrics_mod
from ..classical import analyse_classical
from ..llm import column_mapper, signal_extractor, vision_analyser
from ..llm.client import ollama_available
from ..models import ColumnMap, DataInsight, DataType, FileFormat, ReadKind, ReadResult

_LLM_FALLBACK_THRESHOLD = 0.5

def analyse(filename: str, content: bytes, *, allow_llm: bool = True,
            language_hint: str | None = None) -> DataInsight:
    read = format_reader.read(filename, content, language_hint=language_hint)

    if read.kind is ReadKind.none or read.error:
        return DataInsight(
            analyzable=False, format_detected=read.fmt,
            validation_message=read.error or "This file could not be analysed.",
            parse_confidence=0.0,
        )

    if read.kind is ReadKind.tabular:
        return _analyse_tabular(read, allow_llm)
    if read.kind is ReadKind.image:
        return _analyse_image(read, content, allow_llm)
    if read.kind is ReadKind.text:
        return _analyse_text(read, allow_llm)

    return DataInsight(analyzable=False, format_detected=read.fmt,
                       validation_message="Unsupported content.", parse_confidence=0.0)

def _analyse_tabular(read: ReadResult, allow_llm: bool) -> DataInsight:
    classical = analyse_classical(read)
    column_map = classical.column_map
    data_type = classical.data_type
    parse_conf = classical.data_type_confidence
    used_llm_mapping = False

    weak = data_type is DataType.unknown or column_map.confidence < _LLM_FALLBACK_THRESHOLD
    if allow_llm and weak and ollama_available():
        la1 = column_mapper.map_columns(read)
        if la1 and la1.mapping:
            merged = dict(la1.mapping)
            merged.update(column_map.mapping)
            column_map = ColumnMap(
                platform=la1.platform, data_type=(data_type if data_type is not DataType.unknown else la1.data_type),
                mapping=merged, confidence=max(column_map.confidence, la1.confidence),
                method="HA1-classical+LA1",
            )
            if data_type is DataType.unknown:
                data_type = la1.data_type
            parse_conf = max(parse_conf, la1.confidence)
            used_llm_mapping = True

    metrics = metrics_mod.extract_metrics(read, column_map)
    det_enrich = enr.build_enrichment(data_type, metrics)
    pain_flags = dict(enr.suggest_pain_flags(data_type, metrics))
    enrichment = det_enrich
    if allow_llm and ollama_available():
        sig = signal_extractor.extract_signals(data_type, metrics)
        if sig:
            if sig.enrichment:
                enrichment = sig.enrichment
            for flag, conf in sig.pain_flags.items():
                pain_flags[flag] = max(pain_flags.get(flag, 0.0), conf)

    insight = DataInsight(
        analyzable=True,
        format_detected=read.fmt,
        data_type=data_type,
        data_type_confidence=round(parse_conf, 3),
        metrics=metrics,
        bottleneck_enrichment=enrichment,
        pain_flags_suggested={k: round(v, 2) for k, v in pain_flags.items()},
        parse_confidence=round(parse_conf, 3),
        validation_message=(
            f"Detected {data_type.value} — {metrics.total_records} records"
            + (f" over {metrics.date_range_months} months" if metrics.date_range_months else "")
            + ("." if not used_llm_mapping else " (columns mapped with AI assist).")
        ),
        warnings=list(read.warnings),
    )
    insight.data_readiness_contribution = _data_readiness(insight)
    return insight

def _analyse_image(read: ReadResult, content: bytes, allow_llm: bool) -> DataInsight:
    if not allow_llm or not vision_analyser.model_supports_vision():
        vr = vision_analyser.analyse_image([])
        return DataInsight(
            analyzable=False, format_detected=read.fmt,
            validation_message=vr.message or "Image analysis needs a vision-capable model.",
            parse_confidence=0.0,
            warnings=["Vision model not available — export the underlying data as CSV/XLSX."],
        )
    from pypdf import PdfReader
    vr = vision_analyser.analyse_image([content])
    found = {str(item["label"]): item["value"] for item in vr.metrics_found}
    return DataInsight(
        analyzable=bool(found), format_detected=read.fmt,
        data_type=DataType.analytics, data_type_confidence=0.5 if found else 0.0,
        validation_message=(f"Read {len(found)} metrics from the image."
                            if found else (vr.message or "No metrics read from the image.")),
        parse_confidence=0.5 if found else 0.0,
    )

def _analyse_text(read: ReadResult, allow_llm: bool) -> DataInsight:
    return DataInsight(
        analyzable=True, format_detected=read.fmt,
        data_type=DataType.analytics, data_type_confidence=0.3,
        bottleneck_enrichment="",
        validation_message="Extracted a text layer; detailed analysis is limited without an LLM.",
        parse_confidence=0.3,
        warnings=list(read.warnings),
    )

def _data_readiness(insight: DataInsight) -> float | None:
    if not insight.analyzable or insight.parse_confidence < 0.3:
        return None
    m = insight.metrics
    coverage = min((m.date_range_months or 0) / 12.0, 1.0)
    volume = min((m.total_records or 0) / 500.0, 1.0)
    return round(coverage * 0.5 + volume * 0.3 + insight.parse_confidence * 0.2, 2)
