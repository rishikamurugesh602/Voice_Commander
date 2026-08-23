"""
nlu_engine.py
--------------
Rule-based Natural Language Understanding for voice/text commands.
Converts raw text -> {intent, entities} structured data.
"""

import re
from rapidfuzz import process, fuzz
from services import db_service

FILLER_WORDS = [
    "please", "can you", "could you", "i want to", "i would like to",
    "i want", "i need to", "kindly"
]

WORD_TO_NUMBER = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

INTENT_PATTERNS = [
    ("REMOVE", [r"\bremove\b", r"\bdelete\b", r"\btake off\b", r"\bcancel\b"]),
    ("UPDATE", [r"\bchange\b", r"\bupdate\b", r"\bmake it\b", r"\bset\b.*\bto\b"]),
    ("SUBSTITUTE", [r"\balternative", r"\bsubstitute", r"\breplace", r"\binstead of\b"]),
    ("SEARCH", [r"\bfind\b", r"\bsearch\b", r"\blook for\b", r"\bshow me\b"]),
    ("ADD", [r"\badd\b", r"\bbuy\b", r"\bget\b", r"\bput\b.*\bon\b", r"\bneed\b"]),
]


def normalize(text):
    text = text.lower().strip()
    for filler in FILLER_WORDS:
        text = text.replace(filler, "")
    return " ".join(text.split())


def detect_intent(text):
    for intent, patterns in INTENT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text):
                return intent
    return None


def extract_quantity(text, intent=None, has_price_filter=False):
    if intent in ("SEARCH", "SUBSTITUTE") or has_price_filter:
        return 1

    digit_match = re.search(r"\b(\d+)\b", text)
    if digit_match:
        return int(digit_match.group(1))

    for word, number in WORD_TO_NUMBER.items():
        if re.search(rf"\b{word}\b", text):
            return number

    return 1


def extract_max_price(text):
    match = re.search(r"under\s+(?:rs\.?|rupees|₹)?\s*(\d+)", text)
    if match:
        return float(match.group(1))
    return None


def extract_brand(text):
    conn_products = db_service.search_products()
    known_brands = set(p["brand"].lower() for p in conn_products if p.get("brand"))
    for brand in known_brands:
        if brand in text:
            return brand
    return None


def extract_item(text, intent):
    cleaned = re.sub(r"\b\d+\b", "", text)
    noise_words = [
        "bottles", "bottle", "of", "to", "my", "list", "shopping",
        "the", "a", "an", "on", "for", "under", "rupees", "rs"
    ]
    for intent_name, patterns in INTENT_PATTERNS:
        for p in patterns:
            cleaned = re.sub(p, "", cleaned)
    for word in noise_words:
        cleaned = re.sub(rf"\b{word}\b", "", cleaned)
    for word in WORD_TO_NUMBER:
        cleaned = re.sub(rf"\b{word}\b", "", cleaned)

    cleaned = " ".join(cleaned.split()).strip()

    if not cleaned:
        return None

    products = db_service.search_products()
    product_names = list(set(p["name"] for p in products))

    if not product_names:
        return cleaned

    for name in product_names:
        if name.lower() == cleaned.lower():
            return name

    last_word = cleaned.split()[-1] if cleaned.split() else cleaned
    for name in product_names:
        if name.lower() == last_word.lower():
            return name

    best_match = process.extractOne(cleaned, product_names, scorer=fuzz.WRatio)
    if best_match and best_match[1] >= 60:
        return best_match[0]

    return cleaned


def parse_command(raw_text):
    normalized = normalize(raw_text)
    intent = detect_intent(normalized)
    max_price = extract_max_price(normalized)

    result = {
        "raw_text": raw_text,
        "intent": intent,
        "item": None,
        "quantity": extract_quantity(normalized, intent=intent, has_price_filter=(max_price is not None)),
        "max_price": max_price,
        "brand": extract_brand(normalized),
        "success": intent is not None,
    }

    if intent:
        result["item"] = extract_item(normalized, intent)

    return result