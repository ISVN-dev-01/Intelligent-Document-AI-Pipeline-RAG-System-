# Intelligent Document AI Pipeline — project report

**Project type:** Final-year Computer Science engineering project  
**Implementation:** Python, LangChain, FAISS, MySQL, Gemini and Streamlit  
**Scope:** A single-host, evidence-grounded assistant for a shared collection of private PDFs

## Chapter 1 — Introduction

### Background and motivation

Organizations keep policies, manuals and delivery records in PDFs. Employees often need a specific fact, such as annual leave entitlement or an approval owner, rather than an entire document. Traditional full-text search returns matching files but does not assemble a concise answer. Generative language models can produce fluent answers, but their pretrained knowledge does not establish the contents of a private policy.

Retrieval-augmented generation addresses this gap by finding relevant source passages before generation. This project makes the evidence visible and associates each answer with physical document pages. It also separates storage, model access and application orchestration so each part can be explained and tested independently.

### Problem statement

Build an authenticated PDF question-answering system that preserves source provenance, persists embeddings across restarts, refuses unsupported answers where practical, and records query activity without hiding operational limitations.

### Objectives

1. Extract and clean PDF text while preserving document/page identity.
2. Split long text into manageable overlapping chunks and embed them using a replaceable provider.
3. Use FAISS for in-memory vector search and maintain durable metadata mappings.
4. Generate concise Gemini answers using retrieved evidence and verify citation provenance.
5. Manage metadata and audits through MySQL and SQLAlchemy transactions.
6. Provide a usable Streamlit demonstration, offline tests and measured evaluation.

### Scope

The supported input is a text-based, unencrypted PDF. Two shared roles use one corpus: administrators manage documents and audit history, while users query and browse documents. The project is intended for a student laptop and modest corpus. It excludes OCR, individual identities, fine-grained document permissions and distributed operation.

## Chapter 2 — Literature and technology review

### NLP and dense embeddings

Natural-language processing provides methods to represent and compare text. A dense embedding maps a passage to a numeric vector. Semantically related passages are intended to have nearby representations, although embedding quality varies by domain and language. Here the Google provider uses distinct retrieval task types for documents and questions. All embeddings are normalized so inner product equals cosine similarity.

### Vector search and FAISS

FAISS provides native implementations of dense-vector search. The project chooses `IndexFlatIP`, which compares the query with every stored vector. It is exact search, not an approximate-nearest-neighbor configuration. It avoids repeated parsing and embedding at query time, and uses efficient array operations, but its search cost grows linearly with corpus size. The project does not claim it outperforms another database without a controlled comparative experiment.

### RAG and language models

RAG combines retrieval with generation. Retrieval narrows the model's input to a relevant subset of the corpus. The model can still misinterpret evidence, and retrieval may miss an answer, so citations and refusal rules are required. This implementation uses structured claim objects rather than accepting unrestricted model prose. It verifies that each cited quote appears in the cited chunk; logical correctness still needs evaluation.

### LangChain and supporting technologies

LangChain supplies `PyPDFLoader`, `RecursiveCharacterTextSplitter`, message classes and Google integrations. Direct FAISS handles persistence without pickle. SQLAlchemy isolates relational operations from UI code. Pydantic validates configuration and model output. Streamlit provides forms, chat, metrics and tables with a small Python codebase. The installed LangChain Community package emits a sunset warning; it is retained to meet the specified PyPDFLoader requirement and should be revisited before longer-term deployment.

Primary references: [FAISS documentation](https://faiss.ai/), [LangChain Google chat integration](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai), [Google embeddings](https://ai.google.dev/gemini-api/docs/embeddings), [SQLAlchemy 2 documentation](https://docs.sqlalchemy.org/en/20/), and [Streamlit documentation](https://docs.streamlit.io/).

## Chapter 3 — System analysis

### Existing workflow

A user manually searches file names or keywords, opens candidate PDFs and reconciles their contents. This is slow when facts span documents. A generic chatbot can answer quickly but has no reliable basis for identifying an organization's current uploaded policy.

### Proposed workflow

Administrators ingest documents once. Users ask questions in natural language, receive evidence-linked answers and inspect the retrieved passages. The application records query timings and sources. If it cannot find usable evidence, it abstains rather than forcing a response.

### Functional requirements

The implemented requirements include authentication, multi-PDF upload, validation, duplicate detection, extraction, page-aware chunking, embeddings, persisted FAISS search, selected-document filtering, grounded generation, source inspection, bounded conversation reference, dashboard statistics, deletion and query history. CLI commands perform setup, schema initialization, ingestion and evaluation.

### Non-functional requirements

Maintainability is addressed through separate provider, retrieval, storage and orchestration modules. Reliability is addressed through atomic snapshots, SQL transactions and restart recovery. Privacy is addressed through external runtime directories, environment secrets and plain-text UI rendering. Reproducibility is addressed through a dependency lock, synthetic PDFs and offline tests. Throughput is deliberately limited by a shared pipeline lock to simplify consistency.

### Feasibility

The offline demonstration requires no GPU, paid API or MySQL installation. The main system needs network access to Google and a MySQL 8 server. FAISS CPU runs on the tested Windows environment. No live Google or MySQL performance is inferred from offline tests.

## Chapter 4 — System design

### Architecture and data flow

`app.py` handles application composition and navigation. UI modules call application services. Ingestion flows through validation, extraction, chunking, embeddings and indexing. Query processing flows through validation, query embedding, retrieval, filtering, context construction, structured generation, evidence validation and audit persistence.

Use the Mermaid sources in `docs/diagrams/` for the system architecture, data-flow diagram, RAG pipeline, ER diagram and sequence diagram. They describe actual modules rather than a separate unimplemented REST layer.

### Component design

DocumentService owns ingestion state transitions and deletion. FaissStore owns normalization, publication and reload. Retriever controls top-k, threshold and metadata selection. GeminiService owns the only remote chat-model invocation. QueryService coordinates retrieval and answer validation. Repository owns database session scope. This separation allows tests to replace remote providers while retaining real extraction, FAISS and SQL behavior.

### Database design

The `documents` table has a UUID primary key and unique content hash, plus file statistics, status and timing fields. The `queries` table records role, text, timings and outcome. The `query_sources` table links a query to document/page/chunk identifiers and cosine scores through foreign keys. A deleted document keeps a metadata tombstone for audit integrity.

### Consistency design

SQL and local files cannot share an atomic transaction. The chosen design writes a processing row, publishes vectors atomically and marks the document ready last. Search accepts only SQL-ready document IDs. Startup cleans interrupted records. Index snapshots use a manifest with checksums and a model fingerprint, preventing accidental cross-model reuse. All operations sharing a corpus also share a file lock.

## Chapter 5 — Implementation

### PDF ingestion and chunking

Filenames are checked for paths, control characters and Windows reserved names. File extension and PDF signature must agree. Size, page and extracted-character limits provide basic bounds. Password-protected and image-only PDFs return actionable errors. Each non-empty page is cleaned and split independently with a 1000-character target and 150-character overlap. A physical page reference therefore remains valid for every chunk.

### Embeddings and vector storage

GoogleEmbeddingService batches passages and requests 768-dimensional embeddings. Query vectors use the matching query task. HashEmbeddingService is a deterministic, clearly labeled test/demo baseline; it has no trained semantic knowledge. FaissStore validates finite nonzero vectors, normalizes them and writes native FAISS bytes plus JSON text/metadata. No deserialization of Python objects is required.

### Retrieval and grounding

Retriever embeds the question, searches the in-memory index, applies ready-ID and selected-document filters and a cosine threshold. The context builder discards suspicious chunks and caps the total text. The system prompt treats documents and conversation questions as untrusted data. Gemini returns claims containing a statement, source label and quote. The validator checks source membership and exact quote inclusion before rendering application-generated citations.

### No-answer and memory behavior

No relevant context skips the LLM entirely. Model abstention or invalid quotations produce the fixed information-unavailable answer. The offline demo additionally requires 60% lexical question-term coverage before quoting a passage; this is a deliberately conservative baseline, not semantic verification. Up to three previous user questions help resolve short follow-ups; previous answers do not become factual evidence.

### Streamlit and access control

The dashboard presents document/chunk/query counts, average search latency and vector status. Administrators have upload and history navigation. The chat view supports document selection, plain-text answers and expandable evidence. Password hashes use PBKDF2 with random salts; failed-login cooldowns are shared per role within the process. This does not provide individual accountability or enterprise identity management.

### Audit and observability

Queries and retrieved evidence are inserted in one SQL transaction before the answer is returned. Runtime timings use `perf_counter`. The persisted query duration excludes the audit insertion itself, while the displayed duration includes it. JSON event logs contain operational IDs, counts and error class names but not raw exception messages, document bodies or credentials.

## Chapter 6 — Testing and results

The final verification on 7 October 2026 used Windows and Python 3.13.9. **48 tests passed and one MySQL test was skipped** in the recorded run. Tests cover PDF extraction, invalid uploads, page metadata, vector persistence, filters, invalid vectors, corrupted snapshots, failed publication, duplicate concurrency, provider failure, rollback/retry, citation rejection, abstention, database relationships, audit redaction, roles, CLI workflows, Streamlit navigation and actual localhost HTTP startup. The skipped test requires a separately configured MySQL schema.

The dependency check reported no conflicts. Ruff and syntax compilation completed successfully. Google integration objects constructed using the installed APIs without making requests; provider methods are covered with mocks. Actual Google API success, answer quality and live MySQL operation remain unverified.

A measured offline smoke run ingested three two-page synthetic PDFs into six chunks and persisted/reloaded their FAISS index. Across six answerable cases, retrieval found the expected source/page in 6/6 cases. The source-precision proxy was approximately 0.792. The keyword-answer proxy passed 6/6, and both unanswerable cases abstained. The mean measured retrieval time was approximately 11.83 ms in that run. These are tiny-corpus **offline hash/excerpt** measurements, not evidence of Gemini accuracy, semantic-search quality or production latency. Detailed measured values are retained in `docs/demo_results.json`.

The first baseline evaluation incorrectly returned an excerpt for one unanswerable query because two overlapping words were sufficient. Raising lexical coverage and adding a regression test corrected those supplied cases. Since that change used the evaluation examples, these results are development-set observations, not independent holdout performance. A larger held-out dataset is needed for any general quality claim.

All six sample PDF pages were rendered and visually inspected. Screenshot insertion points for an academic submission:

- **Figure 6.1:** Insert your authenticated overview screenshot with real document counts.
- **Figure 6.2:** Insert a successful multi-PDF ingestion screenshot.
- **Figure 6.3:** Insert a leave-policy answer with the source expander open.
- **Figure 6.4:** Insert an unsupported-question abstention screenshot.
- **Figure 6.5:** Insert admin audit history and evaluation output from your environment.

These are report figure locations, not fabricated screenshots. See `docs/verification.md` for the exact commands and qualification of results.

## Chapter 7 — Conclusion and future scope

The implemented repository demonstrates the complete PDF-to-retrieval-to-answer workflow with source provenance, durable vector storage and relational auditing. Its main educational contribution is connecting AI components to explicit software-engineering and trust boundaries. RAG and prompts reduce some failure modes but do not establish correctness by themselves.

Future work should prioritize OCR and table extraction, hybrid retrieval and reranking, human/entailment evaluation, per-document authorization, SSO, session expiry, encrypted storage, retention workflows and worker isolation. For larger corpora, compare approximate FAISS indexes or a service-based vector store using a controlled benchmark, and replace the coarse pipeline lock with durable asynchronous ingestion and versioned corpus reads.

## Viva preparation

| Question | Answer grounded in this implementation |
|---|---|
| Why RAG? | It brings uploaded evidence into the prompt without retraining model weights. It cannot guarantee faithful interpretation. |
| Why chunks and overlap? | Smaller passages focus retrieval; overlap reduces boundary loss. Character-based chunks can still break meaning. |
| Why FAISS rather than MySQL vectors? | Native dense-vector operations and simple in-memory indexing; MySQL retains structured metadata/audit roles. |
| Is this approximate search? | No. IndexFlatIP performs exact normalized inner-product search. |
| What does 0.35 mean? | A configurable cosine cutoff, not 35% confidence or a universal relevance threshold. |
| Why fingerprint the embedding model? | Vectors from different models/dimensions are not safely comparable; the index must be rebuilt. |
| What happens after a crash? | SQL-ready filtering and startup recovery exclude incomplete ingestion. Mismatched ready counts fail closed. |
| Can prompt injection be eliminated? | No. Role separation, quarantine and quote checks are partial defenses with known gaps. |
| Are citations proof of truth? | They identify retrieved evidence. Exact quote matching proves provenance, not entailment or source accuracy. |
| Is corporate data entirely local? | Only in offline mode. Google mode transmits text to external APIs. |
| What was actually tested? | Local offline unit/integration/UI/HTTP/CLI paths; no real Google or MySQL service claims. |
| What changes for production? | Identity/ACLs, TLS, encryption, isolated parsing, migrations, retention, scale and independent evaluation. |
