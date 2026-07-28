from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "kronvel-backend"
    environment: str = "development"
    log_level: str = "INFO"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Postgres
    database_url: str = "postgresql://kronvel:kronvel@localhost:5432/kronvel"

    # Prometheus (used starting Day 3)
    prometheus_url: str = "http://localhost:9090"

    # Kubernetes (Day 4+) — see SECURITY.md for the scoped ServiceAccount this must use
    kube_config_path: str | None = None
    kube_in_cluster: bool = False

# LLM provider (Day 5+)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-5-mini"

    # Pipeline (Day 3+)
    pipeline_poll_interval_seconds: int = 5
    anomaly_temp_z_threshold: float = 3.0
    anomaly_temp_absolute_threshold_c: float = 85.0
    anomaly_temp_critical_threshold_c: float = 95.0

    # Remediation safety default (used starting Day 6, defined now so it's never forgotten later)
    dry_run_default: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()