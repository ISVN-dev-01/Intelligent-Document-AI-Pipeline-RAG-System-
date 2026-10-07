# Relational database

`database/schema.sql` creates a MySQL 8 database and three InnoDB tables. SQLAlchemy models mirror the schema. Every repository operation uses a short-lived session; writes use `sessions.begin()` so commit/rollback is automatic. Engine connections use pre-ping and recycling. Credentials are encoded with `URL.create`, so special characters in passwords do not corrupt connection URLs.

| Table | Key data | Relationship |
|---|---|---|
| documents | UUID, filename, unique SHA-256, size, pages, chunks, UTC upload time, status, ingest timings | Parent of source audit rows |
| queries | UUID, role, question/answer, UTC time, retrieval count, timings, outcome | Parent of query_sources |
| query_sources | Integer ID, query/document IDs, page, chunk UUID, cosine score | FK to both parents |

Vectors are never stored in MySQL. Chunk text is stored in the vector snapshot JSON, not duplicated into query_sources. History joins filename through document ID. A deleted document keeps its metadata tombstone so past query references remain valid; its PDF and searchable chunks are removed. Prior query answers can still contain information from deleted PDFs. This is intentional audit retention, not secure erasure.

States: `processing → ready` or `processing → failed`; admin removal sets `deleted`. Failed/deleted hashes can be re-ingested. Duplicate protection combines a SQL unique constraint with the process-shared pipeline lock. Restart recovery cleans incomplete writes and checks ready-vector counts.

Query insertion and all source rows commit in one transaction. The UI receives an error if audit persistence fails. Successful, low-relevance and model-abstained results are audited; rejected inputs and provider errors are event-log entries rather than fabricated query answers. `AUDIT_STORE_TEXT=false` stores `[redacted]` text. It does not erase old rows or disable current session display.

All stored timestamps are naive UTC by convention. MySQL `DATETIME` and SQLite preserve this convention. The UI labels them UTC to avoid silent local-time confusion. Shared role names identify a role, not an individual human.

## Setup and operation

Follow the MySQL instructions in README. `AUTO_CREATE_TABLES=true` initializes tables only; it does not create the MySQL database or migrate old tables. After applying the SQL schema, disable automatic creation and give the runtime account SELECT/INSERT/UPDATE/DELETE privileges only. Do not expose the server without TLS and a least-privilege network policy.

SQLite is explicitly for the offline demo and tests; foreign keys are enabled with a connect hook. A MySQL opt-in test checks the real dialect/schema when `TEST_MYSQL_DATABASE` is set. It never drops your tables.

## Backup and recovery

Stop Streamlit and all CLI writers. Back up the SQL database, upload directory and vector directory as one consistent set, and protect the backup as confidential. Restore all three together with the same embedding configuration. If only a vector store is lost, recover the full backup or initialize a fresh database/DATA_DIR and re-ingest original PDFs; do not manually delete the manifest and continue using ready records. No automatic migrations, retention jobs or disaster-recovery guarantees are implemented.
