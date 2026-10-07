import runpy
import sys
from pathlib import Path


def test_cli_setup_ingest_evaluate(settings, monkeypatch):
    import scripts._common as common
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "scripts"))
    # All direct-script imports share the controlled test helper.
    monkeypatch.setitem(sys.modules, "_common", common)
    temporary_root = settings.data_dir / "setup"
    temporary_root.mkdir()
    (temporary_root / ".env.example").write_text((root / ".env.example").read_text())
    monkeypatch.setattr(common, "ROOT", temporary_root)
    monkeypatch.setattr("getpass.getpass", lambda *args: "test-only-password-123")
    monkeypatch.setattr(sys, "argv", ["setup_env.py", "--mode", "demo"])
    runpy.run_path(str(root / "scripts/setup_env.py"), run_name="__main__")
    env_text = (temporary_root / ".env").read_text()
    assert "test-only-password-123" not in env_text
    assert "pbkdf2_sha256" in env_text
    monkeypatch.setattr(common, "ROOT", root)
    for key, value in {"APP_MODE": "demo", "EMBEDDING_PROVIDER": "hash", "DB_BACKEND": "sqlite",
                       "DATA_DIR": str(settings.data_dir), "SIMILARITY_THRESHOLD": "0.12",
                       "ADMIN_PASSWORD_HASH": settings.admin_password_hash.get_secret_value(),
                       "USER_PASSWORD_HASH": settings.user_password_hash.get_secret_value()}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "argv", ["init_db.py"])
    runpy.run_path(str(root / "scripts/init_db.py"), run_name="__main__")
    monkeypatch.setattr(sys, "argv", ["ingest.py", str(root / "data/sample_documents")])
    runpy.run_path(str(root / "scripts/ingest.py"), run_name="__main__")
    result = settings.data_dir / "evaluation.json"
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--output", str(result)])
    runpy.run_path(str(root / "scripts/evaluate.py"), run_name="__main__")
    assert '"cases"' in result.read_text()
