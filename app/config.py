from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ModelProvider = Literal["gpt", "claude", "gemini", "llama", "mistral"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"

    model_provider: ModelProvider = "gpt"
    model_name: str = "gpt-4o-mini"

    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-10-21"

    azure_openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    mistral_api_key: SecretStr | None = None

    ollama_base_url: str = "http://localhost:11434"

    max_research_steps: int = Field(default=5, ge=1, le=15)
    max_sources: int = Field(default=8, ge=1, le=20)
    max_output_tokens: int = Field(default=1500, ge=100, le=4000)

    request_timeout_seconds: float = Field(default=30, ge=5, le=120)
    max_retries: int = Field(default=2, ge=0, le=5)

    database_url: str = "sqlite:///./research.db"

    @model_validator(mode="after")
    def validate_settings(self):
        if self.environment == "production":
            if self.database_url.startswith("sqlite:"):
                raise ValueError("Production requires external database storage.")

            if self.model_provider == "gpt":
                if not self.azure_openai_endpoint:
                    raise ValueError("Azure OpenAI endpoint is required.")

                if not self.azure_openai_deployment:
                    raise ValueError("Azure OpenAI deployment is required.")

        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
