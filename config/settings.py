from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    SERP_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()