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

    # LLM & Conversational Brain (Defaults to 100% Free Groq Llama 3.3 70B)
    LLM_PROVIDER: str = "groq"  # Options: "groq", "ollama", "openai", "anthropic"
    GROQ_API_KEY: str = ""
    GROQ_LLM_MODEL: str = "openai/gpt-oss-20b"

    # Optional / Alternative LLM Providers
    OPENAI_API_KEY: str = ""
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""

    # Local Offline Ollama Provider (100% Offline & Free)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3.2"

    # Voice Synthesis Configuration (100% Free with Edge-TTS: Zero Azure Key Required!)
    TTS_PROVIDER: str = "edge_tts"  # Options: "edge_tts", "azure", "elevenlabs"
    EDGE_TTS_VOICE: str = "ur-PK-UzmaNeural"  # or "ur-PK-AsadNeural"

    # Optional Voice Synthesis Credentials
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

    @property
    def active_llm_provider(self) -> str:
        """
        Determines the active LLM brain provider. Defaults to 100% free Groq Llama 3.3.
        """
        if self.LLM_PROVIDER == "ollama":
            return "ollama"
        if self.LLM_PROVIDER == "openai" and self.OPENAI_API_KEY:
            return "openai"
        if self.LLM_PROVIDER == "anthropic" and self.ANTHROPIC_API_KEY:
            return "anthropic"
        if self.GROQ_API_KEY:
            return "groq"
        if self.OPENAI_API_KEY:
            return "openai"
        return "groq"


settings = Settings()
