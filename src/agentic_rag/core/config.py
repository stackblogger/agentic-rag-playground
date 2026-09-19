from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/agentic_rag"
    upload_dir: str = "data/uploads"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"


settings = Settings()
