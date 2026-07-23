from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "crm_proposals",
    "tier": ["quick", "standard", "full"],
    "text": "How do you create client proposals and contracts?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automated — generated from templates with client data",
            "pain_flags": [],
        },
        {
            "value": "templates",
            "label": "We use templates, adapted manually for each client",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
            ],
        },
        {
            "value": "from_scratch",
            "label": "Written from scratch for every client",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
                PainFlags.SLOW_FOLLOWUP,
            ],
        },
    ],
},
{
    "id": "crm_followup",
    "tier": ["quick", "standard", "full"],
    "text": "How do you follow up with leads and prospects?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automated sequences (CRM, email automation)",
            "pain_flags": [],
        },
        {
            "value": "semi_manual",
            "label": "Partly manual — reminders help, but not fully automated",
            "pain_flags": [
                PainFlags.SLOW_FOLLOWUP,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — follow-ups depend on memory",
            "pain_flags": [
                PainFlags.SLOW_FOLLOWUP,
            ],
        },
    ],
},
{
    "id": "crm_reporting",
    "tier": ["standard", "full"],
    "text": "How do you track your sales pipeline and performance?",
    "type": "single_select",
    "options": [
        {
            "value": "crm_dashboard",
            "label": "CRM dashboard with automated reporting",
            "pain_flags": [],
        },
        {
            "value": "manual_spreadsheet",
            "label": "Manual spreadsheet updated periodically",
            "pain_flags": [
                PainFlags.UNCLEAR_REPORTING,
                PainFlags.NO_DATA_INSIGHTS,
            ],
        },
        {
            "value": "no_tracking",
            "label": "No structured tracking",
            "pain_flags": [
                PainFlags.UNCLEAR_REPORTING,
                PainFlags.UNPREDICTABLE_REVENUE,
            ],
        },
    ],
},
{
    "id": "crm_customer_value",
    "tier": ["full"],
    "text": "Do you know which customers are worth most over time?",
    "help_text": "Not just the largest single order, but repeat value.",
    "type": "single_select",
    "options": [
        {
            "value": "tracked",
            "label": "Yes, we track it",
            "pain_flags": [],
        },
        {
            "value": "roughly",
            "label": "Roughly, from memory",
            "pain_flags": [
                PainFlags.NO_CLV_INSIGHT,
            ],
        },
        {
            "value": "no",
            "label": "No, we treat every customer the same",
            "pain_flags": [
                PainFlags.NO_CLV_INSIGHT,
            ],
        },
    ],
},
{
    "id": "crm_lead_source",
    "tier": ["full"],
    "text": "Where do new leads come from?",
    "type": "single_select",
    "options": [
        {
            "value": "outbound_running",
            "label": "We run outbound prospecting already",
            "pain_flags": [],
        },
        {
            "value": "inbound_only",
            "label": "Inbound and referrals only",
            "pain_flags": [
                PainFlags.NO_OUTBOUND_LEADGEN,
            ],
        },
        {
            "value": "no_process",
            "label": "No steady source of new leads",
            "pain_flags": [
                PainFlags.NO_OUTBOUND_LEADGEN,
            ],
        },
    ],
},
]
