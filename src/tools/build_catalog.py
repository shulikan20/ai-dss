import sqlite3
import json
import os

DB_PATH = "catalog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS capabilities (
    capability_id           TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    domain                  TEXT NOT NULL,
    use_case_category       TEXT NOT NULL,
    task_type_target        TEXT NOT NULL,
    description             TEXT NOT NULL,
    bottleneck_keywords     TEXT,
    requires_historical_data    INTEGER NOT NULL DEFAULT 0,
    required_data_types         TEXT,
    works_without_data          INTEGER NOT NULL DEFAULT 1,
    min_history_months_gate     INTEGER,
    min_technical_capability    INTEGER NOT NULL DEFAULT 1,
    primary_outcome             TEXT,
    secondary_outcomes          TEXT,
    time_to_value_weeks_min     INTEGER,
    time_to_value_weeks_max     INTEGER,
    created_at              TEXT DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS products (
    product_id              TEXT PRIMARY KEY,
    capability_id           TEXT NOT NULL REFERENCES capabilities(capability_id),
    name                    TEXT NOT NULL,
    vendor                  TEXT,
    url                     TEXT,
    integrations            TEXT NOT NULL,
    gdpr_compliant          INTEGER NOT NULL DEFAULT 0,
    deployment_model        TEXT NOT NULL,
    pricing_model           TEXT NOT NULL,
    has_free_tier           INTEGER NOT NULL DEFAULT 0,
    cost_tier               TEXT NOT NULL,
    cost_notes              TEXT,
    implementation_effort   TEXT NOT NULL,
    min_technical_capability INTEGER NOT NULL DEFAULT 1,
    setup_notes             TEXT,
    min_history_months      INTEGER,
    min_record_count        INTEGER,
    works_with_limited_data INTEGER DEFAULT 1,
    data_requirement_notes  TEXT,
    notes                   TEXT,
    created_at              TEXT DEFAULT (date('now'))
);

CREATE INDEX IF NOT EXISTS idx_cap_domain  ON capabilities(domain);
CREATE INDEX IF NOT EXISTS idx_cap_task    ON capabilities(task_type_target);
CREATE INDEX IF NOT EXISTS idx_cap_nodata  ON capabilities(works_without_data);
CREATE INDEX IF NOT EXISTS idx_prod_cap    ON products(capability_id);
CREATE INDEX IF NOT EXISTS idx_prod_cost   ON products(cost_tier);
CREATE INDEX IF NOT EXISTS idx_prod_effort ON products(implementation_effort);
CREATE INDEX IF NOT EXISTS idx_prod_gdpr   ON products(gdpr_compliant);
"""

CAPABILITIES = [
    {
        "capability_id": "faq_dm_automation",
        "name": "FAQ Automation for Repetitive DM Inquiries",
        "domain": "customer_support",
        "use_case_category": "automated_messaging",
        "task_type_target": "repetitive_routine",
        "description": "Automatically responds to common pre-sale questions arriving via Instagram DM, WhatsApp, or email. Uses rule-based flows or AI to handle repetitive questions about sizing, pricing, shipping, and availability without human intervention.",
        "bottleneck_keywords": json.dumps(["repetitive questions", "manual responses", "slow reply time", "FAQ", "pre-sale communication", "DM handling", "same questions", "messaging", "inbox", "response time"]),
        "requires_historical_data": 0, "required_data_types": json.dumps([]), "works_without_data": 1, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["response_time", "conversion"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 2,
    },
    {
        "capability_id": "order_status_automation",
        "name": "Automated Order Status and Shipping Updates",
        "domain": "ecommerce_ops",
        "use_case_category": "post_purchase_communication",
        "task_type_target": "repetitive_routine",
        "description": "Automatically sends customers proactive order confirmation, shipping notification, and delivery status messages. Eliminates inbound 'where is my order' contacts by pushing updates before customers need to ask.",
        "bottleneck_keywords": json.dumps(["where is my order", "shipping update", "delivery status", "order tracking", "post-purchase questions", "customer contacts after order"]),
        "requires_historical_data": 0, "required_data_types": json.dumps(["order_data"]), "works_without_data": 0, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["response_time"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 3,
    },
    {
        "capability_id": "abandoned_cart_recovery",
        "name": "Abandoned Cart and Browse Recovery",
        "domain": "ecommerce_ops",
        "use_case_category": "conversion_recovery",
        "task_type_target": "repetitive_routine",
        "description": "Detects when a visitor adds items to cart or browses products without purchasing and automatically sends a timed follow-up email or message to recover the potential sale. Requires website event tracking to function.",
        "bottleneck_keywords": json.dumps(["low website conversion", "visitors not buying", "cart abandonment", "no follow-up", "browse without purchase", "website traffic not converting"]),
        "requires_historical_data": 0, "required_data_types": json.dumps(["website_events"]), "works_without_data": 0, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "conversion", "secondary_outcomes": json.dumps(["time_saved"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 2,
    },
    {
        "capability_id": "content_generation_social",
        "name": "AI-Assisted Social Media Content Generation",
        "domain": "marketing",
        "use_case_category": "content_creation",
        "task_type_target": "mixed",
        "description": "Generates product descriptions, social media captions, campaign copy, and content variants from a brief or product information. Reduces time spent on writing and ideation for recurring content needs.",
        "bottleneck_keywords": json.dumps(["content creation", "copywriting", "social media posts", "product descriptions", "captions", "writing takes time", "content burden", "campaign copy", "design"]),
        "requires_historical_data": 0, "required_data_types": json.dumps([]), "works_without_data": 1, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["visibility"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 1,
    },
    {
        "capability_id": "document_generation",
        "name": "AI-Assisted Document and Report Generation",
        "domain": "operations_backoffice",
        "use_case_category": "document_automation",
        "task_type_target": "mixed",
        "description": "Generates structured documents — proposals, contracts, reports, briefs, post-event summaries — from a set of inputs or a brief. Reduces time spent writing documents from scratch by using templates combined with AI drafting.",
        "bottleneck_keywords": json.dumps(["report generation", "proposal writing", "document creation", "contracts", "briefs", "writing from scratch", "reporting takes time", "templates", "post-event report", "documentation"]),
        "requires_historical_data": 0, "required_data_types": json.dumps([]), "works_without_data": 1, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["accuracy"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 2,
    },
    {
        "capability_id": "demand_forecasting",
        "name": "Demand Forecasting and Inventory Planning",
        "domain": "supply_chain",
        "use_case_category": "inventory_planning",
        "task_type_target": "judgment_intensive",
        "description": "Predicts future product demand based on historical sales data, seasonality patterns, and trends. Helps determine optimal reorder quantities and timing to reduce stockouts and overstock situations.",
        "bottleneck_keywords": json.dumps(["stockout", "out of stock", "inventory planning", "demand forecasting", "reorder timing", "seasonal demand", "gut feeling ordering", "over-ordering", "stock levels", "running low"]),
        "requires_historical_data": 1, "required_data_types": json.dumps(["order_history", "inventory_data"]), "works_without_data": 0, "min_history_months_gate": 6, "min_technical_capability": 1,
        "primary_outcome": "cost", "secondary_outcomes": json.dumps(["accuracy", "time_saved"]), "time_to_value_weeks_min": 4, "time_to_value_weeks_max": 8,
    },
    {
        "capability_id": "supplier_communication_assistant",
        "name": "Supplier Communication and RFQ Drafting Assistant",
        "domain": "supply_chain",
        "use_case_category": "procurement_communication",
        "task_type_target": "repetitive_routine",
        "description": "Assists with drafting supplier communication, request-for-quote documents, and order follow-up messages. Reduces time spent on repetitive supplier correspondence and helps standardize communication.",
        "bottleneck_keywords": json.dumps(["supplier communication", "RFQ", "supplier emails", "order follow-up", "chasing suppliers", "communication with suppliers", "quote requests", "procurement emails"]),
        "requires_historical_data": 0, "required_data_types": json.dumps([]), "works_without_data": 1, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps([]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 1,
    },
    {
        "capability_id": "email_marketing_personalization",
        "name": "Behavioural Email Marketing Automation",
        "domain": "marketing",
        "use_case_category": "lifecycle_email",
        "task_type_target": "repetitive_routine",
        "description": "Sends personalised email sequences triggered by customer behaviour — first purchase, repeat purchase, inactivity, product browse. Increases customer retention and repeat purchase rate without manual campaign management.",
        "bottleneck_keywords": json.dumps(["email marketing", "customer retention", "repeat purchase", "lifecycle emails", "follow-up emails", "win-back", "personalised emails", "customer segments"]),
        "requires_historical_data": 1, "required_data_types": json.dumps(["order_history", "contact_records"]), "works_without_data": 0, "min_history_months_gate": 3, "min_technical_capability": 1,
        "primary_outcome": "conversion", "secondary_outcomes": json.dumps(["time_saved"]), "time_to_value_weeks_min": 2, "time_to_value_weeks_max": 4,
    },
    {
        "capability_id": "return_management_automation",
        "name": "Return Request Intake and Processing Automation",
        "domain": "ecommerce_ops",
        "use_case_category": "returns_processing",
        "task_type_target": "repetitive_routine",
        "description": "Provides customers with a self-service return request form, automatically generates return labels, and sends status updates throughout the return process. Reduces manual handling time per return case.",
        "bottleneck_keywords": json.dumps(["returns", "refunds", "return handling", "return processing", "manual returns", "return rate", "complaints", "exchanges"]),
        "requires_historical_data": 0, "required_data_types": json.dumps(["order_data"]), "works_without_data": 0, "min_history_months_gate": None, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["response_time"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 3,
    },
    {
        "capability_id": "multichannel_order_sync",
        "name": "Multi-channel Order Synchronisation",
        "domain": "ecommerce_ops",
        "use_case_category": "order_management",
        "task_type_target": "repetitive_routine",
        "description": "Automatically pulls orders from multiple sales channels (Instagram, Facebook Shop, marketplace, website) into a single order management system. Eliminates manual order entry from social channels.",
        "bottleneck_keywords": json.dumps(["manual order entry", "orders from instagram", "facebook orders", "channel sync", "multiple channels", "copy paste orders", "social commerce orders", "order management"]),
        "requires_historical_data": 0, "required_data_types": json.dumps([]), "works_without_data": 1, "min_history_months_gate": None, "min_technical_capability": 2,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["accuracy"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 4,
    },
    {
        "capability_id": "crm_data_enrichment",
        "name": "Automated CRM Data Entry and Enrichment",
        "domain": "crm_sales",
        "use_case_category": "crm_hygiene",
        "task_type_target": "repetitive_routine",
        "description": "Automatically extracts structured information from emails, call notes, and messages and populates CRM fields. Keeps CRM data complete and up to date without manual entry by sales reps.",
        "bottleneck_keywords": json.dumps(["manual CRM entry", "CRM data quality", "missing fields", "CRM hygiene", "data entry", "updating CRM", "CRM not up to date", "incomplete records"]),
        "requires_historical_data": 0, "required_data_types": json.dumps(["communication_logs"]), "works_without_data": 0, "min_history_months_gate": None, "min_technical_capability": 2,
        "primary_outcome": "accuracy", "secondary_outcomes": json.dumps(["time_saved"]), "time_to_value_weeks_min": 2, "time_to_value_weeks_max": 4,
    },
    {
        "capability_id": "campaign_performance_reporting",
        "name": "Unified Marketing Performance Dashboard",
        "domain": "marketing",
        "use_case_category": "performance_reporting",
        "task_type_target": "repetitive_routine",
        "description": "Aggregates performance data from multiple marketing platforms (Meta Ads, email, website analytics) into a single view. Automates weekly reporting and surfaces anomalies without manual data pulling.",
        "bottleneck_keywords": json.dumps(["performance reporting", "marketing dashboard", "manual reporting", "pulling data", "multiple platforms", "CPA", "ROAS", "weekly report", "campaign analysis", "scattered data"]),
        "requires_historical_data": 1, "required_data_types": json.dumps(["ad_platform", "email_marketing", "website_analytics"]), "works_without_data": 0, "min_history_months_gate": 1, "min_technical_capability": 1,
        "primary_outcome": "time_saved", "secondary_outcomes": json.dumps(["accuracy"]), "time_to_value_weeks_min": 1, "time_to_value_weeks_max": 2,
    },
]

PRODUCTS = [
    # faq_dm_automation
    {"product_id": "manychat", "capability_id": "faq_dm_automation", "name": "ManyChat", "vendor": "ManyChat Inc.", "url": "https://manychat.com", "integrations": json.dumps(["instagram_dm", "whatsapp", "facebook", "shopify", "email"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free up to 1,000 contacts. Pro from ~$15/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "No-code visual flow builder. Instagram and WhatsApp setup in 1–2 days.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data needed. Works from day 1.", "notes": "Market leader for Instagram DM automation. Best fit for B2C shops with Instagram as primary channel."},
    {"product_id": "tidio", "capability_id": "faq_dm_automation", "name": "Tidio", "vendor": "Tidio LLC", "url": "https://tidio.com", "integrations": json.dumps(["email", "chat_widget", "shopify", "woocommerce"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free tier available. Paid from ~$29/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Shopify plugin or website widget. Setup under 1 hour.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data needed.", "notes": "Stronger for website chat than DM channels."},
    {"product_id": "chatgpt_custom_gpt", "capability_id": "faq_dm_automation", "name": "ChatGPT Custom GPT / API", "vendor": "OpenAI", "url": "https://openai.com", "integrations": json.dumps(["api"]), "gdpr_compliant": 0, "deployment_model": "api", "pricing_model": "usage", "has_free_tier": 0, "cost_tier": "medium", "cost_notes": "~$10–100/mo depending on volume.", "implementation_effort": "high", "min_technical_capability": 3, "setup_notes": "Requires developer to build channel integration.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "FAQ content provided manually. No order history needed.", "notes": "Most flexible but highest setup cost. Only suitable with technical staff."},
    # order_status_automation
    {"product_id": "keycrm_shipping_notify", "capability_id": "order_status_automation", "name": "KeyCRM Built-in Shipping Notifications", "vendor": "KeyCRM", "url": "https://keycrm.app", "integrations": json.dumps(["keycrm", "nova_poshta", "ukrposhta"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "low", "cost_notes": "Included in KeyCRM subscription (~$20–50/mo).", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Native feature in CRM settings. Active in 1 day.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Works as soon as orders exist in KeyCRM.", "notes": "Specific to Nova Poshta / Ukrposhta delivery services."},
    {"product_id": "shopify_flow_shipping", "capability_id": "order_status_automation", "name": "Shopify Email Notifications", "vendor": "Shopify", "url": "https://shopify.com", "integrations": json.dumps(["shopify", "email", "sms"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "low", "cost_notes": "Included in Shopify subscription. Basic from ~$29/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Built-in templates in Shopify admin. Configure in under 1 hour.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Works from first order.", "notes": "Zero extra cost for Shopify stores."},
    # abandoned_cart_recovery
    {"product_id": "klaviyo_cart", "capability_id": "abandoned_cart_recovery", "name": "Klaviyo Abandoned Cart Flow", "vendor": "Klaviyo", "url": "https://klaviyo.com", "integrations": json.dumps(["shopify", "woocommerce", "email"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free up to 250 contacts. Paid from ~$20/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Pre-built flow template. Shopify/WooCommerce integration in 1–2 hours.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Starts capturing events immediately. No historical data needed.", "notes": "Industry standard for e-commerce email automation."},
    {"product_id": "shopify_abandoned_checkout", "capability_id": "abandoned_cart_recovery", "name": "Shopify Abandoned Checkout Recovery", "vendor": "Shopify", "url": "https://shopify.com", "integrations": json.dumps(["shopify", "email"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "low", "cost_notes": "Included in Shopify subscription.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Native feature. Enable in Marketing settings. 15 minutes.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Works from first abandoned checkout.", "notes": "Zero extra cost for Shopify stores. Less customisable than Klaviyo."},
    # content_generation_social
    {"product_id": "jasper", "capability_id": "content_generation_social", "name": "Jasper", "vendor": "Jasper AI", "url": "https://jasper.ai", "integrations": json.dumps(["browser_extension", "api"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "medium", "cost_notes": "From ~$39/mo per seat.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Browser-based. Brand voice setup takes 1–2 hours.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No company data needed.", "notes": "Marketed at marketing teams. Pre-built templates for product descriptions, social captions, campaigns."},
    {"product_id": "chatgpt_plus_content", "capability_id": "content_generation_social", "name": "ChatGPT Plus / Claude", "vendor": "OpenAI / Anthropic", "url": "https://chat.openai.com", "integrations": json.dumps(["browser"]), "gdpr_compliant": 0, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free tier available. Plus ~$20/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "No setup. Use via chat interface.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No data needed.", "notes": "Most flexible and lowest cost. Requires user to write good prompts."},
    {"product_id": "canva_magic_write", "capability_id": "content_generation_social", "name": "Canva Magic Write", "vendor": "Canva", "url": "https://canva.com", "integrations": json.dumps(["canva"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Included in Canva Free and Pro (~$13/mo).", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Available inside Canva editor. No separate setup.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No data needed.", "notes": "Best fit for companies already using Canva for design."},
    # document_generation
    {"product_id": "notion_ai", "capability_id": "document_generation", "name": "Notion AI", "vendor": "Notion Labs", "url": "https://notion.so", "integrations": json.dumps(["notion"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "low", "cost_notes": "~$8/mo per member on top of Notion plan.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Enable in Notion workspace settings.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Works from any text input. No external data needed.", "notes": "Best fit for companies already using Notion."},
    {"product_id": "chatgpt_docs", "capability_id": "document_generation", "name": "ChatGPT / Claude for Document Drafting", "vendor": "OpenAI / Anthropic", "url": "https://chat.openai.com", "integrations": json.dumps(["browser", "google_docs_extension"]), "gdpr_compliant": 0, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free tier available. Plus ~$20/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "No setup. Paste brief into chat.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No data needed.", "notes": "Lowest barrier. Works well for companies with no existing tooling."},
    # demand_forecasting
    {"product_id": "inventory_planner", "capability_id": "demand_forecasting", "name": "Inventory Planner", "vendor": "Inventory Planner", "url": "https://inventoryplanner.com", "integrations": json.dumps(["shopify", "woocommerce", "amazon"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "medium", "cost_notes": "From ~$99/mo. 14-day trial.", "implementation_effort": "medium", "min_technical_capability": 1, "setup_notes": "Native Shopify/WooCommerce integration. Initial sync 1–2 days.", "min_history_months": 6, "min_record_count": None, "works_with_limited_data": 0, "data_requirement_notes": "Minimum 6 months sales history stated by vendor.", "notes": "Purpose-built for e-commerce inventory forecasting."},
    {"product_id": "stocky_shopify", "capability_id": "demand_forecasting", "name": "Shopify Stocky", "vendor": "Shopify", "url": "https://apps.shopify.com/stocky", "integrations": json.dumps(["shopify"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "free", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free Shopify app.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Install from Shopify App Store.", "min_history_months": 3, "min_record_count": 100, "works_with_limited_data": 1, "data_requirement_notes": "Works with 3+ months. Less accurate with limited history but functional.", "notes": "Free and well-integrated for Shopify stores."},
    # supplier_communication_assistant
    {"product_id": "chatgpt_supplier", "capability_id": "supplier_communication_assistant", "name": "ChatGPT / Claude for Supplier Drafting", "vendor": "OpenAI / Anthropic", "url": "https://chat.openai.com", "integrations": json.dumps(["browser"]), "gdpr_compliant": 0, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free tier available.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "No setup. Use with a standard prompt template.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No data needed.", "notes": "Does not automate — user must trigger each draft manually."},
    # email_marketing_personalization
    {"product_id": "klaviyo_flows", "capability_id": "email_marketing_personalization", "name": "Klaviyo Behavioral Flows", "vendor": "Klaviyo", "url": "https://klaviyo.com", "integrations": json.dumps(["shopify", "woocommerce", "email"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free up to 250 contacts. Scales with list size.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Pre-built flow templates. Shopify/WooCommerce setup in 1–2 hours.", "min_history_months": 3, "min_record_count": 200, "works_with_limited_data": 1, "data_requirement_notes": "Flows work immediately. Personalisation improves with more history.", "notes": "Industry standard for e-commerce email automation."},
    {"product_id": "mailchimp_automations", "capability_id": "email_marketing_personalization", "name": "Mailchimp Customer Journey Builder", "vendor": "Mailchimp", "url": "https://mailchimp.com", "integrations": json.dumps(["shopify", "woocommerce", "email", "api"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free up to 500 contacts. Standard from ~$13/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Visual journey builder. Shopify/WooCommerce or API.", "min_history_months": 1, "min_record_count": 100, "works_with_limited_data": 1, "data_requirement_notes": "Works from minimal data.", "notes": "More accessible than Klaviyo for beginners."},
    # return_management_automation
    {"product_id": "returngo", "capability_id": "return_management_automation", "name": "ReturnGO", "vendor": "ReturnGO", "url": "https://returngo.ai", "integrations": json.dumps(["shopify"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "low", "cost_notes": "From ~$23/mo. 14-day trial.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Shopify app install. Return portal live in 1–2 hours.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data needed.", "notes": "Purpose-built return management for Shopify."},
    {"product_id": "loop_returns", "capability_id": "return_management_automation", "name": "Loop Returns", "vendor": "Loop", "url": "https://loopreturns.com", "integrations": json.dumps(["shopify"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "subscription", "has_free_tier": 0, "cost_tier": "medium", "cost_notes": "From ~$59/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Shopify app. Branded return portal. Setup 1–2 days.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data required.", "notes": "More feature-rich than ReturnGO. Exchange-first approach."},
    # multichannel_order_sync
    {"product_id": "zapier_order_sync", "capability_id": "multichannel_order_sync", "name": "Zapier", "vendor": "Zapier", "url": "https://zapier.com", "integrations": json.dumps(["instagram", "facebook", "shopify", "woocommerce", "google_sheets", "email"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free for 100 tasks/mo. Starter from ~$20/mo.", "implementation_effort": "medium", "min_technical_capability": 2, "setup_notes": "No-code but requires trigger/action understanding. 2–4 hours per integration.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data needed. Syncs new orders in real time.", "notes": "Most flexible — connects almost any two systems."},
    {"product_id": "make_order_sync", "capability_id": "multichannel_order_sync", "name": "Make (formerly Integromat)", "vendor": "Make", "url": "https://make.com", "integrations": json.dumps(["instagram", "facebook", "shopify", "woocommerce", "google_sheets"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free for 1,000 operations/mo. Core from ~$9/mo.", "implementation_effort": "medium", "min_technical_capability": 2, "setup_notes": "Visual scenario builder. More powerful than Zapier. 2–6 hours setup.", "min_history_months": None, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "No historical data needed.", "notes": "Better value than Zapier at scale. Steeper learning curve."},
    # campaign_performance_reporting
    {"product_id": "databox", "capability_id": "campaign_performance_reporting", "name": "Databox", "vendor": "Databox Inc.", "url": "https://databox.com", "integrations": json.dumps(["meta_ads", "google_ads", "mailchimp", "klaviyo", "shopify", "google_analytics"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "freemium", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free for up to 3 sources. Starter from ~$47/mo.", "implementation_effort": "low", "min_technical_capability": 1, "setup_notes": "Pre-built connectors. Dashboard live in 1–2 hours.", "min_history_months": 1, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Starts pulling data immediately after connecting sources.", "notes": "Best low-effort option for unified marketing reporting."},
    {"product_id": "looker_studio", "capability_id": "campaign_performance_reporting", "name": "Google Looker Studio", "vendor": "Google", "url": "https://lookerstudio.google.com", "integrations": json.dumps(["google_analytics", "google_ads", "google_sheets", "meta_ads"]), "gdpr_compliant": 1, "deployment_model": "saas", "pricing_model": "free", "has_free_tier": 1, "cost_tier": "low", "cost_notes": "Free. Some third-party connectors ~$20/mo.", "implementation_effort": "medium", "min_technical_capability": 2, "setup_notes": "Dashboard built from scratch. Setup 4–8 hours.", "min_history_months": 1, "min_record_count": None, "works_with_limited_data": 1, "data_requirement_notes": "Works from day 1.", "notes": "Free but more effort than Databox. Good for Google Workspace users."},
]

CAP_KEYS = ["capability_id","name","domain","use_case_category","task_type_target","description","bottleneck_keywords","requires_historical_data","required_data_types","works_without_data","min_history_months_gate","min_technical_capability","primary_outcome","secondary_outcomes","time_to_value_weeks_min","time_to_value_weeks_max"]
PROD_KEYS = ["product_id","capability_id","name","vendor","url","integrations","gdpr_compliant","deployment_model","pricing_model","has_free_tier","cost_tier","cost_notes","implementation_effort","min_technical_capability","setup_notes","min_history_months","min_record_count","works_with_limited_data","data_requirement_notes","notes"]

def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executemany(f"INSERT INTO capabilities ({','.join(CAP_KEYS)}) VALUES ({','.join(['?']*len(CAP_KEYS))})", [[c.get(k) for k in CAP_KEYS] for c in CAPABILITIES])
    conn.executemany(f"INSERT INTO products ({','.join(PROD_KEYS)}) VALUES ({','.join(['?']*len(PROD_KEYS))})", [[p.get(k) for k in PROD_KEYS] for p in PRODUCTS])
    conn.commit()
    print(f"Built: {len(CAPABILITIES)} capabilities, {len(PRODUCTS)} products\n")
    print("── by domain ──────────────────────────────────────────────")
    for row in conn.execute("SELECT domain, COUNT(*) FROM capabilities GROUP BY domain ORDER BY domain"):
        print(f"  {row[0]:<35} {row[1]} capabilities")
    print("\n── products per capability ────────────────────────────────")
    for row in conn.execute("SELECT c.name, COUNT(p.product_id) FROM capabilities c LEFT JOIN products p ON c.capability_id=p.capability_id GROUP BY c.capability_id ORDER BY c.domain"):
        print(f"  {row[0]:<50} {row[1]} products")
    conn.close()
    print(f"\nSaved: {DB_PATH}")

if __name__ == "__main__":
    build()
