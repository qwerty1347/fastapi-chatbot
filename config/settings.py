from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str | None

    QDRANT_HOST: str

    LANGCHAIN_TRACING_V2: str
    LANGCHAIN_ENDPOINT: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str

    GROQ_API_KEY: str
    SERP_API_KEY: str
    STORAGE_PATH: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()