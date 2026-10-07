import streamlit as st

from utils.errors import AppError
from utils.logging_config import event


def show_error(exc):
    if isinstance(exc, AppError):
        st.error(str(exc))
    else:
        event("application_failure", error_type=type(exc).__name__)
        st.error("The operation could not be completed. Check configuration, database availability and local event logs.")


def show_result(result):
    # Plain text prevents untrusted document/model content from becoming active Markdown links/images.
    st.text(result.answer)
    st.caption(f"Search {result.retrieval_ms:.1f} ms · Embedding {result.embedding_ms:.1f} ms · "
               f"Response {result.duration_ms:.0f} ms · {len(result.evidence)} evidence passages")
    if result.sources:
        st.caption("Cited sources")
        for source in result.sources:
            st.text(f"[{source.label}] {source.document_name} — Page {source.page_number}")
    with st.expander("Inspect retrieved evidence", expanded=False):
        if not result.evidence:
            st.write("No passages passed the relevance and safety filters.")
        for source in result.evidence:
            st.text(f"[{source.label}] {source.document_name} | Page {source.page_number}")
            st.caption(f"Cosine similarity: {source.score:.3f} (retrieval relevance, not answer confidence)")
            st.text(source.text)
            st.divider()
