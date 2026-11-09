"""llm-triage-pipeline: classify, extract and summarise documents with an LLM, safely.

Usage:
    python run.py      # runs all three backends offline and writes reports/report.md

Backends compared:
    1. recorded Claude outputs (clean replay)
    2. the same outputs with fault injection (tests validation, retries and refusal logging)
    3. a keyword baseline
"""

import datetime
import json
import pathlib
from collections import Counter
from typing import Any

from backends import KeywordBackend, ReplayBackend
from pipeline import TOPICS, Backend, process

ROOT = pathlib.Path(__file__).resolve().parent


def load_docs() -> list[dict[str, Any]]:
    with open(ROOT / "data" / "documents.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def _acc(rows: list[dict[str, Any]]) -> float | None:
    return sum(r["correct"] for r in rows) / len(rows) if rows else None


def summarise(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    status = Counter(r["status"] for r in results)
    return {
        "n": n,
        "valid_first_try": status["ok"],
        "ok_after_retry": status["ok_after_retry"],
        "failed": status["failed"],
        "refused": status["refused"],
        "retries": sum(r["attempts"] - 1 for r in results),
        "accuracy": sum(r["correct"] for r in results) / n,
        "dev": _acc([r for r in results if r["split"] == "dev"]),
        "heldout": _acc([r for r in results if r["split"] == "heldout"]),
        "errors": Counter(e for r in results for e in r["errors"]),
    }


def build_report(docs: list[dict[str, Any]], runs: dict[str, Any]) -> str:
    by_id = {d["doc_id"]: d for d in docs}
    lines = ["# LLM triage pipeline report", "",
             f"{len(docs)} documents, {len(TOPICS)} topics. Generated {datetime.datetime.now():%Y-%m-%d %H:%M}.", "",
             "## Comparison", "",
             "| Backend | Valid first try | Valid after retry | Failed | Refused | Retries | Accuracy (dev) | Accuracy (held-out) |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for name, results in runs.items():
        s = summarise(results)
        lines.append(f"| {name} | {s['valid_first_try']} | {s['ok_after_retry']} | {s['failed']} | {s['refused']} | "
                     f"{s['retries']} | {s['dev']:.0%} | {s['heldout']:.0%} |")
    lines += ["", "The keyword baseline's lists were written while looking at the 24 dev documents, so its dev score is "
              "inflated by overfitting. The 8 held-out documents were written afterwards and never used to tune it; "
              "that column is the fair comparison."]

    lines += ["", "## Errors caught by the validator", ""]
    for name, results in runs.items():
        errs = summarise(results)["errors"]
        if errs:
            lines.append(f"- **{name}:** " + ", ".join(f"{k} ({v})" for k, v in errs.most_common()))
    lines += ["", "## Over-refusal log", "",
              "Every document in this set is a legitimate news snippet, so any refusal is an over-refusal."]
    any_refusal = False
    for name, results in runs.items():
        for r in results:
            if "refusal" in r["errors"]:
                any_refusal = True
                lines.append(f"- **{r['doc_id']} / {name}:** refused on attempt 1, final status `{r['status']}`. "
                             f"Text: \"{by_id[r['doc_id']]['text']}\"")
    if not any_refusal:
        lines.append("- None.")

    lines += ["", "## Misclassifications", ""]
    for name, results in runs.items():
        wrong = [r for r in results if r["output"] and not r["correct"]]
        lines.append(f"**{name}:** {len(wrong)} wrong")
        for r in wrong:
            lines.append(f"- {r['doc_id']}: said `{r['output']['topic']}`, gold `{by_id[r['doc_id']]['gold_topic']}` "
                         f"(confidence {r['output']['confidence']}). \"{by_id[r['doc_id']]['text']}\"")
        lines.append("")

    lines += ["## Notes", "",
              "- The Claude outputs were produced by Claude in a chat session on 2026-11-04 and replayed offline. "
              "The fault-injection attempts are hand-written, not model output.",
              "- Gold topics were assigned when the snippets were written. Some snippets genuinely span two topics "
              "(e.g. hospitals running on generators), and low model confidence on those is a useful signal for "
              "human review.",
              "- 32 documents is a demonstration, not a benchmark."]
    return "\n".join(lines)


def main() -> None:
    docs = load_docs()
    rec = ROOT / "recorded" / "claude_2026-11-04.jsonl"
    backends: list[Backend] = [ReplayBackend(rec), ReplayBackend(rec, ROOT / "recorded" / "fault_injection.jsonl"), KeywordBackend()]
    runs: dict[str, list[dict[str, Any]]] = {}
    (ROOT / "logs").mkdir(exist_ok=True)
    with open(ROOT / "logs" / "run_log.jsonl", "w", encoding="utf-8") as log:
        for backend in backends:
            runs[backend.name] = [{**process(doc, backend), "split": doc["split"]} for doc in docs]
            for r in runs[backend.name]:
                log.write(json.dumps(r) + "\n")
    (ROOT / "reports").mkdir(exist_ok=True)
    report = build_report(docs, runs)
    (ROOT / "reports" / "report.md").write_text(report, encoding="utf-8")
    print("\n".join(report.splitlines()[:10]))
    print(f"\nFull report: {ROOT / 'reports' / 'report.md'}")


if __name__ == "__main__":
    main()
