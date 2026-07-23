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
{
    "id": "bo_cashflow",
    "tier": ["full"],
    "text": "Do you have a forward view of cash?",
    "help_text": "Knowing what is coming in and going out over the next months.",
    "type": "single_select",
    "options": [
        {
            "value": "forecasted",
            "label": "Yes, we forecast it",
            "pain_flags": [],
        },
        {
            "value": "bank_balance",
            "label": "We go by the current bank balance",
            "pain_flags": [
                PainFlags.CASHFLOW_VISIBILITY,
            ],
        },
        {
            "value": "no_view",
            "label": "No, it is a recurring surprise",
            "pain_flags": [
                PainFlags.CASHFLOW_VISIBILITY,
            ],
        },
    ],
},
{
    "id": "bo_expenses",
    "tier": ["full"],
    "text": "How are expenses and receipts handled?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Captured automatically and synced to accounting",
            "pain_flags": [],
        },
        {
            "value": "partly_manual",
            "label": "Photographed and entered by hand",
            "pain_flags": [
                PainFlags.MANUAL_EXPENSES,
            ],
        },
        {
            "value": "shoebox",
            "label": "Collected and sorted at the end of the period",
            "pain_flags": [
                PainFlags.MANUAL_EXPENSES,
            ],
        },
    ],
},
{
    "id": "bo_onboarding",
    "tier": ["full"],
    "text": "How do you onboard new staff?",
    "type": "single_select",
    "options": [
        {
            "value": "structured",
            "label": "A structured process that runs itself",
            "pain_flags": [],
        },
        {
            "value": "checklist",
            "label": "A checklist someone works through by hand",
            "pain_flags": [
                PainFlags.MANUAL_ONBOARDING,
            ],
        },
        {
            "value": "ad_hoc",
            "label": "Different every time, depending on who is free",
            "pain_flags": [
                PainFlags.MANUAL_ONBOARDING,
            ],
        },
    ],
},
{
    "id": "bo_knowledge",
    "tier": ["full"],
    "text": "Can the team find internal information quickly?",
    "help_text": "Policies, how-tos, past decisions, product details.",
    "type": "single_select",
    "options": [
        {
            "value": "searchable",
            "label": "Yes, it is documented and searchable",
            "pain_flags": [],
        },
        {
            "value": "scattered",
            "label": "It exists, but is spread across tools and drives",
            "pain_flags": [
                PainFlags.SCATTERED_KNOWLEDGE,
            ],
        },
        {
            "value": "in_heads",
            "label": "Mostly in people's heads, you have to ask someone",
            "pain_flags": [
                PainFlags.SCATTERED_KNOWLEDGE,
            ],
        },
    ],
},
{
    "id": "bo_contracts",
    "tier": ["full"],
    "text": "How are contracts and agreements reviewed?",
    "type": "single_select",
    "options": [
        {
            "value": "not_applicable",
            "label": "We handle very few contracts",
            "pain_flags": [],
        },
        {
            "value": "read_manually",
            "label": "Read line by line by whoever is available",
            "pain_flags": [
                PainFlags.MANUAL_CONTRACT_REVIEW,
            ],
        },
        {
            "value": "external_cost",
            "label": "Sent to a lawyer, which is slow and costly",
            "pain_flags": [
                PainFlags.MANUAL_CONTRACT_REVIEW,
            ],
        },
    ],
},
{
    "id": "bo_scheduling",
    "tier": ["full"],
    "text": "How much time goes on arranging meetings and appointments?",
    "type": "single_select",
    "options": [
        {
            "value": "self_service",
            "label": "Little, people book themselves into a calendar",
            "pain_flags": [],
        },
        {
            "value": "some_back_and_forth",
            "label": "Some, there is email back and forth",
            "pain_flags": [
                PainFlags.SCHEDULING_OVERHEAD,
            ],
        },
        {
            "value": "significant",
            "label": "A lot, someone coordinates it daily",
            "pain_flags": [
                PainFlags.SCHEDULING_OVERHEAD,
            ],
        },
    ],
},
]
