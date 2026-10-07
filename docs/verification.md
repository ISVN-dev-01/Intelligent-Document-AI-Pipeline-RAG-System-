# Verification record

Recorded 7 October 2026 on Windows with Python 3.13.9, in the user's Desktop project directory. See `requirements-lock.txt` for the installed dependency versions.

| Check actually performed | Result |
|---|---|
| Install dependencies in `.venv` | Completed |
| `python -m pip check` | No broken requirements found |
| `python -m ruff check .` | Passed |
| `python -m compileall -q app.py config database embeddings evaluation ingestion llm retrieval scripts security services ui utils vector_store` | Passed |
| `python -m pytest -q --basetemp=tmp/pytest-final` | **48 passed, 1 skipped**, 8.00 seconds reported by pytest |
| Google embedding/chat adapter construction | Passed with dummy key, without network calls |
| Google embedding batching and Gemini structured messages | Mock-provider tests passed |
| SQL table initialization, FKs, transactional audit | Passed against SQLite |
| FAISS initialization, add, persist, reload, delete, corruption detection | Passed using real FAISS |
| Sample ingestion and query after restart | Passed in isolated offline corpus |
| Streamlit authenticated navigation | AppTest passed for all five screens |
| Real Streamlit server startup | Child process returned HTTP 200 and `ok` from `/_stcore/health`, then was stopped |
| CLI setup, schema init, ingestion and evaluation entry points | Executed under test with temporary configuration and mocked password input |
| Sample PDF rendering | All six pages rendered with Poppler and visually inspected |

## Measured offline evaluation

`python scripts/smoke_demo.py` produced the stored [demo_results.json](demo_results.json). Runtime: `2026-10-07T15:37:33.820441+00:00` (21:07:33 IST). Three documents, six pages, six chunks; hash provider, excerpt answers, top-k 5, threshold 0.12.

- Expected filename/page retrieved for 6/6 answerable questions.
- Mean labeled-page source precision proxy: 0.7916666667.
- Required answer strings present in 6/6 answerable outputs.
- Unsupported answers on the two unanswerable cases: 0/2.
- Mean FAISS retrieval duration: 11.8348 ms in that run.

These are observations on a tiny development set, **not general accuracy or production performance**. The offline relevance gate was adjusted after an earlier run falsely returned a passage on one unanswerable case; the final result is not a held-out evaluation. Latencies include local locking/reload checks and are affected by simultaneous verification work. Detailed per-document and per-question timings are preserved in the JSON report; no timing was invented.

## Unverified integrations and observed warnings

- No configured MySQL server or API credentials were available. The MySQL test was skipped; the schema and real Google requests still require validation in your environment.
- Python 3.11 source compatibility is intended; execution here used Python 3.13.9.
- `langchain-community` emitted its package sunset warning. The required PyPDFLoader API still imported and worked with the locked version. Plan a loader migration before long-term production use.
- Poppler emitted missing fallback-font warnings for Symbol/ArialUnicode. The samples use Helvetica and all rendered pages were legible with no clipping.
- Initial sandboxed Streamlit tests could not create a localhost socket. The completed test run used approved execution outside that sandbox. This was an environment restriction, not bypassed in application code.

No live Gemini benchmark, MySQL performance result, enterprise security certification or elimination of hallucinations is claimed.
