from pathlib import Path

import pytest

from config.settings import Settings
from security.auth import Principal, hash_password
from services.bootstrap import build_application


@pytest.fixture(scope="session")
def password_hash():
    return hash_password("test-only-password-123")


@pytest.fixture
def settings(tmp_path, password_hash):
    return Settings(_env_file=None, app_mode="demo", embedding_provider="hash", db_backend="sqlite",
        data_dir=tmp_path, admin_password_hash=password_hash, user_password_hash=password_hash,
        similarity_threshold=0.12)


@pytest.fixture
def app(settings):
    instance = build_application(settings)
    yield instance
    instance.engine.dispose()


@pytest.fixture
def admin():
    return Principal("admin")


@pytest.fixture
def user():
    return Principal("user")


@pytest.fixture
def sample():
    path = Path(__file__).resolve().parents[1] / "data/sample_documents/employee_leave_policy.pdf"
    return path.name, path.read_bytes()
