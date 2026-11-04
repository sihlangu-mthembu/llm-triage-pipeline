# LLM triage pipeline report

32 documents, 6 topics. Generated 2026-11-04 21:07.

## Comparison

| Backend | Valid first try | Valid after retry | Failed | Refused | Retries | Accuracy (dev) | Accuracy (held-out) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-5-5 (chat, recorded 2026-11-04) | 32 | 0 | 0 | 0 | 0 | 96% | 100% |
| claude-opus-5-5 (chat, recorded 2026-11-04) + fault injection | 27 | 5 | 0 | 0 | 6 | 96% | 100% |
| keyword baseline | 32 | 0 | 0 | 0 | 0 | 100% | 12% |

The keyword baseline's lists were written while looking at the 24 dev documents, so its dev score is inflated by overfitting. The 8 held-out documents were written afterwards and never used to tune it; that column is the fair comparison.

## Errors caught by the validator

- **claude-opus-5-5 (chat, recorded 2026-11-04) + fault injection:** summary_too_long (2), invalid_json (1), refusal (1), invalid_topic (1), missing_field (1)

## Over-refusal log

Every document in this set is a legitimate news snippet, so any refusal is an over-refusal.
- **d07 / claude-opus-5-5 (chat, recorded 2026-11-04) + fault injection:** refused on attempt 1, final status `ok_after_retry`. Text: "A study of overdose admissions at an urban emergency unit found that most involved prescription painkillers combined with alcohol."

## Misclassifications

**claude-opus-5-5 (chat, recorded 2026-11-04):** 1 wrong
- d18: said `governance`, gold `crime_safety` (confidence 0.55). "Residents blocked roads with burning tyres during a protest over service delivery, and police used rubber bullets to disperse the crowd."

**claude-opus-5-5 (chat, recorded 2026-11-04) + fault injection:** 1 wrong
- d18: said `governance`, gold `crime_safety` (confidence 0.55). "Residents blocked roads with burning tyres during a protest over service delivery, and police used rubber bullets to disperse the crowd."

**keyword baseline:** 7 wrong
- d26: said `economy`, gold `health` (confidence 0.0). "A new TB testing van will visit farming communities in the Northern Cape every fortnight."
- d27: said `economy`, gold `education` (confidence 0.0). "Early childhood development centres say subsidy payments are three months late, threatening staff salaries."
- d28: said `economy`, gold `energy` (confidence 0.0). "The national transmission company's new line will connect wind farms in the Eastern Cape to Gauteng."
- d29: said `economy`, gold `crime_safety` (confidence 0.0). "Shopkeepers in the CBD hired private security after a spate of armed robberies."
- d30: said `economy`, gold `governance` (confidence 0.0). "The mayor survived a motion of no confidence after two smaller parties abstained."
- d31: said `economy`, gold `health` (confidence 0.0). "Pharmacies report shortages of insulin pens as a supplier faces import delays."
- d32: said `economy`, gold `energy` (confidence 0.0). "Petrol stations in rural towns ran dry after a pipeline maintenance shutdown."

## Notes

- The Claude outputs were produced by Claude in a chat session on 2026-11-04 and replayed offline. The fault-injection attempts are hand-written, not model output.
- Gold topics were assigned when the snippets were written. Some snippets genuinely span two topics (e.g. hospitals running on generators), and low model confidence on those is a useful signal for human review.
- 32 documents is a demonstration, not a benchmark.