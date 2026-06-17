from __future__ import annotations
from dataclasses import dataclass, field

from .column_aliases import _NORM_LOOKUP, all_standard_fields, lookup_exact, normalise

@dataclass
class Fingerprint:
    mapping: dict[str, str] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)

    @property
    def fields_present(self) -> set[str]:
        return set(self.mapping)

def fingerprint(columns: list[str]) -> Fingerprint:
    fp = Fingerprint()
    for col in columns:
        field_name = lookup_exact(col)
        if field_name is None:
            field_name = _token_match(col)
        if field_name and field_name not in fp.mapping:
            fp.mapping[field_name] = col
        elif field_name is None:
            fp.unmatched.append(col)
    return fp


def _token_match(header: str) -> str | None:
    h_tokens = set(normalise(header).split())
    if not h_tokens:
        return None
    best_field, best_len = None, 0
    for norm_alias, std_field in _NORM_LOOKUP.items():
        a_tokens = norm_alias.split()
        if len(norm_alias) < 3:
            continue
        if a_tokens and set(a_tokens).issubset(h_tokens):
            if len(norm_alias) > best_len:
                best_field, best_len = std_field, len(norm_alias)
    return best_field
