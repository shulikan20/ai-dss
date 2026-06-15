from __future__ import annotations

from src.catalog.pain_flags import PainFlags

TAGS: dict[str, list[dict]] = {
    "supply_chain": [
        {
            "label": "We frequently run out of stock on popular items",
            "flags": [PainFlags.STOCKOUTS_UNIVERSAL, PainFlags.STOCKOUTS_SUPPLY_CHAIN],
        },
        {
            "label": "We have too much stock of slow-moving products",
            "flags": [PainFlags.OVERSTOCK],
        },
        {
            "label": "We track inventory manually in spreadsheets or by hand",
            "flags": [PainFlags.MANUAL_INVENTORY, PainFlags.INVENTORY_TRACKING],
        },
        {
            "label": "Supplier communication and order tracking is unstructured",
            "flags": [PainFlags.SUPPLIER_TRACKING],
        },
                {
            "label": "Raising and approving purchase orders is manual",
            "flags": [PainFlags.MANUAL_PURCHASE_ORDERS],
        },
        {
            "label": "We overspend on shipping with a single carrier",
            "flags": [PainFlags.HIGH_SHIPPING_COSTS],
        },
    ],
    "ecommerce_ops": [
        {
            "label": "Managing orders across multiple sales channels is messy",
            "flags": [PainFlags.MULTICHANNEL],
        },
        {
            "label": "Returns and refunds are handled manually",
            "flags": [PainFlags.MANUAL_RETURNS],
        },
        {
            "label": "We lose sales because items go out of stock",
            "flags": [PainFlags.STOCKOUTS_UNIVERSAL],
        },
        {
            "label": "Order processing takes too long",
            "flags": [PainFlags.SLOW_ORDER_PROC],
        },
        {
            "label": "Shoppers can't find products through our search",
            "flags": [PainFlags.POOR_PRODUCT_DISCOVERY],
        },
        {
            "label": "Our average order value is low — customers buy just one item",
            "flags": [PainFlags.LOW_AOV],
        },
        {
            "label": "Managing recurring orders and subscriptions is manual",
            "flags": [PainFlags.MANUAL_SUBSCRIPTIONS],
        },
    ],
    "customer_support": [
        {
            "label": "We answer the same customer questions repeatedly",
            "flags": [PainFlags.REPETITIVE_SUPPORT],
        },
        {
            "label": "Customers complain about slow response times",
            "flags": [PainFlags.SLOW_RESPONSE],
        },
        {
            "label": "Our support team is overwhelmed by message volume",
            "flags": [PainFlags.HIGH_VOLUME_SUPPORT, PainFlags.TICKET_OVERLOAD],
        },
        {
            "label": "Negative reviews are affecting our reputation",
            "flags": [PainFlags.NEGATIVE_REVIEWS],
        },
        {
            "label": "Customers write in several languages but our team speaks one",
            "flags": [PainFlags.MULTILINGUAL_SUPPORT],
        },
    ],
    "marketing": [
        {
            "label": "Our paid ads don't perform well or are hard to manage",
            "flags": [PainFlags.POOR_AD_PERFORMANCE],
        },
        {
            "label": "Creating content takes too much time",
            "flags": [PainFlags.MANUAL_CONTENT],
        },
        {
            "label": "We have low organic traffic to our website",
            "flags": [PainFlags.LOW_ORGANIC_TRAFFIC],
        },
        {
            "label": "Email campaigns have poor engagement",
            "flags": [PainFlags.LOW_EMAIL_ENGAGEMENT],
        },
        {
            "label": "We're losing customers and don't understand why",
            "flags": [PainFlags.CUSTOMER_CHURN, PainFlags.LOW_REPEAT_PURCHASES],
        },
        {
            "label": "We struggle to produce short video content",
            "flags": [PainFlags.NO_VIDEO_CONTENT],
        },
        {
            "label": "We rely only on email and can't reach customers by SMS",
            "flags": [PainFlags.NO_SMS_CHANNEL],
        },
    ],
    "crm_sales": [
        {
            "label": "We have no steady flow of new outbound B2B leads",
            "flags": [PainFlags.NO_OUTBOUND_LEADGEN],
        },
        {
            "label": "We don't know which customers are worth the most over time",
            "flags": [PainFlags.NO_CLV_INSIGHT],
        },
        {
            "label": "We struggle to follow up with leads on time",
            "flags": [PainFlags.SLOW_FOLLOWUP],
        },
        {
            "label": "We have no clear view of our sales pipeline",
            "flags": [PainFlags.UNCLEAR_REPORTING],
        },
        {
            "label": "Revenue is unpredictable month to month",
            "flags": [PainFlags.UNPREDICTABLE_REVENUE],
        },
    ],
    "operations_backoffice": [
        {
            "label": "Invoicing and document creation is manual and slow",
            "flags": [PainFlags.MANUAL_INVOICING],
        },
        {
            "label": "We spend too much time on data entry",
            "flags": [PainFlags.MANUAL_DATA_ENTRY],
        },
        {
            "label": "We re-type receipts and expenses into the books by hand",
            "flags": [PainFlags.MANUAL_EXPENSES],
        },
        {
            "label": "We can't see our cash position ahead of time",
            "flags": [PainFlags.CASHFLOW_VISIBILITY],
        },
        {
            "label": "Onboarding new hires is manual and chaotic",
            "flags": [PainFlags.MANUAL_ONBOARDING],
        },
        {
            "label": "Staff can't find internal information when they need it",
            "flags": [PainFlags.SCATTERED_KNOWLEDGE],
        },
        {
            "label": "Reviewing supplier and client contracts is slow or costly",
            "flags": [PainFlags.MANUAL_CONTRACT_REVIEW],
        },
        {
            "label": "Scheduling meetings means endless back-and-forth emails",
            "flags": [PainFlags.SCHEDULING_OVERHEAD],
        },
    ],
}
