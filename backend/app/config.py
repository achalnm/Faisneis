from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="gemini", description="gemini or groq")

    anthropic_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)

    gemini_model: str = Field(default="gemini-2.5-flash")

    embed_model: str = Field(default="all-MiniLM-L6-v2")

    ingest_date_start: str = Field(default="2020-01-01")
    ingest_date_end: Optional[str] = Field(default=None)

    chroma_dir: Path = Field(default=Path("./data/chroma"))
    cache_dir: Path = Field(default=Path("./data/cache"))

    def model_post_init(self, __context):
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
