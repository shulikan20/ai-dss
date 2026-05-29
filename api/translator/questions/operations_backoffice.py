from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "bo_invoicing",
    "tier": ["quick", "standard", "full"],
    "text": "How are client invoices created and sent?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automated — invoices generated and sent automatically",
            "pain_flags": [],
        },
        {
            "value": "partially_manual",
            "label": "Partially manual — created from templates, sent manually",
            "pain_flags": [
                PainFlags.MANUAL_INVOICING,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — written individually for each client",
            "pain_flags": [
                PainFlags.MANUAL_INVOICING,
                PainFlags.MANUAL_CONTENT,
            ],
        },
    ],
},
{
    "id": "bo_documents",
    "tier": ["quick", "standard", "full"],
    "text": "How are internal documents and reports produced?",
    "help_text": "e.g. weekly reports, post-event summaries, project briefs.",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automated or AI-assisted",
            "pain_flags": [],
        },
        {
            "value": "templates",
            "label": "Templates that are filled in manually",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
            ],
        },
        {
            "value": "from_scratch",
            "label": "Written from scratch each time",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
                PainFlags.MANUAL_INVOICING,
            ],
        },
    ],
},
]
