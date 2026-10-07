# RAG pipeline internals

## Ingestion

`validate_pdf` checks path separators, control characters, Windows reserved names, extension, byte count and PDF magic. The SHA-256 hash detects identical bytes even under a renamed file. It does not detect semantically identical PDFs re-exported with different metadata.

`load_pdf` rejects encrypted, empty, unreadable, over-page-limit and text-free PDFs. It uses `PyPDFLoader(..., mode="page").lazy_load()` after a PyPDF page count. Whitespace cleaning preserves paragraph boundaries and factual punctuation. The extraction cap is checked after each page; it cannot stop a decompression bomb while parsing a single page. Production should sandbox parsers with CPU/memory limits.

Chunks never cross page boundaries. Metadata includes `document_id`, `document_name`, 1-based `page_number`, UUID `chunk_id`, original filename `source`, and UTC `created_at`. PDF page 0 in LangChain becomes displayed page 1 (physical page, not printed Roman numeral numbering).

Google embeddings use `RETRIEVAL_DOCUMENT` for chunks and `RETRIEVAL_QUERY` for questions, 768 output dimensions, batches of 32. The stored fingerprint contains model, dimension and task version. Changing providers/models requires a fresh corpus directory and re-ingestion.

## Search mathematics

Vectors are converted to contiguous float32 and normalized to unit L2 norm. FAISS `IndexFlatIP` computes inner product; for normalized vectors this equals cosine similarity:

`score(q, d) = q dot d / (||q|| * ||d||)`

Higher scores indicate closer vectors. The range is [-1, 1], not a probability. NaN, infinity, zero and inconsistent dimensions are rejected. A metadata filter first restricts eligible documents logically, then returns the highest `top_k` eligible scores. This implementation sorts all FAISS hits to guarantee correct filters; an ANN index with selective candidate expansion is a future scaling improvement.

Empty corpus returns no hits without a Google call. The threshold is configurable and corpus/model dependent, not universally “appropriate.” Calibrate on answerable and unanswerable questions; report recall alongside abstention.

## Evidence and generation

Queries reject malformed input and a small set of instruction-override patterns. Passages matching the same heuristic are quarantined. A character budget selects whole chunks. Evidence is labeled S1, S2, etc. Gemini receives a system instruction plus a JSON user message containing the question, bounded previous questions and untrusted evidence. It has no browsing, SQL, file or execution tools.

Gemini returns `GroundedAnswer(answerable, claims)`. Each claim includes a sentence, a source label and a verbatim supporting quote. Validation requires a known source label and an exact whitespace-normalized quote of at least 12 characters in that source. One invalid claim rejects the entire answer. Citations use application metadata, not invented filenames. This checks provenance, **not full logical entailment**: real quotes can still accompany unsupported interpretations.

No relevant safe chunks bypass generation with the low-relevance message. Model abstention or invalid evidence returns “The information is not available in the uploaded documents.” Sources and retrieved passages are separately shown: retrieved context is not necessarily cited support.

## Memory and metrics

Only up to MEMORY_TURNS previous user questions are passed. Short follow-ups containing a limited pronoun/count cue concatenate the latest question for retrieval. Previous answers are never evidence. The UI retains at most ten exchanges for display; this is independent of the retrieval-memory limit.

`perf_counter` measures chunk embedding and indexing; queries measure embedding, FAISS retrieval, LLM, and total response. The persisted duration ends immediately before audit insertion; UI duration includes audit insertion. Neither is a benchmark claim. Retrieval timing excludes query embedding and SQL ready-ID lookup. Indexing includes snapshot serialization and disk write.
