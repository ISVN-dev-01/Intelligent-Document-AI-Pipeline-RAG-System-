import pytest
from pydantic import ValidationError

from config.settings import Settings


def test_missing_credentials_are_actionable():
    settings = Settings(_env_file=None)
    errors = " ".join(settings.startup_errors())
    assert "GOOGLE_API_KEY" in errors and "ADMIN_PASSWORD_HASH" in errors


def test_invalid_chunk_overlap():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_size=150, chunk_overlap=150)


def test_paths_anchor_to_data_directory(settings):
    assert settings.upload_dir == settings.data_dir / "data/uploads"
    assert settings.faiss_index_path == settings.data_dir / "data/vector_store"
