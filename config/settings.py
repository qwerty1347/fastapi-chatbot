from pydantic import BaseSettings

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str | None
    GROQ_API_KEY: str
    SERP_API_KEY: str
    STORAGE_PATH: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()