from __future__ import annotations

class ExportError(Exception):
    """ExportError"""

class ExportValidationError(ExportError):
    """ExportValidationError"""

class ExportParseError(ExportError):
    """ExportParseError"""

class UnsupportedFormatError(ExportError):
    """UnsupportedFormatError"""
