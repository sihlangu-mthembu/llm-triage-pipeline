# llm-triage-pipeline

![tests](https://github.com/sihlangu-mthembu/llm-triage-pipeline/actions/workflows/tests.yml/badge.svg)

A small Python pipeline that uses an LLM to **classify, extract entities from and summarise** a batch of documents, and that is built around the ways LLM pipelines fail silently: malformed JSON, missing fields, invented categories, over-long outputs and refusals of legitimate requests.

Every output is validated against a schema. Bad outputs are retried up to three times, and every error and refusal is logged. Accuracy is measured against hand-assigned labels and compared with a simple keyword baseline.

It runs fully offline, with **no API key**.

## Quick start

Needs Python 3.10 or newer. No packages to install.

```bash
python run.py                      # runs all three backends, writes reports/report.md and logs/run_log.jsonl
python -m unittest discover tests  # run the tests
```

## How it works

1. **Prompt:** each document goes to the model with a fixed instruction to return JSON with `topic` (one of six), `entities`, a one-sentence `summary` (max 30 words) and a `confidence` from 0 to 1.
2. **Validate:** `pipeline.validate()` checks that the output is JSON, has every field, uses an allowed topic, keeps the summary short and gives a confidence between 0 and 1. It also detects refusals.
3. **Retry:** an invalid output is retried, up to 3 attempts. Each document ends as `ok`, `ok_after_retry`, `failed` or `refused`.
4. **Log and report:** every attempt's errors go to `logs/run_log.jsonl`. The report compares backends, lists every error the validator caught, logs every over-refusal, and lists every misclassification.

## Backends

| Backend | What it is |
| --- | --- |
| Recorded Claude outputs | Real outputs produced by Claude (Opus 5.5) in a chat session on 4 November 2026, given the same prompt, then replayed offline |
| Recorded Claude + fault injection | The same outputs, but 5 documents first return hand-written bad attempts: broken JSON, a refusal, an invalid topic, an over-long summary and a missing field |
| Keyword baseline | Counts topic keywords. Always returns valid JSON |

A new backend only needs a `name` and an `attempt(doc, attempt_number)` method returning the raw model text, so a live API backend can be added without changing the pipeline.

## Results

| Backend | Valid first try | Valid after retry | Failed | Accuracy (dev, 24) | Accuracy (held-out, 8) |
| --- | --- | --- | --- | --- | --- |
| Recorded Claude | 32 | 0 | 0 | 96% | 100% |
| Recorded Claude + fault injection | 27 | 5 | 0 | 96% | 100% |
| Keyword baseline | 32 | 0 | 0 | 100% | 12% |

What the results show:

- **The validator and retries work.** All five injected faults were caught and recovered within three attempts, including an over-long summary that took two retries.
- **Over-refusal is logged.** The injected refusal of a legitimate public-health snippet about overdose admissions shows up in the over-refusal log, with the document text, for review.
- **The baseline's 100% is overfitting.** Its keyword lists were written while looking at the 24 "dev" documents. On 8 held-out documents written afterwards it scores 12%, mostly defaulting to `economy` when it finds no keywords. The held-out column is the fair comparison, and the gap is a small example of why you always evaluate on data you didn't tune on.
- **The LLM's one error is a genuinely ambiguous case.** It labelled a violent service-delivery protest as `governance` (gold: `crime_safety`) with low confidence (0.55). Low confidence is a useful signal for routing items to human review.

## About the data

- **Documents:** 32 short, **fictional** South African news-style snippets written for this project. They name no real people and are not real reports.
- **Gold labels:** assigned when the snippets were written. Some snippets genuinely span two topics (hospitals running on generators: energy or health?).
- **Recorded outputs:** produced by Claude, the same model family that helped write the documents. That could make it look better than an unrelated model would.
- **Fault-injection attempts:** hand-written, not model output.

## Limitations

- 32 documents is a demonstration, not a benchmark.
- Entity extraction is validated for format, not scored for accuracy.
- Refusal detection is pattern-based and would miss politely worded partial refusals.

## Project structure

```
llm-triage-pipeline/
├── run.py            # runs the backends and writes the report and log
├── pipeline.py       # prompt, validation, retry logic
├── backends.py       # replay, fault-injection and keyword backends
├── build_data.py     # writes the documents, recorded outputs and fault cases
├── data/documents.jsonl
├── recorded/         # claude_2026-11-04.jsonl, fault_injection.jsonl
├── reports/report.md
├── logs/run_log.jsonl
└── tests/test_pipeline.py
```

## Author

Sihlangu Mthembu, AI evaluation and data analysis. Economics & Politics, University of Cape Town.
