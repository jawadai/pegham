"""
Configuration management for Pegham.ai using Pydantic Settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Voice AI Credentials
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = "eastus"
    ELEVENLABS_API_KEY: str = ""

    # Pipecat & Transport
    PIPECAT_TRANSPORT: str = "webrtc"  # webrtc, daily, websocket
    DAILY_API_KEY: str = ""
    DAILY_SAMPLE_ROOM_URL: str = ""

    # WhatsApp Automation
    WHATSAPP_SESSION_DIR: str = "./whatsapp_session"
    WHATSAPP_HEADLESS: bool = False
    WHATSAPP_PAGE_TIMEOUT_MS: int = 60000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def session_path(self) -> Path:
        path = Path(self.WHATSAPP_SESSION_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
