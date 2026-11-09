"""Model backends. No API keys needed: both run offline."""

import json
import re
from pathlib import Path

from pipeline import TOPICS


class ReplayBackend:
    """Replays recorded LLM outputs. Optional fault injection serves hand-written bad attempts first."""

    def __init__(self, recorded_path: Path, fault_path: Path | None = None) -> None:
        self.recorded = {}
        with open(recorded_path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                self.recorded[row["doc_id"]] = row["raw"]
                self.model = row["model"]
        self.faults = {}
        if fault_path:
            with open(fault_path, encoding="utf-8") as fh:
                for line in fh:
                    row = json.loads(line)
                    self.faults[row["doc_id"]] = row["attempts"]
        suffix = " + fault injection" if fault_path else ""
        self.name = f"{self.model}{suffix}"

    def attempt(self, doc: dict[str, str], attempt_number: int) -> str:
        bad = self.faults.get(doc["doc_id"], [])
        if attempt_number <= len(bad):
            return bad[attempt_number - 1]
        return self.recorded[doc["doc_id"]]


KEYWORDS = {
    "economy": ["rand", "interest rate", "inflation", "retail", "sales", "business", "price", "credit", "economists"],
    "health": ["health", "hospital", "clinic", "measles", "vaccination", "nurses", "overdose", "medication"],
    "education": ["school", "matric", "university", "universities", "student", "teacher", "learners", "classroom"],
    "energy": ["load-shedding", "power", "solar", "grid", "generator", "outage", "mw", "utility"],
    "crime_safety": ["police", "hijack", "theft", "crime", "policing", "suspicious", "rubber bullets"],
    "governance": ["auditor-general", "parliament", "committee", "council", "electoral", "budget", "municipalit", "board"],
}


class KeywordBackend:
    """A deliberately simple baseline: count topic keywords. Always returns valid JSON."""

    name = "keyword baseline"

    def attempt(self, doc: dict[str, str], attempt_number: int) -> str:
        text = doc["text"].lower()
        scores = {t: sum(text.count(k) for k in words) for t, words in KEYWORDS.items()}
        topic = max(TOPICS, key=lambda t: scores[t])
        total = sum(scores.values())
        entities = re.findall(r"\b[A-Z][a-z]+(?:[- ][A-Z][a-z]+)*\b", doc["text"])[1:]
        summary = " ".join(doc["text"].split()[:25])
        return json.dumps({"topic": topic, "entities": entities, "summary": summary,
                           "confidence": round(scores[topic] / total, 2) if total else 0.0})
