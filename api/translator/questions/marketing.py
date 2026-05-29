from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "mkt_content",
    "tier": ["quick", "standard", "full"],
    "text": "How is marketing content currently created?",
    "help_text": "Social media posts, emails, product descriptions, ad copy.",
    "type": "single_select",
    "options": [
        {
            "value": "use_ai_tools",
            "label": "We already use AI tools for content",
            "pain_flags": [],
        },
        {
            "value": "templates",
            "label": "We use templates and adapt them manually",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — written from scratch each time",
            "pain_flags": [
                PainFlags.MANUAL_CONTENT,
            ],
        },
    ],
},
{
    "id": "mkt_reporting",
    "tier": ["quick", "standard", "full"],
    "text": "How do you track marketing campaign performance?",
    "type": "single_select",
    "options": [
        {
            "value": "automated_dashboard",
            "label": "Automated dashboard — data from all channels in one place",
            "pain_flags": [],
        },
        {
            "value": "manual_weekly",
            "label": "Manual — I pull numbers from each platform every week",
            "pain_flags": [
                PainFlags.NO_DATA_INSIGHTS,
            ],
        },
        {
            "value": "no_tracking",
            "label": "No structured tracking",
            "pain_flags": [
                PainFlags.NO_DATA_INSIGHTS,
                PainFlags.POOR_AD_PERFORMANCE,
            ],
        },
    ],
},
{
    "id": "mkt_paid_ads",
    "tier": ["standard", "full"],
    "text": "Are you running paid advertising?",
    "type": "single_select",
    "options": [
        {
            "value": "no",
            "label": "No paid ads currently",
            "pain_flags": [],
        },
        {
            "value": "yes_automated",
            "label": "Yes — we use automated bidding/optimisation tools",
            "pain_flags": [],
        },
        {
            "value": "yes_manual",
            "label": "Yes — we manage ads manually or in spreadsheets",
            "pain_flags": [
                PainFlags.POOR_AD_PERFORMANCE,
                PainFlags.MANUAL_AD_CREATIVE,
            ],
        },
    ],
},
]
