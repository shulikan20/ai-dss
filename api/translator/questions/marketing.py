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
{
    "id": "mkt_email_quality",
    "tier": ["full"],
    "text": "How does your email marketing perform?",
    "type": "single_select",
    "options": [
        {
            "value": "good",
            "label": "Segmented, and open rates are healthy",
            "pain_flags": [],
        },
        {
            "value": "low_engagement",
            "label": "Segmented, but few people open or click",
            "pain_flags": [
                PainFlags.LOW_EMAIL_ENGAGEMENT,
            ],
        },
        {
            "value": "same_to_everyone",
            "label": "The same message goes to the whole list",
            "pain_flags": [
                PainFlags.LOW_EMAIL_ENGAGEMENT,
                PainFlags.GENERIC_CAMPAIGNS,
            ],
        },
    ],
},
{
    "id": "mkt_organic",
    "tier": ["full"],
    "text": "How much traffic comes from search and content?",
    "type": "single_select",
    "options": [
        {
            "value": "strong",
            "label": "A steady share, we publish regularly",
            "pain_flags": [],
        },
        {
            "value": "some",
            "label": "Some, but it is not growing",
            "pain_flags": [
                PainFlags.LOW_ORGANIC_TRAFFIC,
            ],
        },
        {
            "value": "none",
            "label": "Very little, and we have no content plan",
            "pain_flags": [
                PainFlags.LOW_ORGANIC_TRAFFIC,
                PainFlags.NO_CONTENT_STRATEGY,
            ],
        },
    ],
},
{
    "id": "mkt_video",
    "tier": ["full"],
    "text": "Do you produce video content?",
    "help_text": "Short-form video for social, product video, ads.",
    "type": "single_select",
    "options": [
        {
            "value": "regularly",
            "label": "Regularly",
            "pain_flags": [],
        },
        {
            "value": "occasionally",
            "label": "Occasionally, it takes too long to make",
            "pain_flags": [
                PainFlags.NO_VIDEO_CONTENT,
            ],
        },
        {
            "value": "never",
            "label": "Never, we do not have the skills or time",
            "pain_flags": [
                PainFlags.NO_VIDEO_CONTENT,
            ],
        },
    ],
},
{
    "id": "mkt_sms",
    "tier": ["full"],
    "text": "Do you reach customers by SMS or messaging apps?",
    "type": "single_select",
    "options": [
        {
            "value": "yes",
            "label": "Yes, as a regular channel",
            "pain_flags": [],
        },
        {
            "value": "no_but_relevant",
            "label": "No, but our customers would respond to it",
            "pain_flags": [
                PainFlags.NO_SMS_CHANNEL,
            ],
        },
        {
            "value": "no",
            "label": "No",
            "pain_flags": [
                PainFlags.NO_SMS_CHANNEL,
            ],
        },
    ],
},
{
    "id": "mkt_spend_return",
    "tier": ["full"],
    "text": "Do you know which marketing spend pays for itself?",
    "type": "single_select",
    "options": [
        {
            "value": "measured",
            "label": "Yes, return is measured per channel",
            "pain_flags": [],
        },
        {
            "value": "partly",
            "label": "For some channels only",
            "pain_flags": [
                PainFlags.LOW_MARKETING_ROI,
            ],
        },
        {
            "value": "unknown",
            "label": "No, we cannot tell what the spend returns",
            "pain_flags": [
                PainFlags.LOW_MARKETING_ROI,
            ],
        },
    ],
},
{
    "id": "mkt_retention",
    "tier": ["full"],
    "text": "Do customers buy from you again after the first purchase?",
    "type": "single_select",
    "options": [
        {
            "value": "most_return",
            "label": "Most come back",
            "pain_flags": [],
        },
        {
            "value": "some_return",
            "label": "Some do, but we do nothing to encourage it",
            "pain_flags": [
                PainFlags.LOW_REPEAT_PURCHASES,
            ],
        },
        {
            "value": "rarely_return",
            "label": "Rarely, most buy once and disappear",
            "pain_flags": [
                PainFlags.LOW_REPEAT_PURCHASES,
                PainFlags.CUSTOMER_CHURN,
            ],
        },
    ],
},
]
