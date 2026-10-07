from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_login_and_navigation(settings, monkeypatch):
    for key, value in {"APP_MODE": "demo", "EMBEDDING_PROVIDER": "hash", "DB_BACKEND": "sqlite",
                       "DATA_DIR": str(settings.data_dir),
                       "ADMIN_PASSWORD_HASH": settings.admin_password_hash.get_secret_value(),
                       "USER_PASSWORD_HASH": settings.user_password_hash.get_secret_value()}.items():
        monkeypatch.setenv(key, value)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.selectbox[0].select("admin")
    app.text_input[0].input("test-only-password-123")
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 4
    for page in ["Ask documents", "Document library", "Upload documents", "Query history"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
