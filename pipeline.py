"""Core pipeline: send each document to a model backend, validate the output, retry on failure.

A backend is any object with  .name  and  .attempt(doc, attempt_number) -> str  (the raw model text).
"""

import json
import re

TOPICS = ["economy", "health", "education", "energy", "crime_safety", "governance"]
MAX_SUMMARY_WORDS = 30
MAX_ATTEMPTS = 3

PROMPT = (
    "Classify this news snippet. Reply with JSON only, using exactly these keys: "
    '"topic" (one of: ' + ", ".join(TOPICS) + '), "entities" (list of named organisations, places or brands), '
    f'"summary" (one sentence, at most {MAX_SUMMARY_WORDS} words) and "confidence" (number from 0 to 1).\n\nSnippet: '
)

REFUSAL_PATTERNS = [r"\bi'?m sorry\b", r"\bi can'?t help\b", r"\bi cannot (?:help|assist)\b", r"\bunable to assist\b"]


def looks_like_refusal(raw):
    lowered = raw.lower()
    return any(re.search(p, lowered) for p in REFUSAL_PATTERNS)


def validate(raw):
    """Return (parsed_output, None) if valid, else (None, error_code)."""
    if looks_like_refusal(raw):
        return None, "refusal"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(data, dict):
        return None, "invalid_json"
    for key in ("topic", "entities", "summary", "confidence"):
        if key not in data:
            return None, "missing_field"
    if data["topic"] not in TOPICS:
        return None, "invalid_topic"
    if not isinstance(data["entities"], list) or not all(isinstance(e, str) for e in data["entities"]):
        return None, "bad_entities"
    if not isinstance(data["summary"], str) or len(data["summary"].split()) > MAX_SUMMARY_WORDS:
        return None, "summary_too_long"
    if not isinstance(data["confidence"], (int, float)) or not 0 <= data["confidence"] <= 1:
        return None, "bad_confidence"
    return data, None


def process(doc, backend):
    """Run one document through the backend with retries. Returns a result record."""
    errors = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = backend.attempt(doc, attempt)
        data, error = validate(raw)
        if data:
            status = "ok" if attempt == 1 else "ok_after_retry"
            return {"doc_id": doc["doc_id"], "backend": backend.name, "status": status, "attempts": attempt,
                    "errors": errors, "output": data, "correct": data["topic"] == doc["gold_topic"]}
        errors.append(error)
    status = "refused" if errors and all(e == "refusal" for e in errors) else "failed"
    return {"doc_id": doc["doc_id"], "backend": backend.name, "status": status, "attempts": MAX_ATTEMPTS,
            "errors": errors, "output": None, "correct": False}
