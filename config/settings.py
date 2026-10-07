"""Validated environment settings; relative runtime paths are anchored outside the repo."""
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_mode: Literal["google", "demo"] = "google"
    data_dir: Path = Path.home() / ".document_ai"
    google_api_key: SecretStr = SecretStr("")
    embedding_provider: Literal["google", "hash"] = "google"
    embedding_model: str = "models/gemini-embedding-001"
    llm_model: str = "gemini-3.8-flash"
    llm_temperature: float = Field(0.2, ge=0, le=1)
    db_backend: Literal["mysql", "sqlite"] = "mysql"
    mysql_host: str = "localhost"
    mysql_port: int = Field(3306, ge=1, le=65535)
    mysql_database: str = "document_ai"
    mysql_user: str = "document_ai"
    mysql_password: SecretStr = SecretStr("")
    auto_create_tables: bool = True
    faiss_index_path: Path = Path("data/vector_store")
    upload_dir: Path = Path("data/uploads")
    chunk_size: int = Field(1000, ge=100, le=4000)
    chunk_overlap: int = Field(150, ge=0)
    top_k: int = Field(5, ge=1, le=30)
    similarity_threshold: float = Field(0.35, ge=-1, le=1)
    max_upload_mb: int = Field(20, ge=1, le=100)
    max_pdf_pages: int = Field(300, ge=1, le=1000)
    max_extracted_chars: int = Field(2_000_000, ge=1000)
    max_question_chars: int = Field(2000, ge=10, le=10000)
    max_context_chars: int = Field(12000, ge=1000, le=60000)
    memory_turns: int = Field(3, ge=0, le=5)
    api_timeout_seconds: int = Field(60, ge=5, le=180)
    admin_password_hash: SecretStr = SecretStr("")
    user_password_hash: SecretStr = SecretStr("")
    audit_store_text: bool = True

    @field_validator("data_dir", mode="before")
    @classmethod
    def default_data_dir(cls, value):
        return value or Path.home() / ".document_ai"

    @model_validator(mode="after")
    def validate_combination(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        if self.app_mode == "demo" and self.embedding_provider != "hash":
            raise ValueError("Demo mode requires EMBEDDING_PROVIDER=hash.")
        if self.app_mode == "google" and self.embedding_provider != "google":
            raise ValueError("Google mode requires EMBEDDING_PROVIDER=google.")
        self.data_dir = self.data_dir.expanduser().resolve()
        for name in ("faiss_index_path", "upload_dir"):
            path = getattr(self, name).expanduser()
            setattr(self, name, (self.data_dir / path).resolve())
        return self

    def startup_errors(self) -> list[str]:
        errors = []
        if self.app_mode == "google" and not self.google_api_key.get_secret_value():
            errors.append("GOOGLE_API_KEY is not configured. Create .env using .env.example.")
        if not self.admin_password_hash.get_secret_value():
            errors.append("ADMIN_PASSWORD_HASH is missing. Run python scripts/setup_env.py.")
        if not self.user_password_hash.get_secret_value():
            errors.append("USER_PASSWORD_HASH is missing. Run python scripts/setup_env.py.")
        if self.db_backend == "mysql" and not self.mysql_password.get_secret_value():
            errors.append("MYSQL_PASSWORD is not configured.")
        return errors
