"""
Synthetic CRM Data Generator — 3 Fictional Companies
=====================================================
Generates realistic B2C e-commerce order data for three completely
fictional businesses. No connection to any real company.

Companies:
  SC1 — TinyWonders GmbH (Vienna, Austria) — premium wooden toys, EUR
  SC2 — FitPol (Warsaw, Poland)             — fitness supplements, PLN
  SC3 — PawNL (Amsterdam, Netherlands)      — pet accessories, EUR

Output per company:
  synthetic_<id>_orders.json
  synthetic_<id>_orders.csv
"""

import json
import csv
import random
from datetime import datetime, timedelta

random.seed(99)

COMPANIES = {

    "SC1_TinyWonders": {
        "id": "SC1",
        "name": "TinyWonders GmbH",
        "country": "Austria",
        "currency": "EUR",
        "num_orders": 640,
        "start_date": datetime(2023, 9, 1),
        "end_date":   datetime(2026, 3, 31),
        "channels": [("Website", 0.72), ("Instagram", 0.28)],
        "delivery_services": [("DPD Austria", 0.60), ("Österreichische Post", 0.40)],
        "managers": ["Manager_A", "Manager_B"],
        "statuses": [
            ("Completed",        0.85),
            ("New",              0.10),
            ("Awaiting Review",  0.03),
            ("Cancelled",        0.02),
        ],
        "products": [
            ("Wooden Block Set 40pcs",        24,  38),
            ("Waldorf Rainbow Stacker",        32,  52),
            ("Magnetic Drawing Board",         18,  29),
            ("Sensory Ball Set",               14,  22),
            ("Wooden Train Track Set",         48,  74),
            ("Montessori Puzzle 6-shape",      16,  26),
            ("Finger Paint Set",               10,  18),
            ("Wooden Kitchen Playset",         55,  88),
            ("Balance Bike 12-inch",           89, 135),
            ("Beeswax Modelling Kit",          12,  19),
            ("Silicone Building Blocks",       22,  34),
            ("Felt Animal Sewing Kit",         15,  24),
        ],
        "cities": [
            "Vienna", "Graz", "Linz", "Salzburg", "Innsbruck",
            "Klagenfurt", "Wels", "Sankt Pölten", "Dornbirn", "Feldkirch"
        ],
        "seasonal_peak_months": [11, 12],
        "seasonal_boost": 3.2,
        "quantity_single_prob": 0.80,
    },

    "SC2_FitPol": {
        "id": "SC2",
        "name": "FitPol Sp. z o.o.",
        "country": "Poland",
        "currency": "PLN",
        "num_orders": 950,
        "start_date": datetime(2023, 4, 1),
        "end_date":   datetime(2026, 3, 31),
        "channels": [("Website", 0.55), ("Instagram", 0.30), ("Facebook Shop", 0.15)],
        "delivery_services": [("InPost Paczkomat", 0.65), ("DPD Poland", 0.25), ("Poczta Polska", 0.10)],
        "managers": ["Manager_A", "Manager_B", "Manager_C"],
        "statuses": [
            ("Completed",         0.87),
            ("New",               0.09),
            ("Awaiting Payment",  0.02),
            ("Cancelled",         0.02),
        ],
        "products": [
            ("Whey Protein Concentrate 1kg Vanilla",   89, 129),
            ("Whey Protein Concentrate 1kg Chocolate", 89, 129),
            ("Creatine Monohydrate 500g",              45,  69),
            ("Pre-Workout Energy Powder 300g",         59,  89),
            ("BCAA 2:1:1 Powder 400g",                 49,  74),
            ("Omega-3 Fish Oil 90 capsules",           29,  44),
            ("Magnesium Complex 60 caps",              24,  38),
            ("Vitamin D3+K2 60 caps",                  19,  32),
            ("Collagen Peptides 300g",                 54,  79),
            ("Shaker Bottle 700ml",                    14,  22),
            ("Gym Bag Medium",                         49,  74),
            ("Resistance Band Set 5pcs",               39,  59),
        ],
        "cities": [
            "Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan",
            "Gdansk", "Szczecin", "Bydgoszcz", "Lublin", "Katowice"
        ],
        "seasonal_peak_months": [1, 9],
        "seasonal_boost": 2.0,
        "quantity_single_prob": 0.70,
    },

    "SC3_PawNL": {
        "id": "SC3",
        "name": "PawNL B.V.",
        "country": "Netherlands",
        "currency": "EUR",
        "num_orders": 720,
        "start_date": datetime(2023, 7, 1),
        "end_date":   datetime(2026, 3, 31),
        "channels": [("Website", 0.68), ("Instagram", 0.22), ("Marktplaats", 0.10)],
        "delivery_services": [("PostNL", 0.70), ("DHL Netherlands", 0.20), ("DPD", 0.10)],
        "managers": ["Manager_A", "Manager_B"],
        "statuses": [
            ("Completed",        0.86),
            ("New",              0.09),
            ("Awaiting Review",  0.03),
            ("Returned",         0.02),
        ],
        "products": [
            ("Dog Collar Leather M",              18,  29),
            ("Dog Collar Leather L",              22,  34),
            ("Cat Scratching Post 60cm",          28,  44),
            ("Pet Feeding Mat Silicone",           9,  16),
            ("Orthopedic Dog Bed M",              44,  69),
            ("Orthopedic Dog Bed L",              62,  92),
            ("Automatic Pet Water Fountain",      29,  46),
            ("Stainless Steel Bowl Set",          14,  22),
            ("Retractable Dog Leash 5m",          16,  26),
            ("Interactive Cat Toy Wand",           8,  14),
            ("Dog Raincoat Size M",               24,  38),
            ("Travel Pet Carrier Bag",            38,  58),
        ],
        "cities": [
            "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
            "Tilburg", "Groningen", "Almere", "Breda", "Nijmegen"
        ],
        "seasonal_peak_months": [11, 12],
        "seasonal_boost": 2.0,
        "quantity_single_prob": 0.82,
    },
}

def weighted_choice(options):
    values, weights = zip(*options)
    r = random.random()
    cumulative = 0.0
    for v, w in zip(values, weights):
        cumulative += w
        if r <= cumulative:
            return v
    return values[-1]


def seasonal_weight(dt, peak_months, boost):
    if dt.month in peak_months:
        return boost
    elif dt.month in [m - 1 for m in peak_months if m > 1] + [m + 1 for m in peak_months if m < 12]:
        return 1.5
    else:
        return 0.8


def generate_orders(company):
    n = company["num_orders"]
    start = company["start_date"]
    end = company["end_date"]
    peak_months = company["seasonal_peak_months"]
    boost = company["seasonal_boost"]
    all_dates = []
    current = start
    while current <= end:
        w = seasonal_weight(current, peak_months, boost)
        if random.random() < w / (boost + 0.5):
            all_dates.append(current)
        current += timedelta(hours=random.randint(1, 12))

    if len(all_dates) < n:
        all_dates = all_dates * (n // len(all_dates) + 2)
    selected_dates = sorted(random.sample(all_dates, n))

    orders = []
    for i, order_date in enumerate(selected_dates):
        product_name, price_min, price_max = random.choice(company["products"])
        base_price = round(random.uniform(price_min, price_max) * 2) / 2  # round to 0.5
        quantity = 1 if random.random() < company["quantity_single_prob"] else random.randint(2, 3)
        total_price = round(base_price * quantity, 2)

        status = weighted_choice(company["statuses"])
        channel = weighted_choice(company["channels"])
        city = random.choice(company["cities"])
        delivery = weighted_choice(company["delivery_services"])
        manager = random.choice(company["managers"])

        delivery_date = None
        if status == "Completed":
            delivery_date = (order_date + timedelta(days=random.randint(1, 6))).strftime("%Y-%m-%d")

        orders.append({
            "order_id": f"{company['id']}-{str(i+1).zfill(5)}",
            "product_name": product_name,
            "quantity": quantity,
            f"price_{company['currency'].lower()}": total_price,
            "channel": channel,
            "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "manager": manager,
            "city": city,
            "country": company["country"],
            "delivery_service": delivery,
            "delivery_date": delivery_date,
        })

    return orders


def print_summary(company_def, orders):
    cid = company_def["id"]
    name = company_def["name"]
    currency = company_def["currency"]
    total = len(orders)
    completed = sum(1 for o in orders if o["status"] == "Completed")
    prices = [o[f"price_{currency.lower()}"] for o in orders]
    channels = {}
    for o in orders:
        channels[o["channel"]] = channels.get(o["channel"], 0) + 1

    print(f"\n── {cid} {name} ──")
    print(f"  Orders     : {total}")
    print(f"  Completed  : {completed} ({completed/total*100:.1f}%)")
    print(f"  Channels   : {', '.join(f'{k} {v}' for k,v in channels.items())}")
    print(f"  Price range: {min(prices):.2f} – {max(prices):.2f} {currency}")
    print(f"  Avg price  : {sum(prices)/len(prices):.2f} {currency}")
    print(f"  Date range : {orders[0]['order_date'][:10]} → {orders[-1]['order_date'][:10]}")


def save(company_key, company_def, orders):
    cid = company_def["id"].lower()

    meta = {
        "description": f"Synthetic CRM order export for {company_def['name']} — fictional data only",
        "company": company_def["name"],
        "country": company_def["country"],
        "currency": company_def["currency"],
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "total_records": len(orders),
    }

    json_path = f"synthetic_{cid}_orders.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "orders": orders}, f, ensure_ascii=False, indent=2)

    csv_path = f"synthetic_{cid}_orders.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=orders[0].keys())
        writer.writeheader()
        writer.writerows(orders)

    print(f"  Saved: {json_path}, {csv_path}")


def main():
    print("Generating synthetic CRM exports for 3 fictional companies...")
    for key, company_def in COMPANIES.items():
        orders = generate_orders(company_def)
        print_summary(company_def, orders)
        save(key, company_def, orders)
    print("\nDone.")


if __name__ == "__main__":
    main()
