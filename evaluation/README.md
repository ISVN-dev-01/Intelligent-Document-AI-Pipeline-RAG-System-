# Lightweight RAG evaluation

Ingest exactly the three supplied PDFs into a fresh corpus, then run:

```bash
python scripts/evaluate.py --output evaluation/results.json
```

The command prompts for admin authentication and records all evaluation queries in the normal audit database. Google mode makes real provider requests. For a cost-free, reproducible baseline, run `python scripts/smoke_demo.py`; it builds a fresh isolated corpus and uses the deterministic hash/excerpt providers.

The eight-case dataset includes six answerable questions with a expected filename/page and required answer terms, plus two unanswerable questions. The results contain run timestamp, provider, threshold, top-k, per-question evidence and measured latencies. No scores are populated until code executes.

| Metric | Computation | Limitation |
|---|---|---|
| Retrieval hit rate | Fraction of answerable questions retrieving the labeled filename AND page | Small dataset; post-threshold/safety-filter evidence |
| Source precision proxy | Relevant labeled-page chunks / retrieved evidence chunks | Other unlabeled pages may also be useful; not exhaustive relevance labels |
| Answer keyword proxy | Fraction whose answers contain every expected string | An incorrect answer can contain the words; not semantic correctness |
| Unsupported-answer rate on unanswerable | Unanswerable cases with outcome `answered` / unanswerable cases | Two cases only; cannot measure all hallucinations |
| Mean retrieval latency | Mean measured FAISS search time in milliseconds | Excludes embedding/network; tiny corpus and warm-cache effects |

For answer correctness, manually review each claim against its evidence and label supported/unsupported, complete/partial, and contradictory/non-contradictory. Keyword scores must never be presented as a human-verified accuracy score. Add domain-specific cases, multi-document cases and adversarial documents; retain a separate holdout set when tuning thresholds. Offline hash results must never be claimed as Gemini or semantic-model quality.
