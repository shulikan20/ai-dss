from __future__ import annotations

from .format_reader import detect_format, read
from .models import FileFormat, ReadKind, ValidationResult

_MIN_ROWS = 2
_UNSUPPORTED_HINT = (
    "This file format is not supported yet. Export your data as CSV, XLSX or JSON and try again."
)

def validate(filename: str, content: bytes) -> ValidationResult:
    fmt = detect_format(filename, content)

    if content is None or len(content) == 0:
        return ValidationResult(
            can_analyze=False, format_detected=fmt,
            reason="This file appears to be empty.",
            suggested_action="Upload a file that contains your exported data.",
        )

    if fmt is FileFormat.unknown:
        return ValidationResult(
            can_analyze=False, format_detected=fmt,
            reason="This file format is not recognised.",
            suggested_action=_UNSUPPORTED_HINT,
        )

    result = read(filename, content)

    if result.error is not None or result.kind is ReadKind.none:
        return ValidationResult(
            can_analyze=False, format_detected=result.fmt,
            reason=result.error or "This file could not be read.",
            suggested_action=_UNSUPPORTED_HINT,
        )

    if result.kind is ReadKind.tabular:
        if not result.columns:
            return ValidationResult(
                can_analyze=False, format_detected=result.fmt,
                reason="No columns were found in this file.",
                suggested_action="Make sure the export includes a header row.",
            )
        if result.n_rows < _MIN_ROWS:
            return ValidationResult(
                can_analyze=False, format_detected=result.fmt,
                reason=(
                    f"This file contains fewer than {_MIN_ROWS} data rows — not "
                    "enough to extract meaningful signals."
                ),
                suggested_action="Export a fuller history (ideally several months of data).",
            )
        return ValidationResult(
            can_analyze=True, format_detected=result.fmt,
            reason=f"Found {result.n_rows} rows across {len(result.columns)} columns.",
        )

    if result.kind is ReadKind.text:
        return ValidationResult(
            can_analyze=True, format_detected=result.fmt,
            reason="Found an extractable text layer to analyse.",
        )

    if result.kind is ReadKind.image:
        pages = result.image_page_count or 1
        what = "scanned PDF" if result.fmt is FileFormat.pdf_image else "image"
        return ValidationResult(
            can_analyze=True, format_detected=result.fmt,
            reason=f"Detected a {what} ({pages} page(s)); will read it with a vision model.",
            suggested_action=(
                "If analysis does not work, export the underlying data as CSV or "
                "XLSX for the most reliable result."
            ),
        )

    return ValidationResult(
        can_analyze=False, format_detected=result.fmt,
        reason="This file does not appear to contain analysable business data.",
        suggested_action=_UNSUPPORTED_HINT,
    )
