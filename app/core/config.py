from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    FINNHUB_API_KEY: str | None = None

    # ✅ EMAIL SETTINGS
    EMAIL_PROVIDER: str = "sendgrid"

    # SMTP (optional)
    EMAIL_HOST: str | None = None
    EMAIL_PORT: int | None = None
    EMAIL_USER: str | None = None
    EMAIL_PASS: str | None = None

    # SendGrid
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str | None = None

    BACKEND_URL: str

    # ✅ QSTASH SETTINGS
    QSTASH_URL: str
    QSTASH_TOKEN: str
    QSTASH_CURRENT_SIGNING_KEY: str
    QSTASH_NEXT_SIGNING_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
