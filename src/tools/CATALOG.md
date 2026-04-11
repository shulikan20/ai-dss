# Tool Catalog

SQLite database (`catalog.db`) containing AI capability patterns and the specific products that implement them. Used as input to the matching pipeline alongside company profiles.

## Run the editor

```bash
pip install flask
python server.py
# open http://localhost:5050
```

Add, edit, and delete capabilities and products through the browser interface. Changes go directly to `catalog.db`.

---

## Structure

Two tables: **capabilities** (what the tool does) and **products** (specific tools that implement it).

---

## capabilities

| Field | Role | Notes |
|---|---|---|
| `capability_id` | — | Unique, snake_case |
| `name` | — | Human label |
| `domain` | fit scoring | Matched against process domain |
| `use_case_category` | fit scoring | Specific label within domain |
| `task_type_target` | fit scoring | `repetitive_routine` / `judgment_intensive` / `mixed` |
| `description` | semantic matching | Vector-embedded, compared against company bottleneck description |
| `bottleneck_keywords` | keyword matching | How companies typically describe this problem |
| `works_without_data` | **gate** | If `0` and company has no data → excluded |
| `required_data_types` | **gate** | Company must have all listed types |
| `min_history_months_gate` | **gate** | Company must have ≥ this many months of data |
| `min_technical_capability` | **gate** | 1=low 2=medium 3=high |
| `primary_outcome` | fit scoring | `time_saved` / `conversion` / `response_time` / `cost` / `accuracy` / `visibility` |
| `time_to_value_weeks_min/max` | fit scoring | How fast results appear |

Fields marked **gate** are hard filters — if the company fails any of them, the capability is excluded before scoring begins.

---

## products

| Field | Role | Notes |
|---|---|---|
| `product_id` | — | Unique, snake_case |
| `capability_id` | — | Links to parent capability |
| `name` / `vendor` / `url` | — | Identity |
| `integrations` | compatibility scoring | Matched against company's current tools and channels |
| `gdpr_compliant` | compatibility scoring | EU companies score non-compliant products lower |
| `deployment_model` | readiness scoring | `saas` / `api` / `self_hosted` / `hybrid` |
| `pricing_model` | readiness scoring | `free` / `freemium` / `subscription` / `usage` / `enterprise` |
| `has_free_tier` | readiness scoring | Boolean |
| `cost_tier` | readiness scoring | `low` / `medium` / `high` / `enterprise` |
| `cost_notes` | output | Shown in recommendation |
| `implementation_effort` | readiness scoring | `low` / `medium` / `high` |
| `min_technical_capability` | readiness scoring | Product may need more than the capability gate |
| `setup_notes` | output | Shown in recommendation |
| `min_history_months` | confidence scoring | Adjusts confidence, not eligibility |
| `works_with_limited_data` | confidence scoring | `1` = degrades gracefully, `0` = needs full data |
| `data_requirement_notes` | output | Shown in recommendation |
| `notes` | output | Any other context |

Product-level data requirements are scoring modifiers, not gates. They adjust confidence after the capability has already passed.

---

## Domains

`customer_support` · `ecommerce_ops` · `crm_sales` · `marketing` · `operations_backoffice` · `supply_chain` · `finance` · `hr` · `it_ops` · `product_engineering` · `manufacturing` · `procurement`