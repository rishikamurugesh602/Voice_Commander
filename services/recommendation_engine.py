"""
recommendation_engine.py
--------------------------
Rule-based suggestions: frequency-based "running low" alerts + seasonal picks.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from services import db_service

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEASONAL_PATH = os.path.join(BASE_DIR, "data", "seasonal.json")


def get_frequency_suggestions(max_suggestions=4):
    """
    Look at purchase history. For items bought 2+ times, calculate the
    average gap between purchases. If it's been longer than that average
    since the last purchase, suggest it (classic 'running low' logic).
    Skip items already on the current shopping list.
    """
    history = db_service.get_purchase_history()
    if not history:
        return []

    # Group purchase dates by product
    purchases_by_item = defaultdict(list)
    for record in history:
        date = datetime.strptime(record["purchased_at"], "%Y-%m-%d")
        purchases_by_item[record["product_name"]].append(date)

    current_list_items = {
        item["product_name"].lower() for item in db_service.get_shopping_list()
    }

    suggestions = []
    today = datetime.now()

    for item, dates in purchases_by_item.items():
        if item.lower() in current_list_items:
            continue  # already on the list, no need to suggest

        dates.sort()
        if len(dates) < 2:
            continue  # not enough history to establish a pattern

        # Average gap between consecutive purchases
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        avg_gap = sum(gaps) / len(gaps)

        days_since_last = (today - dates[-1]).days

        if days_since_last >= avg_gap:
            suggestions.append({
                "item": item,
                "reason": f"You're running low on {item}",
                "days_since_last": days_since_last,
            })

    # Most overdue first
    suggestions.sort(key=lambda s: s["days_since_last"], reverse=True)
    return suggestions[:max_suggestions]


def get_seasonal_suggestions(max_suggestions=4):
    """Return in-season items for the current month, excluding items already on the list."""
    with open(SEASONAL_PATH, "r") as f:
        seasonal_data = json.load(f)

    current_month = str(datetime.now().month)
    seasonal_items = seasonal_data.get(current_month, [])

    current_list_items = {
        item["product_name"].lower() for item in db_service.get_shopping_list()
    }

    filtered = [item for item in seasonal_items if item.lower() not in current_list_items]
    return filtered[:max_suggestions]


def get_all_suggestions():
    """Combined suggestions payload for the UI."""
    return {
        "frequency": get_frequency_suggestions(),
        "seasonal": get_seasonal_suggestions(),
    }