"""
Neural Text-to-Speech service for Pegham.ai.
Supports 100% Free Edge-TTS (Urdu ur-PK) with zero API keys or Azure accounts needed.
"""

import asyncio
from typing import AsyncGenerator, Optional
from backend.config import settings
from backend.utils.logger import logger

try:
    import edge_tts
except ImportError:
    edge_tts = None


class TTSService:
    """
    Asynchronous Text-to-Speech service.
    Defaults to 100% free edge-tts using native Microsoft Urdu neural voices.
    """

    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self.voice = settings.EDGE_TTS_VOICE

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Streams MP3 audio chunks using edge-tts without requiring an Azure key.
        """
        if not edge_tts:
            logger.warning("edge-tts library is not installed. Install via: pip install edge-tts")
            return

        logger.info(f"🎙️ Synthesizing speech with edge-tts (voice={self.voice}): '{text}'")
        try:
            communicate = edge_tts.Communicate(text=text, voice=self.voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except Exception as e:
            logger.error(f"Failed to synthesize audio with edge-tts: {e}")

    async def synthesize_bytes(self, text: str) -> bytes:
        """
        Synthesizes complete audio bytes into an in-memory buffer.
        """
        audio = bytearray()
        async for chunk in self.synthesize_stream(text):
            audio.extend(chunk)
        return bytes(audio)


tts_service = TTSService()
