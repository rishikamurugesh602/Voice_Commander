"""
db_service.py
All SQLite database operations for EchoCart.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "shopping.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
DATA_DIR = os.path.join(BASE_DIR, "data")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()

    cur = conn.execute("SELECT COUNT(*) as count FROM products")
    if cur.fetchone()["count"] == 0:
        _seed_products(conn)
        _seed_purchase_history(conn)

    conn.close()


def _seed_products(conn):
    with open(os.path.join(DATA_DIR, "products.json"), "r") as f:
        products = json.load(f)
    for p in products:
        conn.execute(
            "INSERT INTO products (name, brand, category, price, unit) VALUES (?, ?, ?, ?, ?)",
            (p["name"], p["brand"], p["category"], p["price"], p["unit"])
        )
    conn.commit()


def _seed_purchase_history(conn):
    today = datetime.now()
    history = [
        ("Milk", 1, 2), ("Milk", 1, 5), ("Milk", 1, 8), ("Milk", 1, 11),
        ("Bread", 1, 3), ("Bread", 1, 9),
        ("Bananas", 1, 1), ("Bananas", 1, 6),
        ("Eggs", 1, 4), ("Eggs", 1, 10),
    ]
    for name, qty, days_ago in history:
        purchased_at = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO purchase_history (product_name, quantity, purchased_at) VALUES (?, ?, ?)",
            (name, qty, purchased_at)
        )
    conn.commit()


def get_shopping_list():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM shopping_list ORDER BY category, added_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_item(product_name, category, quantity=1):
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM shopping_list WHERE LOWER(product_name) = LOWER(?)",
        (product_name,)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE shopping_list SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO shopping_list (product_name, category, quantity) VALUES (?, ?, ?)",
            (product_name, category, quantity)
        )
    conn.commit()
    conn.close()


def remove_item(product_name):
    conn = get_connection()
    conn.execute("DELETE FROM shopping_list WHERE LOWER(product_name) = LOWER(?)", (product_name,))
    conn.commit()
    conn.close()


def update_quantity(product_name, new_quantity):
    conn = get_connection()
    conn.execute(
        "UPDATE shopping_list SET quantity = ? WHERE LOWER(product_name) = LOWER(?)",
        (new_quantity, product_name)
    )
    conn.commit()
    conn.close()


def search_products(query=None, brand=None, max_price=None):
    conn = get_connection()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []

    if query:
        sql += " AND LOWER(name) LIKE ?"
        params.append(f"%{query.lower()}%")
    if brand:
        sql += " AND LOWER(brand) LIKE ?"
        params.append(f"%{brand.lower()}%")
    if max_price:
        sql += " AND price <= ?"
        params.append(max_price)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_for_product(product_name):
    conn = get_connection()
    row = conn.execute(
        "SELECT category FROM products WHERE LOWER(name) LIKE ? LIMIT 1",
        (f"%{product_name.lower()}%",)
    ).fetchone()
    conn.close()
    return row["category"] if row else "Other"


def get_purchase_history():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchase_history ORDER BY purchased_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_command(raw_transcript, intent, entities, success=True):
    conn = get_connection()
    conn.execute(
        "INSERT INTO command_history (raw_transcript, detected_intent, detected_entities, success) VALUES (?, ?, ?, ?)",
        (raw_transcript, intent, json.dumps(entities), int(success))
    )
    conn.commit()
    conn.close()


def get_recent_commands(limit=10):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM command_history ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["detected_entities"] = json.loads(d["detected_entities"]) if d["detected_entities"] else {}
        result.append(d)
    return result