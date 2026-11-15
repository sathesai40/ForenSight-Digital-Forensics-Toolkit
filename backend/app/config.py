from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ForenSight Digital Forensics Toolkit"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # Network Binding
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS configuration - strictly constrained for development security
    allowed_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Forensic Data Storage Paths
    sqlite_db_path: str = "./data/forensight.db"
    evidence_vault_dir: str = "./data/vault"
    reports_dir: str = "./data/reports"
    max_evidence_size_mb: int = 25

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def database_url(self) -> str:
        # SQLite connection string
        db_path = Path(self.sqlite_db_path)
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path.as_posix()}"

    def ensure_directories(self) -> None:
        """Ensure storage paths exist upon startup."""
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.evidence_vault_dir).mkdir(parents=True, exist_ok=True)
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
