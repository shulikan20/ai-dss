from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path

from .models import FileFormat, ReadKind, ReadResult

_MAX_SAMPLE = 5000
_PDF_TEXT_MIN_CHARS = 40
_EXT_FORMAT = {
    ".csv": FileFormat.csv,
    ".tsv": FileFormat.tsv,
    ".xlsx": FileFormat.xlsx,
    ".xlsm": FileFormat.xlsx,
    ".xls": FileFormat.xls,
    ".json": FileFormat.json,
    ".jsonl": FileFormat.jsonl,
    ".ndjson": FileFormat.jsonl,
    ".pdf": FileFormat.pdf_text,
    ".png": FileFormat.image,
    ".jpg": FileFormat.image,
    ".jpeg": FileFormat.image,
    ".webp": FileFormat.image,
    ".gif": FileFormat.image,
    ".bmp": FileFormat.image,
}
_CEE_HINTS = {"pl", "cs", "cz", "sk", "hu", "hr", "sl", "ro", "sr"}


def detect_format(filename: str, content: bytes | None = None) -> FileFormat:
    ext = Path(filename or "").suffix.lower()
    if ext in _EXT_FORMAT:
        return _EXT_FORMAT[ext]
    if content:
        head = content[:16]
        if head[:4] == b"%PDF":
            return FileFormat.pdf_text
        if head[:2] in (b"\xff\xd8",) or head[:8].startswith(b"\x89PNG"):
            return FileFormat.image
        stripped = content.lstrip()[:1]
        if stripped in (b"{", b"["):
            return FileFormat.json
    return FileFormat.unknown


def read(filename: str, content: bytes, *, language_hint: str | None = None) -> ReadResult:
    fmt = detect_format(filename, content)
    try:
        if content is None or len(content) == 0:
            return ReadResult(fmt=fmt, kind=ReadKind.none, error="The file is empty.")
        if fmt in (FileFormat.csv, FileFormat.tsv):
            return _read_delimited(content, fmt, language_hint)
        if fmt in (FileFormat.xlsx, FileFormat.xls):
            return _read_excel(content, fmt)
        if fmt is FileFormat.json:
            return _read_json(content, language_hint)
        if fmt is FileFormat.jsonl:
            return _read_jsonl(content, language_hint)
        if fmt in (FileFormat.pdf_text, FileFormat.pdf_image):
            return _read_pdf(content)
        if fmt is FileFormat.image:
            return ReadResult(
                fmt=FileFormat.image, kind=ReadKind.image, image_page_count=1,
                warnings=["Image content — analysis requires a vision-capable model."],
            )
        return ReadResult(
            fmt=FileFormat.unknown, kind=ReadKind.none,
            error="Unsupported or unrecognised file format.",
        )
    except Exception as exc:  # noqa
        return ReadResult(fmt=fmt, kind=ReadKind.none, error=f"Could not read file: {exc}")

def _decode(content: bytes, language_hint: str | None = None) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return content.decode(enc), enc
        except UnicodeDecodeError:
            continue
    legacy = "cp1250" if (language_hint and language_hint.strip().lower()[:2] in _CEE_HINTS) else "cp1252"
    try:
        return content.decode(legacy), legacy
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes

        best = from_bytes(content).best()
        if best is not None:
            return str(best), best.encoding or "latin-1"
    except Exception:  # noqa
        pass
    return content.decode("latin-1", errors="replace"), "latin-1"

def _records_from_frame(df, fmt: FileFormat, warnings: list[str]) -> ReadResult:
    import pandas as pd

    df = df.dropna(axis=1, how="all")
    columns = [str(c) for c in df.columns]
    n_rows = int(len(df))

    if n_rows > _MAX_SAMPLE:
        step = math.ceil(n_rows / _MAX_SAMPLE)
        sample = df.iloc[::step]
        if len(sample) and sample.index[-1] != df.index[-1]:
            sample = pd.concat([sample, df.iloc[[-1]]])
        warnings.append(
            f"Large file: metrics computed from a representative {len(sample)}-row "
            f"sample evenly spanning all {n_rows} rows (not the first {len(sample)})."
        )
    else:
        sample = df

    records = [
        {str(k): (None if (isinstance(v, float) and math.isnan(v)) else v)
         for k, v in row.items()}
        for row in sample.replace({pd.NA: None}).to_dict(orient="records")
    ]
    return ReadResult(
        fmt=fmt, kind=ReadKind.tabular, columns=columns,
        records=records, n_rows=n_rows, warnings=warnings,
    )

def _read_delimited(content: bytes, fmt: FileFormat, language_hint: str | None = None) -> ReadResult:
    import pandas as pd

    text, enc = _decode(content, language_hint)
    warnings = [] if enc.startswith("utf-8") else [f"Decoded as {enc}."]
    default = "\t" if fmt is FileFormat.tsv else ","
    sep = default
    try:
        sniff = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        sep = sniff.delimiter
    except Exception:  # noqa
        warnings.append("Could not sniff delimiter; used default.")
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=True,
                     na_values=["", "null", "NULL", "None"], engine="python")
    if df.shape[1] == 1 and sep != ";":
        try:
            alt = pd.read_csv(io.StringIO(text), sep=";", dtype=str, engine="python")
            if alt.shape[1] > df.shape[1]:
                df, sep = alt, ";"
        except Exception:  # noqa
            pass
    return _records_from_frame(df, fmt, warnings)

def _read_excel(content: bytes, fmt: FileFormat) -> ReadResult:
    import pandas as pd

    engine = "openpyxl" if fmt is FileFormat.xlsx else None
    xls = pd.ExcelFile(io.BytesIO(content), engine=engine)
    warnings: list[str] = []
    first = xls.parse(xls.sheet_names[0], dtype=str)

    if len(xls.sheet_names) == 1:
        return _records_from_frame(first, fmt, warnings)
    base_cols = list(first.columns)
    frames = [first]
    skipped = []
    for name in xls.sheet_names[1:]:
        df = xls.parse(name, dtype=str)
        if list(df.columns) == base_cols:
            frames.append(df)
        else:
            skipped.append(name)
    if len(frames) > 1:
        combined = pd.concat(frames, ignore_index=True)
        warnings.append(
            f"Combined {len(frames)} same-schema sheets into one dataset "
            f"({len(combined)} rows)."
        )
    else:
        combined = first
        warnings.append(
            f"Workbook has {len(xls.sheet_names)} sheets with differing schemas; "
            f"read the first ('{xls.sheet_names[0]}')."
        )
    if skipped:
        warnings.append(f"Skipped sheet(s) with a different schema: {', '.join(skipped)}.")
    return _records_from_frame(combined, fmt, warnings)

def _find_records_list(obj):
    if isinstance(obj, list):
        return obj if (obj and isinstance(obj[0], dict)) else None
    if isinstance(obj, dict):
        best = None
        for key in ("orders", "data", "records", "results", "items", "rows", "leads", "tickets"):
            v = obj.get(key)
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        for v in obj.values():
            cand = _find_records_list(v)
            if cand and (best is None or len(cand) > len(best)):
                best = cand
        return best
    return None

def _read_json(content: bytes, language_hint: str | None = None) -> ReadResult:
    import pandas as pd

    text, _ = _decode(content, language_hint)
    data = json.loads(text)
    records = _find_records_list(data)
    if records is None:
        if isinstance(data, dict) and data:
            df = pd.json_normalize(data)
            return _records_from_frame(df, FileFormat.json,
                                       ["JSON is a single object — treated as one summary record."])
        return ReadResult(fmt=FileFormat.json, kind=ReadKind.none,
                          error="JSON contains no list of records to analyse.")
    df = pd.json_normalize(records)
    return _records_from_frame(df, FileFormat.json, [])

def _read_jsonl(content: bytes, language_hint: str | None = None) -> ReadResult:
    import pandas as pd

    text, _ = _decode(content, language_hint)
    rows = []
    bad = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except json.JSONDecodeError:
            bad += 1
    if not rows:
        return ReadResult(fmt=FileFormat.jsonl, kind=ReadKind.none,
                          error="No valid JSON object lines found.")
    warnings = [f"Skipped {bad} malformed line(s)."] if bad else []
    df = pd.json_normalize(rows)
    return _records_from_frame(df, FileFormat.jsonl, warnings)


def _read_pdf(content: bytes) -> ReadResult:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = len(reader.pages)
    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:  # noqa
            continue
    text = "\n".join(text_parts).strip()
    if len(text) >= _PDF_TEXT_MIN_CHARS:
        return ReadResult(fmt=FileFormat.pdf_text, kind=ReadKind.text,
                          text=text, image_page_count=pages)
    return ReadResult(
        fmt=FileFormat.pdf_image, kind=ReadKind.image, image_page_count=pages,
        warnings=["PDF has no extractable text layer likely screenshots needs a vision-capable model"],
    )
