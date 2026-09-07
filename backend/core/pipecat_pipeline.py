"""
Pipecat Real-Time Voice Pipeline builder for Kabootar.ai.
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

    async def build_pipeline(self):
        """
        Builds and wires together the Pipecat processors:
        - Transport Input (WebRTC Audio Stream)
        - Silero VAD (Voice Activity Detection)
        - STT (Groq Whisper / Azure ur-PK)
        - LLM Context & Function Calling (OpenAI / Groq)
        - TTS (Azure Neural / ElevenLabs)
        - Transport Output
        """
        logger.info("Assembling Pipecat Voice Pipeline...")
        # Pipeline assembly will be defined with pipecat-ai components
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
