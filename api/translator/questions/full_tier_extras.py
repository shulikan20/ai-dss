from __future__ import annotations

from api.translator.questions.types import Question

EXTRAS: list[Question] = [
    {
        "id": "data_structured",
        "tier": ["standard", "full"],
        "text": "Do you have structured historical data (e.g. sales records, order history) in a system?",
        "help_text": "This affects how accurate AI recommendations can be for your business.",
        "type": "profile_field",
        "maps_to": "has_structured_export",
        "options": [
            {"value": "yes_clean", "label": "Yes — clean, digital records in a system", "profile_value": True},
            {"value": "yes_messy", "label": "Yes — but messy or spread across tools", "profile_value": True},
            {"value": "no_spreadsheet", "label": "Only in spreadsheets", "profile_value": False},
            {"value": "no_nothing", "label": "No structured data", "profile_value": False},
        ],
    },
    {
        "id": "data_history_months",
        "tier": ["standard", "full"],
        "text": "How many months of data history do you have?",
        "type": "profile_field",
        "maps_to": "history_months",
        "options": [
            {"value": "0", "label": "None — just getting started", "profile_value": 0},
            {"value": "3", "label": "1 – 3 months", "profile_value": 3},
            {"value": "12", "label": "3 – 12 months", "profile_value": 12},
            {"value": "24", "label": "Over 12 months", "profile_value": 24},
        ],
    },
    {
        "id": "full_integrations",
        "tier": ["full"],
        "text": "Which platforms does your company use?",
        "help_text": "Select all that apply.",
        "type": "multi_select",
        "maps_to": "integrations",
        "options": [
            {"value": "shopify", "label": "Shopify", "profile_value": "shopify"},
            {"value": "woocommerce", "label": "WooCommerce", "profile_value": "woocommerce"},
            {"value": "magento", "label": "Magento", "profile_value": "magento"},
            {"value": "meta_ads", "label": "Meta Ads", "profile_value": "meta_ads"},
            {"value": "google_ads", "label": "Google Ads", "profile_value": "google_ads"},
            {"value": "mailchimp", "label": "Mailchimp", "profile_value": "mailchimp"},
            {"value": "klaviyo", "label": "Klaviyo", "profile_value": "klaviyo"},
            {"value": "hubspot", "label": "HubSpot", "profile_value": "hubspot"},
            {"value": "salesforce", "label": "Salesforce", "profile_value": "salesforce"},
            {"value": "xero", "label": "Xero", "profile_value": "xero"},
            {"value": "quickbooks", "label": "QuickBooks", "profile_value": "quickbooks"},
        ],
    },
    {
        "id": "full_data_exports",
        "tier": ["full"],
        "text": "What data do you have available as an export?",
        "help_text": "These help generate more accurate recommendations.",
        "type": "multi_select",
        "maps_to": "export_types_available",
        "options": [
            {"value": "orders", "label": "Order history", "profile_value": "orders"},
            {"value": "inventory", "label": "Inventory data", "profile_value": "inventory"},
            {"value": "crm", "label": "CRM / customer data", "profile_value": "crm"},
            {"value": "support_tickets", "label": "Support ticket history", "profile_value": "support_tickets"},
            {"value": "marketing", "label": "Marketing / ad data", "profile_value": "marketing"},
            {"value": "none", "label": "None / not sure", "profile_value": None},
        ],
    },
    {
        "id": "full_tech_level",
        "tier": ["standard", "full"],
        "text": "How would you rate your team's technical level?",
        "help_text": "This helps us recommend tools that match your setup capacity.",
        "type": "profile_field",
        "maps_to": "tech_sophistication",
        "options": [
            {"value": "1", "label": "Not technical — we prefer no-code / plug-and-play tools", "profile_value": 1},
            {"value": "2", "label": "Some technical people — can handle guided setup", "profile_value": 2},
            {"value": "3", "label": "Mostly technical — comfortable with APIs and integrations","profile_value": 3},
        ],
    },
]
