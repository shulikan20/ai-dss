from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "cs_message_volume",
    "tier": ["quick", "standard", "full"],
    "text": "How many customer messages do you receive per week?",
    "help_text": "Include DMs, emails, and chat messages from customers.",
    "type": "single_select",
    "options": [
        {
            "value": "low",
            "label": "Under 50",
            "pain_flags": [],
        },
        {
            "value": "medium",
            "label": "50 – 200",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
            ],
        },
        {
            "value": "high",
            "label": "Over 200",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
                PainFlags.REPETITIVE_SUPPORT,
            ],
        },
    ],
},
{
    "id": "cs_repetitive",
    "tier": ["quick", "standard", "full"],
    "text": "Do customers ask the same questions repeatedly?",
    "help_text": "e.g. 'What's your return policy?', 'Where's my order?'",
    "type": "single_select",
    "options": [
        {
            "value": "rarely",
            "label": "Rarely — questions are usually unique",
            "pain_flags": [],
        },
        {
            "value": "sometimes",
            "label": "Sometimes",
            "pain_flags": [
                PainFlags.REPETITIVE_SUPPORT,
            ],
        },
        {
            "value": "constantly",
            "label": "Constantly — the same 5-10 questions over and over",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
                PainFlags.REPETITIVE_SUPPORT,
            ],
        },
    ],
},
{
    "id": "cs_response_time",
    "tier": ["quick", "standard", "full"],
    "text": "How quickly do you typically respond to customers?",
    "type": "single_select",
    "options": [
        {
            "value": "same_day",
            "label": "Same day",
            "pain_flags": [],
        },
        {
            "value": "one_two_days",
            "label": "1 – 2 days",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
                PainFlags.SLOW_RESPONSE,
            ],
        },
        {
            "value": "longer",
            "label": "Longer than 2 days",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
                PainFlags.REPETITIVE_SUPPORT,
                PainFlags.SLOW_RESPONSE,
            ],
        },
    ],
},
{
    "id": "cs_channels",
    "tier": ["standard", "full"],
    "text": "What channels do customers use to contact you?",
    "help_text": "Select the primary ones. Affects integration recommendations.",
    "type": "single_select",
    "options": [
        {
            "value": "one_channel",
            "label": "Mainly one channel (e.g. only email)",
            "pain_flags": [],
        },
        {
            "value": "two_three",
            "label": "2–3 channels (e.g. email + Instagram DM + chat)",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
            ],
        },
        {
            "value": "many",
            "label": "4+ channels — hard to keep track",
            "pain_flags": [
                PainFlags.HIGH_VOLUME_SUPPORT,
                PainFlags.TICKET_OVERLOAD,
            ],
        },
    ],
},
{
    "id": "cs_repetition_rate",
    "tier": ["standard", "full"],
    "text": "What percentage of messages are questions you've answered before?",
    "type": "single_select",
    "options": [
        {
            "value": "under_25",
            "label": "Under 25% — most are unique",
            "pain_flags": [],
        },
        {
            "value": "25_50",
            "label": "25–50%",
            "pain_flags": [
                PainFlags.REPETITIVE_SUPPORT,
            ],
        },
        {
            "value": "over_50",
            "label": "Over 50% — majority are repeat questions",
            "pain_flags": [
                PainFlags.REPETITIVE_SUPPORT,
                PainFlags.HIGH_VOLUME_SUPPORT,
            ],
        },
    ],
},
{
    "id": "cs_languages",
    "tier": ["full"],
    "text": "Do customers contact you in more than one language?",
    "help_text": "Counts any language your team has to reply in.",
    "type": "single_select",
    "options": [
        {
            "value": "one_language",
            "label": "One language only",
            "pain_flags": [],
        },
        {
            "value": "two_three",
            "label": "Two or three languages",
            "pain_flags": [
                PainFlags.MULTILINGUAL_SUPPORT,
            ],
        },
        {
            "value": "many",
            "label": "More languages than the team speaks",
            "pain_flags": [
                PainFlags.MULTILINGUAL_SUPPORT,
            ],
        },
    ],
},
{
    "id": "cs_reviews",
    "tier": ["full"],
    "text": "How do you handle public reviews and ratings?",
    "help_text": "Google, Trustpilot, marketplace reviews, app store ratings.",
    "type": "single_select",
    "options": [
        {
            "value": "monitored",
            "label": "Monitored and answered consistently",
            "pain_flags": [],
        },
        {
            "value": "occasionally",
            "label": "Answered occasionally, when someone notices",
            "pain_flags": [
                PainFlags.NEGATIVE_REVIEWS,
            ],
        },
        {
            "value": "not_tracked",
            "label": "Not tracked at all",
            "pain_flags": [
                PainFlags.NEGATIVE_REVIEWS,
                PainFlags.BRAND_REPUTATION,
            ],
        },
    ],
},
]
