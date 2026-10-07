import streamlit as st


def render(app, principal):
    principal.require_admin()
    st.caption("WORKSPACE / AUDIT")
    st.title("Query history")
    st.caption("Most recent 50 queries • Admin only • Times shown in UTC")
    rows = app.repository.history()
    if not rows:
        st.info("Ask a question to create the first audit record.")
    for row in rows:
        with st.expander(f"{row.created_at} · {row.outcome} · {row.actor_role}"):
            st.text(row.query_text)
            st.text(row.response_text)
            st.caption(f"{row.retrieval_count} passages · Search {row.retrieval_ms:.1f} ms · Pipeline {row.duration_ms:.0f} ms")
            for source, filename in app.repository.query_sources(row.id):
                st.text(f"{filename} — Page {source.page_number} — similarity {source.similarity_score:.3f}")
