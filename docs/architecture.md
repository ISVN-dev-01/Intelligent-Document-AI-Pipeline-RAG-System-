# Architecture and component decisions

The composition root is `services/bootstrap.py`. It validates configuration, opens an SQLAlchemy engine, chooses providers, loads the FAISS store and recovers interrupted uploads. Streamlit caches this application per process; a single cached AuthService provides role-level throttling across browser sessions. Sessions store only the logged-in principal and bounded chat display history.

| Component | Responsibility | Why this choice / tradeoff |
|---|---|---|
| Streamlit | Forms, chat, metrics and source inspection | Small Python UI, easy viva; lacks enterprise session/identity features |
| DocumentService | Validate, deduplicate, extract, chunk, embed, publish | Centralizes state transitions and rollback |
| PyPDFLoader | Page text extraction using PyPDF | Real page metadata; does not OCR or faithfully interpret all tables |
| RecursiveCharacterTextSplitter | Split paragraphs with overlap | Understandable configurable heuristic, not semantic segmentation |
| EmbeddingService protocol | Document/query vectors | Swappable provider without rewriting retrieval |
| FaissStore | Exact normalized inner-product search | Fast native dense-vector operations; O(Nd), in-memory |
| Repository | Short-lived SQLAlchemy transactions | Portable SQLite tests and MySQL runtime; no scattered SQL |
| Retriever | Query embeddings, metadata filters, thresholds | Separates search choices from generation |
| GeminiService | One structured LangChain model call | No deprecated chains or unrestricted agent tools |
| Guardrails | Passage quarantine, context budget, output citations | Defense in depth, not a security proof |
| AuditService | Persist query, evidence and timings | Fails closed if auditing fails |

## Persistence and consistency

Runtime data defaults to the user's home `.document_ai`, never the source tree. PDF names on disk are UUIDs. FAISS is a native binary snapshot and chunk text/metadata is JSON. A manifest records provider fingerprint, generation UUID and SHA-256 checksums. Both snapshot files are flushed before atomically replacing the manifest with `os.replace`. Other instances reload after a generation change. A failed publication leaves the old manifest usable. Old snapshots are cleaned after publication; this is not a substitute for backups. Checksums detect accidental corruption, not malicious rewriting by a local attacker.

There is no distributed transaction spanning MySQL and files. A common local FileLock serializes ingestion, deletion and query processing. Records begin `processing`; their vectors are published before SQL becomes `ready`. Retrieval always intersects SQL-ready IDs. Startup removes vectors for non-ready records and marks interrupted jobs failed. Retry reuses the file hash record. A ready record with missing vectors triggers an error rather than silently losing documents. SQL tombstones retain source foreign keys after deletion.

Use **one DATA_DIR with one corresponding database** and a local filesystem. Two processes sharing a database but using different DATA_DIR values are unsupported. The shared lock is held during remote requests for clarity and consistency, limiting concurrency. Scale out with durable jobs, versioned corpus state and a transactional indexing ledger.

## Trust boundaries

The authenticated browser calls trusted in-process services. Principal objects are not bearer tokens or a public API; local Python execution is already trusted. Admin and user are shared roles, not per-person accounts. All authorized users see the same corpus. External Google services receive text only when Google mode is configured. UI renders evidence and answers as plain text so model-supplied links/images cannot become active content.

Mermaid source: [system](diagrams/system.mmd), [data flow](diagrams/data_flow.mmd), [sequence](diagrams/sequence.mmd).
