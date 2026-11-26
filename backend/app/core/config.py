from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cognis — LMS & Data Analytics Suite"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "dev-secret-key-replace-in-prod-9f8e7d6c5b4a"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    DATABASE_URL: str = "sqlite:///./cognis.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Genuine Email & OTP Settings
    VERIFY_EMAIL_DNS: bool = True
    OTP_EXPIRE_MINUTES: int = 10
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
