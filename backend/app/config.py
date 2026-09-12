from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env."""

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/canvas_lab"

    # Twilio WhatsApp - messages are only ever actually sent when this is
    # true (on top of having real Twilio credentials set). Leave it false
    # to keep every notification going to the log instead, e.g. while
    # testing.
    notifications_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""  # e.g. "whatsapp:+14155238886"

    # Which origin(s) the frontend is served from (comma-separated for CORS).
    cors_origins: str = "http://localhost:5173"

    # Shared secret the monitoring agents authenticate with
    agent_api_key: str = "change-me"
    agent_poll_interval_minutes: int = 15

    # Signs the "who are you" session cookie
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
