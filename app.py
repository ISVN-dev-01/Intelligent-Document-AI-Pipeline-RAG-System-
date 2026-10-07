"""Streamlit entry point. Run: streamlit run app.py."""
import streamlit as st
from pydantic import ValidationError

from services.bootstrap import build_application
from ui import chat, dashboard, documents, history, upload
from ui.common import show_error
from utils.errors import AppError

st.set_page_config(page_title="Document Intelligence", page_icon="📚", layout="wide")


@st.cache_resource
def application():
    return build_application()


def main():
    try:
        app = application()
    except ValidationError as exc:
        st.error("Configuration needs attention. Check .env against .env.example.")
        for error in exc.errors(include_input=False, include_url=False):
            st.write(" / ".join(map(str, error["loc"])) or "Configuration", error["msg"])
        return
    except Exception as exc:
        show_error(exc)
        st.info("First run: python scripts/setup_env.py --mode demo")
        return
    if "principal" not in st.session_state:
        st.title("Document Intelligence")
        st.caption("PRIVATE KNOWLEDGE • EVIDENCE FIRST")
        st.write("Sign in to explore your team's document library.")
        with st.form("login"):
            role = st.selectbox("Role", ["user", "admin"])
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                try:
                    st.session_state.principal = app.auth.login(role, password)
                    st.rerun()
                except AppError as exc:
                    st.error(str(exc))
        return
    principal = st.session_state.principal
    with st.sidebar:
        st.title("Document\nIntelligence")
        st.caption("A grounded workspace for private knowledge")
        pages = ["Overview", "Ask documents", "Document library"]
        if principal.role == "admin":
            pages += ["Upload documents", "Query history"]
        page = st.radio("Workspace", pages, label_visibility="collapsed")
        st.divider()
        st.caption(f"Signed in as {principal.role}")
        st.caption("Offline demo" if app.settings.app_mode == "demo" else "Google Gemini")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()
    if app.settings.app_mode == "demo":
        st.info("Offline demonstration: hashed word retrieval and verbatim excerpts. Gemini is not being called.")
    else:
        st.caption("Google mode: document text is sent to Google for embeddings; retrieved evidence is sent for answers.")
    renderers = {"Overview": dashboard.render, "Ask documents": chat.render,
                 "Document library": documents.render, "Upload documents": upload.render,
                 "Query history": history.render}
    try:
        renderers[page](app, principal)
    except Exception as exc:
        show_error(exc)


if __name__ == "__main__":
    main()
