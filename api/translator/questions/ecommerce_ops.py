from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "ec_order_entry",
    "tier": ["quick", "standard", "full"],
    "text": "How do you process incoming orders?",
    "help_text": "Consider all channels — web store, social media, marketplaces.",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automatically — orders flow into our system without manual work",
            "pain_flags": [],
        },
        {
            "value": "semi_manual",
            "label": "Partly manual — some orders need to be entered or checked by hand",
            "pain_flags": [
                PainFlags.MANUAL_DATA_ENTRY,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — all orders are entered by hand each day",
            "pain_flags": [
                PainFlags.MANUAL_DATA_ENTRY,
                PainFlags.NO_DATA_INSIGHTS,
            ],
        },
    ],
},
{
    "id": "ec_channels",
    "tier": ["quick", "standard", "full"],
    "text": "How many sales channels do you sell through?",
    "help_text": "e.g. your own website, Shopify, Amazon, Instagram, wholesale.",
    "type": "single_select",
    "options": [
        {
            "value": "one",
            "label": "One channel only",
            "pain_flags": [],
        },
        {
            "value": "two_three",
            "label": "2 – 3 channels",
            "pain_flags": [
                PainFlags.MULTICHANNEL,
            ],
        },
        {
            "value": "four_plus",
            "label": "4 or more channels",
            "pain_flags": [
                PainFlags.MULTICHANNEL,
                PainFlags.MANUAL_DATA_ENTRY,
            ],
        },
    ],
},
{
    "id": "ec_returns",
    "tier": ["quick", "standard", "full"],
    "text": "How are customer returns handled?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automated — customers self-serve, labels generated automatically",
            "pain_flags": [],
        },
        {
            "value": "partially_manual",
            "label": "Partially manual — some steps handled by the team",
            "pain_flags": [
                PainFlags.MANUAL_RETURNS,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — every return handled from start to finish by staff",
            "pain_flags": [
                PainFlags.MANUAL_RETURNS,
            ],
        },
    ],
},
{
    "id": "ec_order_volume",
    "tier": ["standard", "full"],
    "text": "What is your approximate monthly order volume?",
    "type": "single_select",
    "options": [
        {
            "value": "under_100",
            "label": "Under 100 orders/month",
            "pain_flags": [],
        },
        {
            "value": "100_500",
            "label": "100 – 500 orders/month",
            "pain_flags": [],
        },
        {
            "value": "500_2000",
            "label": "500 – 2,000 orders/month",
            "pain_flags": [
                PainFlags.MANUAL_DATA_ENTRY,
            ],
        },
        {
            "value": "over_2000",
            "label": "Over 2,000 orders/month",
            "pain_flags": [
                PainFlags.MANUAL_DATA_ENTRY,
                PainFlags.SLOW_ORDER_PROC,
            ],
        },
    ],
},
{
    "id": "ec_product_content",
    "tier": ["full"],
    "text": "How are product descriptions written?",
    "type": "single_select",
    "options": [
        {
            "value": "supplied",
            "label": "Supplied by the manufacturer or generated automatically",
            "pain_flags": [],
        },
        {
            "value": "adapted",
            "label": "Adapted by hand from supplier text",
            "pain_flags": [
                PainFlags.MANUAL_DESCRIPTIONS,
            ],
        },
        {
            "value": "from_scratch",
            "label": "Written from scratch for every product",
            "pain_flags": [
                PainFlags.MANUAL_DESCRIPTIONS,
            ],
        },
    ],
},
{
    "id": "ec_product_discovery",
    "tier": ["full"],
    "text": "Can customers find the right product on your site easily?",
    "help_text": "Search quality, filters, and how often people give up.",
    "type": "single_select",
    "options": [
        {
            "value": "easily",
            "label": "Yes, search and filters work well",
            "pain_flags": [],
        },
        {
            "value": "sometimes",
            "label": "Sometimes, search results are hit and miss",
            "pain_flags": [
                PainFlags.POOR_PRODUCT_DISCOVERY,
            ],
        },
        {
            "value": "often_fail",
            "label": "Often not, customers ask us to find things for them",
            "pain_flags": [
                PainFlags.POOR_PRODUCT_DISCOVERY,
            ],
        },
    ],
},
{
    "id": "ec_pricing",
    "tier": ["full"],
    "text": "How do you set and review prices?",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Automatically, against rules or competitor data",
            "pain_flags": [],
        },
        {
            "value": "periodic_manual",
            "label": "Reviewed by hand every few weeks",
            "pain_flags": [
                PainFlags.COMPETITOR_PRICING,
            ],
        },
        {
            "value": "rarely_reviewed",
            "label": "Set once and rarely revisited, margins are tight",
            "pain_flags": [
                PainFlags.COMPETITOR_PRICING,
                PainFlags.MARGIN_PRESSURE,
            ],
        },
    ],
},
{
    "id": "ec_order_value",
    "tier": ["full"],
    "text": "Do you actively try to increase the value of each order?",
    "help_text": "Cross-sells, bundles, recommended products at checkout.",
    "type": "single_select",
    "options": [
        {
            "value": "automated",
            "label": "Yes, recommendations run automatically",
            "pain_flags": [],
        },
        {
            "value": "occasionally",
            "label": "Occasionally, set up by hand",
            "pain_flags": [
                PainFlags.LOW_AOV,
            ],
        },
        {
            "value": "no",
            "label": "No",
            "pain_flags": [
                PainFlags.LOW_AOV,
            ],
        },
    ],
},
{
    "id": "ec_subscriptions",
    "tier": ["full"],
    "text": "Do you sell subscriptions or repeat orders?",
    "type": "single_select",
    "options": [
        {
            "value": "none",
            "label": "No, one-off purchases only",
            "pain_flags": [],
        },
        {
            "value": "yes_automated",
            "label": "Yes, renewals and billing run automatically",
            "pain_flags": [],
        },
        {
            "value": "yes_manual",
            "label": "Yes, but renewals and changes are handled by hand",
            "pain_flags": [
                PainFlags.MANUAL_SUBSCRIPTIONS,
            ],
        },
    ],
},
]
