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

    llm_provider: str = Field(default="claude", description="claude or gemini")

    anthropic_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)

    claude_model: str = Field(default="claude-sonnet-4-6")
    gemini_model: str = Field(default="gemini-1.5-flash")

    embed_model: str = Field(default="all-MiniLM-L6-v2")

    ingest_date_start: str = Field(default="2020-01-01")
    ingest_date_end: Optional[str] = Field(default=None)

    # Pinecone replaces local Chroma for cloud deployments
    pinecone_api_key: Optional[str] = Field(default=None)
    pinecone_index: str = Field(default="faisneis-speeches")

    # Kept for local dev / migration scripts
    chroma_dir: Path = Field(default=Path("./data/chroma"))
    cache_dir: Path = Field(default=Path("./data/cache"))

    allowed_origins: str = Field(default="")

    def model_post_init(self, __context):
        if not self.claude_model:
            self.claude_model = "claude-sonnet-4-6"
        if not self.gemini_model:
            self.gemini_model = "gemini-2.5-flash"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if not self.pinecone_api_key:
            self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
