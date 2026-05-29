from __future__ import annotations

from src.catalog.pain_flags import PainFlags
from api.translator.questions.types import Question

QUESTIONS: list[Question] = [
{
    "id": "sc_inventory",
    "tier": ["quick", "standard", "full"],
    "text": "How do you currently track inventory levels?",
    "type": "single_select",
    "options": [
        {
            "value": "dedicated_system",
            "label": "Dedicated inventory system (e.g. Linnworks, TradeGecko)",
            "pain_flags": [],
        },
        {
            "value": "shopify_woocommerce",
            "label": "Shopify / WooCommerce built-in tracking",
            "pain_flags": [
                PainFlags.STOCKOUTS_SUPPLY_CHAIN,
                PainFlags.INVENTORY_TRACKING,
            ],
        },
        {
            "value": "excel_manual",
            "label": "Excel spreadsheet or manual counting",
            "pain_flags": [
                PainFlags.STOCKOUTS_SUPPLY_CHAIN,
                PainFlags.STOCKOUTS_UNIVERSAL,
                PainFlags.INVENTORY_TRACKING,
                PainFlags.OVERSTOCK,
            ],
        },
    ],
},
{
    "id": "sc_stockouts",
    "tier": ["quick", "standard", "full"],
    "text": "How often do you run out of stock unexpectedly?",
    "type": "single_select",
    "options": [
        {
            "value": "rarely",
            "label": "Rarely or never",
            "pain_flags": [],
        },
        {
            "value": "few_per_year",
            "label": "A few times per year",
            "pain_flags": [
                PainFlags.STOCKOUTS_SUPPLY_CHAIN,
                PainFlags.STOCKOUTS_UNIVERSAL,
            ],
        },
        {
            "value": "monthly",
            "label": "Monthly or more often",
            "pain_flags": [
                PainFlags.STOCKOUTS_SUPPLY_CHAIN,
                PainFlags.STOCKOUTS_UNIVERSAL,
                PainFlags.OVERSTOCK,
            ],
        },
    ],
},
{
    "id": "sc_suppliers",
    "tier": ["quick", "standard", "full"],
    "text": "How do you manage communication with suppliers?",
    "help_text": "Ordering, lead time updates, RFQs.",
    "type": "single_select",
    "options": [
        {
            "value": "platform_automated",
            "label": "Via a dedicated procurement platform",
            "pain_flags": [],
        },
        {
            "value": "email_phone",
            "label": "Mostly email and phone — some structure",
            "pain_flags": [
                PainFlags.SUPPLIER_TRACKING,
            ],
        },
        {
            "value": "fully_manual",
            "label": "Fully manual — no standard process",
            "pain_flags": [
                PainFlags.SUPPLIER_TRACKING,
                PainFlags.MANUAL_DATA_ENTRY,
            ],
        },
    ],
},
{
    "id": "sc_demand_forecasting",
    "tier": ["standard", "full"],
    "text": "How do you forecast what to reorder?",
    "type": "single_select",
    "options": [
        {
            "value": "software",
            "label": "Dedicated forecasting software",
            "pain_flags": [],
        },
        {
            "value": "spreadsheet_formula",
            "label": "Spreadsheet formulas or basic rules",
            "pain_flags": [
                PainFlags.STOCKOUTS_UNIVERSAL,
            ],
        },
        {
            "value": "manual_review",
            "label": "Manual review of past sales",
            "pain_flags": [
                PainFlags.STOCKOUTS_UNIVERSAL,
                PainFlags.OVERSTOCK,
            ],
        },
        {
            "value": "gut_feeling",
            "label": "Gut feeling / experience",
            "pain_flags": [
                PainFlags.STOCKOUTS_UNIVERSAL,
                PainFlags.OVERSTOCK,
            ],
        },
    ],
},
]
