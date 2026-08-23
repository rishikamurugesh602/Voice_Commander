"""
command_handler.py
--------------------
Orchestrates the full command pipeline: NLU -> validation -> DB action -> logging.
This is the ONLY file that connects nlu_engine.py to db_service.py.
"""

import json
from services import db_service
from services import nlu_engine


def execute(raw_text):
    """
    Main entry point. Takes raw text (from typed input or voice transcript),
    runs it through NLU, executes the resulting action, logs it, and
    returns a UI-ready result dict:
    {
        "success": bool,
        "message": str,        # human-readable feedback for the UI
        "intent": str,
        "data": list | None,   # search results, if applicable
    }
    """
    parsed = nlu_engine.parse_command(raw_text)
    intent = parsed["intent"]
    item = parsed["item"]

    # No intent recognized at all -> can't proceed
    if not intent:
        result = {
            "success": False,
            "message": "Sorry, I didn't understand that command. Try something like 'Add milk' or 'Find toothpaste'.",
            "intent": None,
            "data": None,
        }
        db_service.log_command(raw_text, None, parsed, success=False)
        return result

    # Route to the correct handler based on intent
    handler_map = {
        "ADD": _handle_add,
        "REMOVE": _handle_remove,
        "UPDATE": _handle_update,
        "SEARCH": _handle_search,
        "SUBSTITUTE": _handle_substitute,
    }

    handler_fn = handler_map.get(intent)
    result = handler_fn(parsed)

    # Log every executed command for the "Recent Commands" panel + debugging
    db_service.log_command(raw_text, intent, parsed, success=result["success"])

    return result


def _handle_add(parsed):
    item = parsed["item"]
    quantity = parsed["quantity"]

    if not item:
        return {
            "success": False,
            "message": "I couldn't figure out which item to add. Please try again.",
            "intent": "ADD",
            "data": None,
        }

    category = db_service.get_category_for_product(item)
    db_service.add_item(item, category, quantity)

    return {
        "success": True,
        "message": f"Added {quantity} {item} to your list.",
        "intent": "ADD",
        "data": db_service.get_shopping_list(),
    }


def _handle_remove(parsed):
    item = parsed["item"]

    if not item:
        return {
            "success": False,
            "message": "I couldn't figure out which item to remove. Please try again.",
            "intent": "REMOVE",
            "data": None,
        }

    current_list = db_service.get_shopping_list()
    exists = any(i["product_name"].lower() == item.lower() for i in current_list)

    if not exists:
        return {
            "success": False,
            "message": f"{item} isn't on your list.",
            "intent": "REMOVE",
            "data": current_list,
        }

    db_service.remove_item(item)

    return {
        "success": True,
        "message": f"Removed {item} from your list.",
        "intent": "REMOVE",
        "data": db_service.get_shopping_list(),
    }


def _handle_update(parsed):
    item = parsed["item"]
    quantity = parsed["quantity"]

    if not item:
        return {
            "success": False,
            "message": "I couldn't figure out which item to update. Please try again.",
            "intent": "UPDATE",
            "data": None,
        }

    current_list = db_service.get_shopping_list()
    exists = any(i["product_name"].lower() == item.lower() for i in current_list)

    if not exists:
        return {
            "success": False,
            "message": f"{item} isn't on your list yet. Try adding it first.",
            "intent": "UPDATE",
            "data": current_list,
        }

    db_service.update_quantity(item, quantity)

    return {
        "success": True,
        "message": f"Updated {item} to {quantity}.",
        "intent": "UPDATE",
        "data": db_service.get_shopping_list(),
    }


def _handle_search(parsed):
    item = parsed["item"]
    brand = parsed["brand"]
    max_price = parsed["max_price"]

    results = db_service.search_products(query=item, brand=brand, max_price=max_price)

    if not results:
        return {
            "success": False,
            "message": f"No products found matching your search.",
            "intent": "SEARCH",
            "data": [],
        }

    return {
        "success": True,
        "message": f"Found {len(results)} product(s).",
        "intent": "SEARCH",
        "data": results,
    }


def _handle_substitute(parsed):
    item = parsed["item"]

    if not item:
        return {
            "success": False,
            "message": "I couldn't figure out which item you want alternatives for.",
            "intent": "SUBSTITUTE",
            "data": None,
        }

    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sub_path = os.path.join(base_dir, "data", "substitutions.json")

    with open(sub_path, "r") as f:
        substitutions = json.load(f)

    alternatives = substitutions.get(item.lower(), [])

    if not alternatives:
        return {
            "success": False,
            "message": f"No alternatives found for {item}.",
            "intent": "SUBSTITUTE",
            "data": [],
        }

    return {
        "success": True,
        "message": f"Alternatives for {item}: {', '.join(alternatives)}.",
        "intent": "SUBSTITUTE",
        "data": alternatives,
    }