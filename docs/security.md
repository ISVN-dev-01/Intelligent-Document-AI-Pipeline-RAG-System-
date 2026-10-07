# Security model and honest limitations

## Implemented boundary

This is a single-host trusted-operator application. It binds to 127.0.0.1. Users must sign in with one of two shared role passwords. Admin manages documents and sees global query history; user queries and browses the shared document library. Services also check the admin role on mutation. There are no individual identities or per-document ACLs. Selection filters restrict search scope; they must never be advertised as authorization.

Passwords use random 16-byte salts and PBKDF2-HMAC-SHA256 with 600,000 iterations. Verification uses constant-time comparison. Five failures trigger a one-minute, role-wide process-local cooldown, which persists across browser refreshes but resets after restart. This basic control can itself cause denial of service and is not an enterprise rate limiter. Sign-out clears session state; authenticated sessions do not currently expire automatically.

## Data flow and privacy

Google mode sends extracted text to Google for embedding and selected passages plus the question and bounded question history for generation. Thus this is private **storage**, not a guarantee of local-only processing. Account-specific provider retention, training and regional controls must be reviewed by the operator. Offline demo mode makes no model requests.

PDFs, JSON chunk text, FAISS vectors and SQL audits can all contain confidential information. Use OS ACLs, encrypted disks and protected backups. Default storage is outside source code, but explicit DATA_DIR overrides can point anywhere; never configure a public/synced directory for private documents. The repository itself may reside on OneDrive; the normal default data directory does not. Filesystem permissions are not provisioned by this application.

Query auditing defaults to storing questions and answers. Set AUDIT_STORE_TEXT=false to redact future stored text. Source IDs, role and timings remain. Administrator-visible history is shared. Deletion removes PDF/vectors but intentionally retains audit answers and document metadata. Previous browser sessions may still display previously received answers. There is no automated retention or guaranteed secure deletion.

## Input and prompt controls

1. Reject invalid names, file types, oversized inputs, encrypted PDFs and empty extraction.
2. UUID disk filenames prevent upload path traversal.
3. Bound pages, extracted text, query length, context length and conversation history.
4. Validate query syntax and flag common override/secret-exfiltration phrases.
5. Quarantine retrieved passages containing the same known patterns.
6. Keep system instructions separate from JSON-encoded untrusted document data.
7. Give the model no tools, external search or direct access to secrets.
8. Threshold retrieval before generation; require explicit abstention if evidence is absent.
9. Validate source labels and exact quotes against retrieved text; reject invalid outputs.
10. Render answers and evidence as plain text, preventing active model-generated links/images.

These controls are **mitigations**. Regexes have false positives and miss paraphrased, multilingual or encoded injections. A source can state false facts. A true quote does not prove the model's claim follows from it. Similarity does not measure correctness. A robust production evaluation needs adversarial prompts, entailment testing, human review and document trust policies.

## File and operational risks

FAISS snapshots are loaded with native deserialization, never pickle. Checksums protect against accidental corruption, not an attacker who controls both files and manifest. Load only locally generated indexes protected from modification. PDF parsing runs in the app process: page/character limits do not fully defend decompression bombs or parser vulnerabilities. Add sandboxed workers and malware scanning before accepting hostile public uploads.

Application JSON logs allowlist event names, counts, IDs and error class names. They omit raw prompts, answers, passwords and exception messages. Library debugging/tracing can still capture data if an operator enables it; do not enable LangSmith or verbose provider tracing for private corpora without authorization. UI errors never intentionally expose full stack traces.

Do not publish this default service directly to the internet. A production deployment needs SSO/OIDC, per-person audit identity, server-enforced document ACLs, session expiry, TLS, secure secrets storage, database TLS, patch management, worker isolation, retention/deletion workflows and restore testing. No claim of enterprise compliance is made.
