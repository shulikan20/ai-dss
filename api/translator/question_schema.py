from __future__ import annotations

from typing import TypedDict

from src.catalog.pain_flags import PainFlags

class AnswerOption(TypedDict):
    value: str
    label: str
    pain_flags: list[str]

class ProfileFieldOption(TypedDict):
    """Used for questions that map to a profile field, not pain flags."""
    value: str
    label: str
    profile_value: int | str | list[str]

class Question(TypedDict, total=False):
    id: str
    tier: list[str]
    text: str
    help_text: str
    type: str
    options: list
    maps_to: str

class Domain(TypedDict):
    id: str
    label: str
    description: str

CATALOG_PATHS_TO_VERIFY = {
    PainFlags.HIGH_VOLUME_SUPPORT,
    PainFlags.REPETITIVE_SUPPORT,
    PainFlags.MANUAL_RETURNS,
    PainFlags.MANUAL_DATA_ENTRY,
    PainFlags.NO_DATA_INSIGHTS,
    PainFlags.MANUAL_CONTENT,
    PainFlags.STOCKOUTS_SUPPLY_CHAIN,
    PainFlags.MANUAL_INVOICING,
    PainFlags.SLOW_FOLLOWUP,
    PainFlags.UNCLEAR_REPORTING,
    PainFlags.POOR_AD_PERFORMANCE,
    PainFlags.SUPPLIER_TRACKING,
    PainFlags.INVENTORY_TRACKING,
    PainFlags.STOCKOUTS_UNIVERSAL,
    PainFlags.OVERSTOCK,
    # supply_chain.procurement.pain_supplier_delays ! not in catalog !
}

_DOMAINS: list[Domain] = [
    {
        "id": "ecommerce_ops",
        "label": "E-commerce & Order Management",
        "description": "Online store operations, order processing, fulfilment, returns",
    },
    {
        "id": "customer_support",
        "label": "Customer Support",
        "description": "Handling customer messages, DMs, emails, and support tickets",
    },
    {
        "id": "marketing",
        "label": "Marketing & Content",
        "description": "Social media, content creation, paid advertising, reporting",
    },
    {
        "id": "supply_chain",
        "label": "Supply Chain & Inventory",
        "description": "Stock management, procurement, supplier relationships",
    },
    {
        "id": "crm_sales",
        "label": "Sales & CRM",
        "description": "Client acquisition, proposals, contracts, pipeline management",
    },
    {
        "id": "operations_backoffice",
        "label": "Finance & Back-office",
        "description": "Invoicing, document generation, internal reporting",
    },
]
_QUESTIONS: dict[str, list[Question]] = {
    "customer_support": [
        {
            "id": "cs_message_volume",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
                    ],
                },
                {
                    "value": "longer",
                    "label": "Longer than 2 days",
                    "pain_flags": [
                        PainFlags.HIGH_VOLUME_SUPPORT,
                        PainFlags.REPETITIVE_SUPPORT,
                    ],
                },
            ],
        },
    ],
    "ecommerce_ops": [
        {
            "id": "ec_order_entry",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
                        PainFlags.MANUAL_DATA_ENTRY,
                    ],
                },
                {
                    "value": "four_plus",
                    "label": "4 or more channels",
                    "pain_flags": [
                        PainFlags.MANUAL_DATA_ENTRY,
                        PainFlags.NO_DATA_INSIGHTS,
                    ],
                },
            ],
        },
        {
            "id": "ec_returns",
            "tier": ["standard", "full"],
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
    ],
    "marketing": [
        {
            "id": "mkt_content",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
    ],
    "supply_chain": [
        {
            "id": "sc_inventory",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
    ],
    "crm_sales": [
        {
            "id": "crm_proposals",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
            "tier": ["full"],
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
                    ],
                },
            ],
        },
    ],
    "operations_backoffice": [
        {
            "id": "bo_invoicing",
            "tier": ["standard", "full"],
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
            "tier": ["standard", "full"],
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
    ],
}

_FULL_TIER_EXTRAS: list[Question] = [
    {
        "id": "full_integrations",
        "tier": ["full"],
        "text": "Which platforms does your company use?",
        "help_text": "Select all that apply.",
        "type": "multi_select",
        "maps_to": "integrations",              # profile.integrations: list[str]
        "options": [
            {"value": "shopify",      "label": "Shopify",              "profile_value": "shopify"},
            {"value": "woocommerce",  "label": "WooCommerce",          "profile_value": "woocommerce"},
            {"value": "magento",      "label": "Magento",              "profile_value": "magento"},
            {"value": "meta_ads",     "label": "Meta Ads",             "profile_value": "meta_ads"},
            {"value": "google_ads",   "label": "Google Ads",           "profile_value": "google_ads"},
            {"value": "mailchimp",    "label": "Mailchimp",            "profile_value": "mailchimp"},
            {"value": "klaviyo",      "label": "Klaviyo",              "profile_value": "klaviyo"},
            {"value": "hubspot",      "label": "HubSpot",              "profile_value": "hubspot"},
            {"value": "salesforce",   "label": "Salesforce",           "profile_value": "salesforce"},
            {"value": "xero",         "label": "Xero",                 "profile_value": "xero"},
            {"value": "quickbooks",   "label": "QuickBooks",           "profile_value": "quickbooks"},
        ],
    },
    {
        "id": "full_data_exports",
        "tier": ["full"],
        "text": "What data do you have available as an export?",
        "help_text": "These help generate more accurate recommendations.",
        "type": "multi_select",
        "maps_to": "export_types_available",    # profile.export_types_available: list[str]
        "options": [
            {"value": "orders",          "label": "Order history",          "profile_value": "orders"},
            {"value": "inventory",       "label": "Inventory data",         "profile_value": "inventory"},
            {"value": "crm",             "label": "CRM / customer data",    "profile_value": "crm"},
            {"value": "support_tickets", "label": "Support ticket history", "profile_value": "support_tickets"},
            {"value": "marketing",       "label": "Marketing / ad data",    "profile_value": "marketing"},
            {"value": "none",            "label": "None / not sure",        "profile_value": None},
        ],
    },
    {
        "id": "full_tech_level",
        "tier": ["full"],
        "text": "How would you rate your team's technical level?",
        "help_text": "This helps us recommend tools that match your setup capacity.",
        "type": "profile_field",
        "maps_to": "tech_sophistication",       # profile.tech_sophistication: int (1/2/3)
        "options": [
            {"value": "1", "label": "Not technical — we prefer no-code / plug-and-play tools", "profile_value": 1},
            {"value": "2", "label": "Some technical people — can handle guided setup",          "profile_value": 2},
            {"value": "3", "label": "Mostly technical — comfortable with APIs and integrations","profile_value": 3},
        ],
    },
]

QUESTION_SCHEMA: dict = {
    "domains": _DOMAINS,
    "questions": _QUESTIONS,
    "full_tier_extras": _FULL_TIER_EXTRAS,
}

def get_questions_for_tier(tier: str) -> dict[str, list[Question]]:
    if tier == "quick":
        return {}

    result: dict[str, list[Question]] = {}
    for domain, questions in _QUESTIONS.items():
        filtered = [q for q in questions if tier in q["tier"]]
        if filtered:
            result[domain] = filtered
    return result

def get_all_catalog_pain_flags() -> set[str]:
    flags: set[str] = set()
    for questions in _QUESTIONS.values():
        for question in questions:
            for option in question.get("options", []):
                flags.update(option.get("pain_flags", []))
    return flags