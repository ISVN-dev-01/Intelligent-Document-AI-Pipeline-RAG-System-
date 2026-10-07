import argparse
from pathlib import Path

from _common import authenticated_app, cli_error

from utils.errors import DuplicateDocument


def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs as an authenticated administrator.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    paths = sorted(args.path.glob("*.pdf")) if args.path.is_dir() else [args.path]
    if not paths:
        parser.error("No PDF files found.")
    app, principal = authenticated_app()
    failed = False
    try:
        for path in paths:
            try:
                if path.stat().st_size > app.settings.max_upload_mb * 1024 * 1024:
                    print(f"Rejected {path.name}: exceeds upload limit")
                    failed = True
                    continue
                row = app.documents.ingest(principal, path.name, path.read_bytes())
                print(f"Ready: {row.filename}; {row.page_count} pages, {row.chunk_count} chunks; "
                      f"embedding {row.embedding_ms:.1f} ms, indexing {row.indexing_ms:.1f} ms")
            except DuplicateDocument:
                print(f"Already indexed: {path.name}")
    finally:
        app.engine.dispose()
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        cli_error(exc)
