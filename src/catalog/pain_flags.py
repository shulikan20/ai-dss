from __future__ import annotations

class PainFlags:
    HIGH_VOLUME_SUPPORT = "customer_support.volume.pain_high_volume_support"
    REPETITIVE_SUPPORT = "universal.processes.pain_repetitive_support"
    SLOW_RESPONSE = "universal.processes.pain_slow_response"
    TICKET_OVERLOAD = "universal.processes.pain_ticket_overload"
    BRAND_REPUTATION = "customer_support.reputation.pain_brand_reputation"
    NEGATIVE_REVIEWS = "customer_support.reputation.pain_negative_reviews"
    MULTILINGUAL_SUPPORT = "customer_support.language.pain_multilingual_support"
    MANUAL_RETURNS = "ecommerce_ops.pain_points.pain_manual_returns"
    INVENTORY_TRACKING = "ecommerce_ops.pain_points.pain_inventory_tracking"
    SLOW_ORDER_PROC = "ecommerce_ops.pain_points.pain_slow_order_processing"
    MULTICHANNEL = "ecommerce_ops.pain_points.pain_multichannel"
    MANUAL_DESCRIPTIONS = "ecommerce_ops.catalogue.pain_manual_descriptions"
    COMPETITOR_PRICING = "ecommerce_ops.pricing.pain_competitor_pricing"
    MARGIN_PRESSURE = "ecommerce_ops.pricing.pain_margin_pressure"
    POOR_PRODUCT_DISCOVERY = "ecommerce_ops.discovery.pain_poor_product_discovery"
    LOW_AOV = "ecommerce_ops.revenue.pain_low_aov"
    MANUAL_SUBSCRIPTIONS = "ecommerce_ops.subscriptions.pain_manual_subscriptions"
    STOCKOUTS_SUPPLY_CHAIN = "supply_chain.inventory.pain_stockouts"
    STOCKOUTS_UNIVERSAL = "universal.processes.pain_stockouts"
    OVERSTOCK = "universal.processes.pain_overstock"
    SUPPLIER_TRACKING = "universal.processes.pain_supplier_tracking"
    MANUAL_INVENTORY = "universal.processes.pain_manual_inventory"
    MANUAL_PURCHASE_ORDERS = "supply_chain.procurement.pain_manual_purchase_orders"
    HIGH_SHIPPING_COSTS = "supply_chain.logistics.pain_high_shipping_costs"
    POOR_AD_PERFORMANCE = "marketing.paid.pain_poor_ad_performance"
    MANUAL_AD_CREATIVE = "marketing.paid.pain_manual_ad_creative"
    NO_DATA_INSIGHTS = "universal.processes.pain_no_data_insights"
    LOW_MARKETING_ROI = "universal.processes.pain_low_marketing_roi"
    MANUAL_CONTENT = "universal.processes.pain_manual_content_creation"
    GENERIC_CAMPAIGNS = "marketing.email.pain_generic_campaigns"
    LOW_EMAIL_ENGAGEMENT = "marketing.email.pain_low_email_engagement"
    LOW_ORGANIC_TRAFFIC = "marketing.organic.pain_low_organic_traffic"
    NO_CONTENT_STRATEGY = "marketing.organic.pain_no_content_strategy"
    CUSTOMER_CHURN = "marketing.retention.pain_customer_churn"
    LOW_REPEAT_PURCHASES = "marketing.retention.pain_low_repeat_purchases"
    NO_VIDEO_CONTENT = "marketing.content.pain_no_video_content"
    NO_SMS_CHANNEL = "marketing.messaging.pain_no_sms"
    MANUAL_DATA_ENTRY = "universal.processes.pain_manual_data_entry"
    MANUAL_INVOICING = "universal.processes.pain_manual_invoicing"
    MANUAL_EXPENSES = "operations_backoffice.finance.pain_manual_expenses"
    CASHFLOW_VISIBILITY = "operations_backoffice.finance.pain_cashflow_visibility"
    MANUAL_ONBOARDING = "operations_backoffice.hr.pain_manual_onboarding"
    SCATTERED_KNOWLEDGE = "operations_backoffice.knowledge.pain_scattered_knowledge"
    MANUAL_CONTRACT_REVIEW = "operations_backoffice.legal.pain_manual_contract_review"
    SCHEDULING_OVERHEAD = "operations_backoffice.scheduling.pain_scheduling_overhead" 
    SLOW_FOLLOWUP = "crm_sales.pipeline.pain_slow_followup"
    UNCLEAR_REPORTING = "crm_sales.pipeline.pain_unclear_reporting"
    UNPREDICTABLE_REVENUE = "crm_sales.pipeline.pain_unpredictable_revenue"
    NO_OUTBOUND_LEADGEN = "crm_sales.outbound.pain_no_outbound_leadgen"
    NO_CLV_INSIGHT = "crm_sales.analytics.pain_no_clv_insight"

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("PainFlags is not meant to be subclassed")

    @classmethod
    def all_paths(cls) -> frozenset[str]:
        return frozenset(
            v for k, v in vars(cls).items()
            if not k.startswith("_") and isinstance(v, str)
        )

    @classmethod
    def validate(cls, path: str) -> str:
        if path not in cls.all_paths():
            raise ValueError(
                f"Unknown pain flag path: {path!r}. "
                f"Register it in PainFlags before using it in catalog or question_schema."
            )
        return path