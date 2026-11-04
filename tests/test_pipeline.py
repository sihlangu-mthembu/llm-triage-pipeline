import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline import process, validate  # noqa: E402

GOOD = json.dumps({"topic": "energy", "entities": [], "summary": "Short summary.", "confidence": 0.9})
DOC = {"doc_id": "x1", "gold_topic": "energy", "text": "Load-shedding this weekend."}


class FakeBackend:
    name = "fake"

    def __init__(self, outputs):
        self.outputs = outputs

    def attempt(self, doc, attempt_number):
        return self.outputs[min(attempt_number, len(self.outputs)) - 1]


class ValidateTests(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate(GOOD)[1])

    def test_error_codes(self):
        cases = {
            '{"topic": "energy"': "invalid_json",
            '{"topic": "energy", "summary": "x", "confidence": 1}': "missing_field",
            '{"topic": "sport", "entities": [], "summary": "x", "confidence": 1}': "invalid_topic",
            '{"topic": "energy", "entities": [], "summary": "x", "confidence": 7}': "bad_confidence",
            "I'm sorry, but I can't help with that.": "refusal",
        }
        for raw, code in cases.items():
            self.assertEqual(validate(raw)[1], code, raw)

    def test_long_summary(self):
        raw = json.dumps({"topic": "energy", "entities": [], "summary": "word " * 40, "confidence": 0.5})
        self.assertEqual(validate(raw)[1], "summary_too_long")


class RetryTests(unittest.TestCase):
    def test_recovers_after_retry(self):
        r = process(DOC, FakeBackend(["not json", GOOD]))
        self.assertEqual((r["status"], r["attempts"], r["errors"]), ("ok_after_retry", 2, ["invalid_json"]))

    def test_fails_after_max_attempts(self):
        r = process(DOC, FakeBackend(["not json"]))
        self.assertEqual(r["status"], "failed")

    def test_persistent_refusal(self):
        r = process(DOC, FakeBackend(["I'm sorry, I can't help with that."]))
        self.assertEqual(r["status"], "refused")


if __name__ == "__main__":
    unittest.main()
