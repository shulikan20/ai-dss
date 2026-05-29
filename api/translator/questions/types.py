from __future__ import annotations

from typing import TypedDict

class AnswerOption(TypedDict):
    value: str
    label: str
    pain_flags: list[str]

class ProfileFieldOption(TypedDict):
    value: str
    label: str
    profile_value: int | str | list[str]

class Question(TypedDict, total=False):
    id: str
    tier: list[str]
    text: str
    help_text: str
    type: str
    options: list
    maps_to: str

class Domain(TypedDict):
    id: str
    label: str
    description: str
