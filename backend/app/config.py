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

    # CORS origins: comma-separated string, JSON list, or list
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,https://dr-roposky.vercel.app",
        validation_alias=AliasChoices("CORS_ORIGINS", "ROKOSPY_BACKEND_CORS_ORIGINS"),
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        if not v:
            return ["http://localhost:3000", "http://127.0.0.1:3000", "https://dr-roposky.vercel.app"]
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(o).strip().rstrip("/") for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [origin.strip().rstrip("/") for origin in v_str.split(",") if origin.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(origin).strip().rstrip("/") for origin in v if str(origin).strip()]
        return ["http://localhost:3000", "http://127.0.0.1:3000", "https://dr-roposky.vercel.app"]


backend_config = BackendConfig()
