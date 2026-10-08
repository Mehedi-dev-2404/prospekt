from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Anthropic Claude API
    ANTHROPIC_API_KEY: str

    # Google Places API
    GOOGLE_PLACES_API_KEY: str

    # Dashboard (Next.js app replacing Google Sheets for approvals/monitoring)
    DASHBOARD_URL: Optional[str] = None

    # Gmail API (optional)
    GMAIL_CREDENTIALS_PATH: Optional[str] = None
    GMAIL_TOKEN_JSON: Optional[str] = None

    # Vercel
    VERCEL_API_TOKEN: str
    VERCEL_TEAM_ID: Optional[str] = None

    # Email (Gmail)
    GMAIL_FROM_EMAIL: str

    # Hunter.io
    HUNTER_API_KEY: Optional[str] = None

    # Slack
    SLACK_WEBHOOK_URL: str

    # App settings
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
