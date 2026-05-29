from __future__ import annotations

from api.translator.questions.types import Domain

DOMAINS: list[Domain] = [
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
