import streamlit as st


def render(app, principal):
    st.caption("WORKSPACE / OVERVIEW")
    st.title("Your documents. Clear answers.")
    st.write("Turn reports, policies and project guides into answers you can trace to a page.")
    stats = app.statistics.snapshot()
    for column, label, key in zip(st.columns(4), ["Documents", "Indexed chunks", "Questions asked", "Avg. search"],
                                  ["documents", "chunks", "queries", "avg_retrieval_ms"]):
        column.metric(label, f"{stats[key]:.1f} ms" if key.endswith("ms") else stats[key])
    left, right = st.columns([2, 1])
    with left, st.container(border=True):
        st.subheader("From upload to evidence")
        st.write("1. An administrator uploads a readable PDF.")
        st.write("2. The pipeline builds searchable, page-aware passages.")
        st.write("3. Ask a question, then inspect the evidence behind the answer.")
    with right, st.container(border=True):
        st.subheader("Workspace status")
        st.write(f"Vector store: {stats['vector_status']}")
        st.write(f"Database: {app.settings.db_backend.upper()}")
        st.write(f"Last query (UTC): {stats['last_query'] or 'No queries yet'}")
    st.subheader("Try a question")
    st.write("What is the annual leave entitlement? • What are the password requirements? • Who approves project milestones?")
