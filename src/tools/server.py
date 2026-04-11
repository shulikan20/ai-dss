import json
import sqlite3
import os
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")
DB_PATH = os.path.join(os.path.dirname(__file__), "catalog.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
@app.route("/")
def index():
    return send_from_directory(".", "catalog_ui.html")

@app.route("/api/capabilities", methods=["GET"])
def get_capabilities():
    conn = get_db()
    rows = conn.execute("SELECT * FROM capabilities ORDER BY domain, name").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["bottleneck_keywords"] = json.loads(d["bottleneck_keywords"] or "[]")
        d["required_data_types"] = json.loads(d["required_data_types"] or "[]")
        d["secondary_outcomes"] = json.loads(d["secondary_outcomes"] or "[]")
        # attach product count
        count = conn.execute(
            "SELECT COUNT(*) FROM products WHERE capability_id=?", (d["capability_id"],)
        ).fetchone()[0]
        d["product_count"] = count
        result.append(d)
    conn.close()
    return jsonify(result)


@app.route("/api/capabilities", methods=["POST"])
def add_capability():
    data = request.json
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO capabilities (
                capability_id, name, domain, use_case_category, task_type_target,
                description, bottleneck_keywords,
                requires_historical_data, required_data_types,
                works_without_data, min_history_months_gate, min_technical_capability,
                primary_outcome, secondary_outcomes,
                time_to_value_weeks_min, time_to_value_weeks_max
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            data["capability_id"], data["name"], data["domain"],
            data.get("use_case_category", ""), data.get("task_type_target", ""),
            data.get("description", ""),
            json.dumps(data.get("bottleneck_keywords", [])),
            1 if data.get("required_data_types") else 0,
            json.dumps(data.get("required_data_types", [])),
            data.get("works_without_data", 1),
            data.get("min_history_months_gate") or None,
            data.get("min_technical_capability", 1),
            data.get("primary_outcome", ""),
            json.dumps(data.get("secondary_outcomes", [])),
            data.get("time_to_value_weeks_min") or None,
            data.get("time_to_value_weeks_max") or None,
        ])
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"ok": False, "error": "capability_id already exists"}), 400


@app.route("/api/capabilities/<cap_id>", methods=["PUT"])
def update_capability(cap_id):
    data = request.json
    conn = get_db()
    conn.execute("""
        UPDATE capabilities SET
            name=?, domain=?, use_case_category=?, task_type_target=?,
            description=?, bottleneck_keywords=?,
            requires_historical_data=?, required_data_types=?,
            works_without_data=?, min_history_months_gate=?, min_technical_capability=?,
            primary_outcome=?, secondary_outcomes=?,
            time_to_value_weeks_min=?, time_to_value_weeks_max=?
        WHERE capability_id=?
    """, [
        data["name"], data["domain"],
        data.get("use_case_category", ""), data.get("task_type_target", ""),
        data.get("description", ""),
        json.dumps(data.get("bottleneck_keywords", [])),
        1 if data.get("required_data_types") else 0,
        json.dumps(data.get("required_data_types", [])),
        data.get("works_without_data", 1),
        data.get("min_history_months_gate") or None,
        data.get("min_technical_capability", 1),
        data.get("primary_outcome", ""),
        json.dumps(data.get("secondary_outcomes", [])),
        data.get("time_to_value_weeks_min") or None,
        data.get("time_to_value_weeks_max") or None,
        cap_id,
    ])
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/capabilities/<cap_id>", methods=["DELETE"])
def delete_capability(cap_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE capability_id=?", (cap_id,))
    conn.execute("DELETE FROM capabilities WHERE capability_id=?", (cap_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/products", methods=["GET"])
def get_products():
    cap_id = request.args.get("capability_id")
    conn = get_db()
    if cap_id:
        rows = conn.execute(
            "SELECT * FROM products WHERE capability_id=? ORDER BY name", (cap_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY capability_id, name").fetchall()
    result = []
    for row in rows:
        d = dict(row)
        d["integrations"] = json.loads(d["integrations"] or "[]")
        result.append(d)
    conn.close()
    return jsonify(result)

@app.route("/api/products", methods=["POST"])
def add_product():
    data = request.json
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO products (
                product_id, capability_id, name, vendor, url,
                integrations, gdpr_compliant,
                deployment_model, pricing_model, has_free_tier, cost_tier, cost_notes,
                implementation_effort, min_technical_capability, setup_notes,
                min_history_months, min_record_count, works_with_limited_data,
                data_requirement_notes, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            data["product_id"], data["capability_id"], data["name"],
            data.get("vendor", ""), data.get("url", ""),
            json.dumps(data.get("integrations", [])),
            data.get("gdpr_compliant", 0),
            data.get("deployment_model", "saas"),
            data.get("pricing_model", "freemium"),
            data.get("has_free_tier", 0),
            data.get("cost_tier", "low"),
            data.get("cost_notes", ""),
            data.get("implementation_effort", "low"),
            data.get("min_technical_capability", 1),
            data.get("setup_notes", ""),
            data.get("min_history_months") or None,
            data.get("min_record_count") or None,
            data.get("works_with_limited_data", 1),
            data.get("data_requirement_notes", ""),
            data.get("notes", ""),
        ])
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"ok": False, "error": "product_id already exists"}), 400

@app.route("/api/products/<prod_id>", methods=["PUT"])
def update_product(prod_id):
    data = request.json
    conn = get_db()
    conn.execute("""
        UPDATE products SET
            capability_id=?, name=?, vendor=?, url=?,
            integrations=?, gdpr_compliant=?,
            deployment_model=?, pricing_model=?, has_free_tier=?, cost_tier=?, cost_notes=?,
            implementation_effort=?, min_technical_capability=?, setup_notes=?,
            min_history_months=?, min_record_count=?, works_with_limited_data=?,
            data_requirement_notes=?, notes=?
        WHERE product_id=?
    """, [
        data["capability_id"], data["name"],
        data.get("vendor", ""), data.get("url", ""),
        json.dumps(data.get("integrations", [])),
        data.get("gdpr_compliant", 0),
        data.get("deployment_model", "saas"),
        data.get("pricing_model", "freemium"),
        data.get("has_free_tier", 0),
        data.get("cost_tier", "low"),
        data.get("cost_notes", ""),
        data.get("implementation_effort", "low"),
        data.get("min_technical_capability", 1),
        data.get("setup_notes", ""),
        data.get("min_history_months") or None,
        data.get("min_record_count") or None,
        data.get("works_with_limited_data", 1),
        data.get("data_requirement_notes", ""),
        data.get("notes", ""),
        prod_id,
    ])
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/products/<prod_id>", methods=["DELETE"])
def delete_product(prod_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE product_id=?", (prod_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    cap_count = conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0]
    prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    by_domain = conn.execute(
        "SELECT domain, COUNT(*) n FROM capabilities GROUP BY domain ORDER BY domain"
    ).fetchall()
    conn.close()
    return jsonify({
        "capabilities": cap_count,
        "products": prod_count,
        "by_domain": [{"domain": r[0], "count": r[1]} for r in by_domain]
    })

if __name__ == "__main__":
    print("\n  AI-DSS Catalog Editor")
    print("  ─────────────────────────────────")
    print("  Open in browser: http://localhost:5050")
    print("  Database:        catalog.db")
    print("  Press Ctrl+C to stop\n")
    app.run(debug=False, port=5050)
