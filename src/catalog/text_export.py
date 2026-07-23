from __future__ import annotations

from collections import defaultdict

from sqlalchemy import text

CAP_SQL = text(
    """
    SELECT capability_id, name, domain, use_case_category, task_type_target,
           description, bottleneck_keywords, works_without_data,
           required_data_types, min_history_months_gate,
           min_technical_capability, mapped_pain_points, primary_outcome,
           secondary_outcomes, time_to_value_weeks_min, time_to_value_weeks_max
    FROM capabilities
    ORDER BY domain, capability_id
    """
)

PROD_SQL = text(
    """
    SELECT product_id, capability_id, name, vendor, url, cost_tier,
           has_free_tier, gdpr_compliant, implementation_effort, cost_notes,
           min_technical_capability, works_with_limited_data, min_history_months
    FROM products
    ORDER BY capability_id, name
    """
)

TECH_LEVELS = {
    1: "1 (non-technical)",
    2: "2 (comfortable with SaaS)",
    3: "3 (has technical staff)",
    4: "4 (engineering team)",
    5: "5 (specialist/data team)",
}


def _fmt_list(value) -> str:
    if not value:
        return "-"
    if isinstance(value, str):
        return f"`{value}`"
    return ", ".join(f"`{v}`" for v in value)


def _one_line(description: str | None, limit: int = 160) -> str:
    if not description:
        return ""
    text_ = " ".join(description.split())
    first = text_.split(". ")[0].rstrip(".")
    if len(first) > limit:
        first = first[: limit - 1].rsplit(" ", 1)[0] + "..."
    return first


def fetch(session) -> tuple[list[dict], dict[str, list[dict]]]:
    caps = [dict(r) for r in session.execute(CAP_SQL).mappings()]
    prods_by_cap: dict[str, list[dict]] = defaultdict(list)
    for row in session.execute(PROD_SQL).mappings():
        prods_by_cap[row["capability_id"]].append(dict(row))
    return caps, prods_by_cap


def render_full(caps: list[dict], prods: dict[str, list[dict]]) -> str:
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for c in caps:
        by_domain[c["domain"]].append(c)

    n_prod = sum(len(v) for v in prods.values())
    out: list[str] = [
        "# AI-Tools Capability Catalogue",
        "",
        f"{len(caps)} capabilities, {n_prod} products, {len(by_domain)} domains",
        "",
        "Generated from the live PostgreSQL catalogue.",
        "",
        "",
        "---",
        "",
    ]

    for domain in sorted(by_domain):
        domain_caps = by_domain[domain]
        out.append(f"## {domain} ({len(domain_caps)} capabilities)")
        out.append("")
        for c in domain_caps:
            out.append(f"### {c['name']}")
            out.append("")
            out.append(f"`{c['capability_id']}`")
            out.append("")
            if c["description"]:
                out.append(" ".join(c["description"].split()))
                out.append("")

            out.append(f"- Bottleneck keywords: {_fmt_list(c['bottleneck_keywords'])}")
            out.append(f"- Mapped pain flags: {_fmt_list(c['mapped_pain_points'])}")
            out.append(f"- Primary outcome: {c['primary_outcome'] or '-'}")
            if c["secondary_outcomes"]:
                out.append(f"- Secondary outcomes: {_fmt_list(c['secondary_outcomes'])}")

            out.append(
                f"- Hard gate, minimum technical capability: "
                f"{TECH_LEVELS.get(c['min_technical_capability'], c['min_technical_capability'])}"
            )
            out.append("- Data-readiness inputs (scored, not gated):")
            out.append(
                f"    - works without data: "
                f"{'yes' if c['works_without_data'] else 'no'}"
            )
            out.append(f"    - required data types: {_fmt_list(c['required_data_types'])}")
            out.append(f"    - minimum history: {c['min_history_months_gate']} months")

            ttv_min, ttv_max = c["time_to_value_weeks_min"], c["time_to_value_weeks_max"]
            if ttv_min is not None or ttv_max is not None:
                out.append(f"- Time to value: {ttv_min}-{ttv_max} weeks")

            cap_prods = prods.get(c["capability_id"], [])
            out.append(f"- Products ({len(cap_prods)}):")
            if not cap_prods:
                out.append("    - none mapped")
            for p in cap_prods:
                bits = []
                if p["vendor"]:
                    bits.append(p["vendor"])
                if p["cost_tier"]:
                    bits.append(f"{p['cost_tier']} cost")
                if p["has_free_tier"]:
                    bits.append("free tier")
                if p["gdpr_compliant"]:
                    bits.append("GDPR")
                if p["implementation_effort"]:
                    bits.append(f"{p['implementation_effort']} effort")
                suffix = f" - {'; '.join(bits)}" if bits else ""
                link = f"[{p['name']}]({p['url']})" if p["url"] else p["name"]
                out.append(f"    - {link}{suffix}")
            out.append("")
        out.append("---")
        out.append("")

    return "\n".join(out)


def render_compact(caps: list[dict]) -> str:
    by_domain: dict[str, list[dict]] = defaultdict(list)
    for c in caps:
        by_domain[c["domain"]].append(c)

    out = [
        f"AI-DSS CAPABILITY CATALOGUE - {len(caps)} capabilities across "
        f"{len(by_domain)} domains",
        "Format: capability_id | name | what it does",
        "",
    ]
    for domain in sorted(by_domain):
        out.append(f"== {domain} ==")
        for c in by_domain[domain]:
            out.append(
                f"{c['capability_id']} | {c['name']} | {_one_line(c['description'])}"
            )
        out.append("")
    return "\n".join(out)
