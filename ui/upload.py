import streamlit as st

from ui.common import show_error


def render(app, principal):
    principal.require_admin()
    st.caption("WORKSPACE / INGESTION")
    st.title("Add to your knowledge library")
    st.write("Upload text-based PDFs. Duplicate content is detected automatically.")
    st.caption(f"Up to {app.settings.max_upload_mb} MB and {app.settings.max_pdf_pages} pages per file. Scanned PDFs require OCR.")
    files = st.file_uploader("Choose PDF documents", type=["pdf"], accept_multiple_files=True)
    if st.button("Process documents", type="primary", disabled=not files):
        progress = st.progress(0)
        for index, file in enumerate(files):
            with st.status(f"Processing {file.name}", expanded=True) as status:
                try:
                    row = app.documents.ingest(principal, file.name, file.getvalue())
                    st.write(f"{row.page_count} pages · {row.chunk_count} chunks")
                    st.caption(f"Embedding {row.embedding_ms:.0f} ms · Indexing {row.indexing_ms:.0f} ms")
                    status.update(label=f"Ready: {file.name}", state="complete")
                except Exception as exc:
                    show_error(exc)
                    status.update(label=f"Not ingested: {file.name}", state="error")
            progress.progress((index + 1) / len(files))
