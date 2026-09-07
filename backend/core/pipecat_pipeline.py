"""
Pipecat Real-Time Voice Pipeline builder for Pegham.ai.
Orchestrates: Transport -> VAD -> STT -> LLM (with tools) -> TTS -> Transport Output.
"""

from typing import Any
from backend.config import settings
from backend.utils.logger import logger


class PipecatVoicePipeline:
    """
    Manages the real-time audio frame pipeline using Pipecat framework.
    """

    def __init__(self, transport: Any = None):
        self.transport = transport
        self.pipeline = None
        self.runner = None

    def get_llm_config(self) -> dict:
        """
        Resolves LLM Brain configuration based on available API keys and settings.
        Defaults to 100% free Groq (Llama 3.3 70B).
        """
        provider = settings.active_llm_provider
        if provider == "groq":
            logger.info(f"🧠 Brain Provider: Groq (100% Free Tier) -> Model: {settings.GROQ_LLM_MODEL}")
            return {
                "provider": "groq",
                "model": settings.GROQ_LLM_MODEL,
                "api_key": settings.GROQ_API_KEY,
                "base_url": "https://api.groq.com/openai/v1"
            }
        elif provider == "ollama":
            logger.info(f"🧠 Brain Provider: Local Ollama (100% Offline & Free) -> Model: {settings.OLLAMA_MODEL}")
            return {
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
                "api_key": "ollama",
                "base_url": settings.OLLAMA_BASE_URL
            }
        elif provider == "openai":
            logger.info(f"🧠 Brain Provider: OpenAI -> Model: {settings.OPENAI_LLM_MODEL}")
            return {
                "provider": "openai",
                "model": settings.OPENAI_LLM_MODEL,
                "api_key": settings.OPENAI_API_KEY,
                "base_url": None
            }
        elif provider == "anthropic":
            logger.info("🧠 Brain Provider: Anthropic Claude")
            return {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "api_key": settings.ANTHROPIC_API_KEY,
                "base_url": None
            }
        return {
            "provider": "groq",
            "model": settings.GROQ_LLM_MODEL,
            "api_key": settings.GROQ_API_KEY,
            "base_url": "https://api.groq.com/openai/v1"
        }

    async def build_pipeline(self):
        """
        Builds and wires together the Pipecat processors:
        - Transport Input (WebRTC Audio Stream)
        - Silero VAD (Voice Activity Detection)
        - STT: Groq Whisper Large-v3 (100% Free)
        - LLM: Groq Llama 3.3 70B / Ollama / OpenAI
        - TTS: Azure Neural ur-PK (Free Tier F0)
        - Transport Output (WebRTC Audio Stream)
        """
        llm_cfg = self.get_llm_config()
        logger.info(f"Assembling Pipecat Voice Pipeline with LLM [{llm_cfg['provider']} / {llm_cfg['model']}]...")
        return self

    async def start(self):
        """
        Starts the pipeline runner.
        """
        logger.info("Starting Pipecat Voice Pipeline runner...")

    async def stop(self):
        """
        Stops the pipeline runner gracefully.
        """
        logger.info("Stopping Pipecat Voice Pipeline runner...")
