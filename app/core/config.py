"""Environment-backed application settings.

Secrets are read from the environment. They are never given production values
in source code.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _blank_to_default(value: object, default: str) -> object:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Instagram DM Automation"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: str = ""

    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = "http://localhost:8000/api/v1/instagram/callback"
    meta_api_version: str = ""
    meta_graph_base_url: str = "https://graph.instagram.com"
    meta_oauth_authorize_url: str = "https://www.instagram.com/oauth/authorize"
    meta_oauth_token_url: str = "https://api.instagram.com/oauth/access_token"
    # Documented Business Login scopes. Confirm the set granted to your app
    # in the Meta App Dashboard before using a real authorization URL.
    meta_oauth_scopes: str = (
        "instagram_business_basic,"
        "instagram_business_manage_comments,"
        "instagram_business_manage_messages"
    )
    meta_webhook_verify_token: str = ""
    meta_webhook_fields: str = "comments"

    # Postgres async URL, e.g. postgresql+asyncpg://user:pass@host/dbname
    # Leave empty to keep using the in-memory repositories.
    database_url: str = "postgresql+asyncpg://postgres:00000@localhost:5432/my_test_db"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    task_execution_mode: str = "inline"

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    log_level: str = "INFO"

    llm_provider: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    mock_external_services: bool = False
    seed_demo_data: bool = False

    cors_origins: str = "http://localhost:5173"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"

    rate_limit_enabled: bool = True
    rate_limit_backend: str = "memory"
    rate_limit_auth_per_minute: int = 20
    rate_limit_automation_create_per_minute: int = 30
    rate_limit_instagram_per_minute: int = 60
    rate_limit_webhook_per_minute: int = 300

    retry_base_seconds: float = 0.5
    retry_max_attempts: int = 5
    request_max_body_bytes: int = Field(default=1_048_576)

    @field_validator("meta_graph_base_url", mode="before")
    @classmethod
    def _default_graph_base(cls, value: object) -> object:
        return _blank_to_default(value, "https://graph.instagram.com")

    @field_validator("meta_oauth_authorize_url", mode="before")
    @classmethod
    def _default_authorize_url(cls, value: object) -> object:
        return _blank_to_default(value, "https://www.instagram.com/oauth/authorize")

    @field_validator("meta_oauth_token_url", mode="before")
    @classmethod
    def _default_token_url(cls, value: object) -> object:
        return _blank_to_default(value, "https://api.instagram.com/oauth/access_token")

    @field_validator("meta_api_version", mode="before")
    @classmethod
    def _strip_version(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip("/")
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env.lower() == "test"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        hosts = [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]
        if not self.is_production and "testserver" not in hosts:
            hosts.append("testserver")
        return hosts

    @property
    def oauth_scope_list(self) -> list[str]:
        return [item.strip() for item in self.meta_oauth_scopes.split(",") if item.strip()]

    @property
    def resolved_jwt_secret(self) -> str:
        if self.jwt_secret.strip():
            return self.jwt_secret
        if self.is_production:
            raise RuntimeError("JWT_SECRET is required in production")
        return "dev-only-insecure-jwt-secret"

    @property
    def resolved_secret_key(self) -> str:
        if self.secret_key.strip():
            return self.secret_key
        if self.is_production:
            raise RuntimeError("SECRET_KEY is required in production")
        return "dev-only-insecure-secret-key"

    @property
    def use_celery(self) -> bool:
        return self.task_execution_mode.lower() == "celery"


def validate_settings(settings: Settings) -> None:
    """Refuse an unsafe production configuration at startup."""
    if not settings.is_production:
        return
    problems: list[str] = []
    if settings.mock_external_services:
        problems.append("MOCK_EXTERNAL_SERVICES must be false in production")
    if not settings.jwt_secret.strip():
        problems.append("JWT_SECRET must be set in production")
    if not settings.secret_key.strip():
        problems.append("SECRET_KEY must be set in production")
    if not settings.meta_app_secret.strip():
        problems.append("META_APP_SECRET must be set in production")
    if not settings.meta_webhook_verify_token.strip():
        problems.append("META_WEBHOOK_VERIFY_TOKEN must be set in production")
    origins = settings.cors_origin_list
    if not origins or "*" in origins:
        problems.append("CORS_ORIGINS must be an explicit allow-list in production")
    if "*" in settings.trusted_host_list:
        problems.append("TRUSTED_HOSTS must not contain '*' in production")
    if problems:
        raise RuntimeError("Invalid production configuration: " + "; ".join(problems))


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    validate_settings(settings)
    return settings
