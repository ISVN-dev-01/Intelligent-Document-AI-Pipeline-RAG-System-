import streamlit as st

from ui.common import show_error, show_result


def render(app, principal):
    st.caption("WORKSPACE / DOCUMENT QA")
    st.title("Ask your documents")
    st.write("Answers are grounded in retrieved passages. Open the evidence to verify the source.")
    rows = [r for r in app.repository.documents() if r.processing_status == "ready"]
    choices = {row.id: row.filename for row in rows}
    selected = st.multiselect("Limit search to documents (empty means all)", list(choices), format_func=choices.get)
    if not rows:
        st.info("The library is empty. An administrator can upload the sample PDFs to get started.")
    if st.button("Clear conversation"):
        st.session_state.messages = []
    messages = st.session_state.setdefault("messages", [])
    for question, result in messages:
        with st.chat_message("user"):
            st.text(question)
        with st.chat_message("assistant"):
            show_result(result)
    question = st.chat_input("Ask about a policy, process or project", max_chars=app.settings.max_question_chars)
    if question:
        with st.chat_message("user"):
            st.text(question)
        try:
            with st.spinner("Finding supporting evidence..."):
                result = app.queries.ask(principal, question, [q for q, _ in messages], set(selected) if selected else None)
            with st.chat_message("assistant"):
                show_result(result)
            messages.append((question, result))
            del messages[:-10]
        except Exception as exc:
            show_error(exc)
    st.caption(f"Uses at most {app.settings.memory_turns} recent questions for reference. Conversation answers are never treated as evidence.")
