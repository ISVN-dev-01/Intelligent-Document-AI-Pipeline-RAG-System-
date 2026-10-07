import streamlit as st


def render(app, principal):
    st.caption("WORKSPACE / LIBRARY")
    st.title("Document library")
    rows = app.repository.documents()
    if not rows:
        st.info("No documents uploaded yet.")
        return
    st.dataframe([{"Filename": r.filename, "Pages": r.page_count, "Chunks": r.chunk_count,
                   "Uploaded (UTC)": r.uploaded_at, "Status": r.processing_status} for r in rows],
                 hide_index=True, width="stretch")
    if principal.role == "admin":
        available = {r.id: r for r in rows if r.processing_status != "deleted"}
        if available:
            st.subheader("Manage documents")
            target = st.selectbox("Document", list(available), format_func=lambda x: available[x].filename)
            confirmed = st.checkbox("Remove this document from search and delete its stored PDF")
            if st.button("Delete document", disabled=not confirmed):
                app.documents.delete(principal, target)
                st.session_state.pop("messages", None)
                st.rerun()
            st.caption("Audit history is retained. Other active sessions may still display previously returned answers.")
