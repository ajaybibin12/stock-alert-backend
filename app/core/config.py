from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    FINNHUB_API_KEY: str | None = None

    # ✅ EMAIL SETTINGS (REQUIRED)
    EMAIL_HOST: str
    EMAIL_PORT: int     # ✅ MUST BE INT
    EMAIL_USER: str
    EMAIL_PASS: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()


