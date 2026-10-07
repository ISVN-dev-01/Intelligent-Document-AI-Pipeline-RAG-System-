"""Exercise the full offline pipeline in a fresh, isolated local directory."""
import json
from uuid import uuid4

from _common import ROOT, cli_error

from config.settings import Settings
from evaluation.evaluator import evaluate
from security.auth import Principal, hash_password
from services.bootstrap import build_application


def run():
    data_dir = ROOT / "tmp" / f"smoke-{uuid4().hex}"
    password_hash = hash_password("smoke-test-only-credential")
    settings = Settings(_env_file=None, app_mode="demo", embedding_provider="hash", db_backend="sqlite",
        data_dir=data_dir, admin_password_hash=password_hash, user_password_hash=password_hash,
        similarity_threshold=0.12)
    app = build_application(settings)
    principal = Principal("admin")
    measurements = []
    try:
        for path in sorted((ROOT / "data/sample_documents").glob("*.pdf")):
            doc = app.documents.ingest(principal, path.name, path.read_bytes())
            measurements.append({"filename": doc.filename, "pages": doc.page_count, "chunks": doc.chunk_count,
                                 "embedding_ms": doc.embedding_ms, "indexing_ms": doc.indexing_ms})
        dataset = json.loads((ROOT / "evaluation/evaluation_dataset.json").read_text())
        result = evaluate(app, principal, dataset)
        result["ingestion"] = measurements
        result["data_dir"] = str(data_dir)
        output = ROOT / "evaluation" / "results-smoke.json"
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
        print(f"Measured report: {output}")
    finally:
        app.engine.dispose()
    restarted = build_application(settings)
    try:
        answer = restarted.queries.ask(principal, "What is the annual leave entitlement?")
        assert "24" in answer.answer
        print("Restart check passed: saved vectors returned cited annual leave evidence.")
    finally:
        restarted.engine.dispose()


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        cli_error(exc)
