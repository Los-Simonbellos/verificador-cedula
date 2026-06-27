from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Security ---
    api_key: str = "changeme"

    # --- Data provider ---
    # "pnp" | "mock"
    provider: str = "mock"
    source_url: str = "https://www.sistemaspnp.com/cedula"
    http_timeout: float = 10.0
    user_agent: str = (
        "Mozilla/5.0 (compatible; verificador-cedula/0.1; +https://github.com/cuevasrja)"
    )

    # --- Cache ---
    cache_ttl_seconds: int = 3600

    # --- Logging ---
    log_level: str = "INFO"

    # --- Future: persistencia histórica ---
    history_enabled: bool = False

    # --- CORS ---
    cors_origins: list[str] = ["*"]


settings = Settings()
