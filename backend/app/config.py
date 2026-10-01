"""Backend service configuration."""

from typing import List, Union
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ROKOSPY_BACKEND_",
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "rokospy-backend"
    VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MAX_UPLOAD_SIZE_MB: int = 100

    # Supabase PostgreSQL Configuration
    SUPABASE_URL: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_URL", "ROKOSPY_BACKEND_SUPABASE_URL"),
    )
    SUPABASE_SERVICE_ROLE_KEY: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "ROKOSPY_BACKEND_SUPABASE_SERVICE_ROLE_KEY"),
    )
    SUPABASE_ANON_KEY: Union[str, None] = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "ROKOSPY_BACKEND_SUPABASE_ANON_KEY"),
    )

    # CORS origins: comma-separated string or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


backend_config = BackendConfig()
