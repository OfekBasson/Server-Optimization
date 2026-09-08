from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env."""

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/canvas_lab"

    # Twilio WhatsApp
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""  # e.g. "whatsapp:+14155238886"

    # Microsoft OIDC (university/Outlook accounts)
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_tenant_id: str = ""
    ms_redirect_uri: str = "http://localhost:8000/api/auth/callback"

    # Shared secret the monitoring agents authenticate with
    agent_api_key: str = "change-me"
    agent_poll_interval_minutes: int = 15

    # Signs the OAuth login session cookie
    session_secret_key: str = "change-me-too"

    # Idle-but-reserved detection
    idle_threshold_minutes: int = 120
    idle_gpu_util_percent_threshold: float = 5.0

    # Stale / long-standing reservation check-ins
    stale_reservation_days: int = 5
    nudge_cooldown_hours: int = 12

    # How often scheduled jobs run
    scheduler_interval_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
