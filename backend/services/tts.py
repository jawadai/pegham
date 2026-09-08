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

        import re
        # Clean text of emojis and special markdown symbols that can confuse Edge-TTS
        clean_text = re.sub(r'[^\w\s\d.,!?:;\'"۔،؟\u0600-\u06FF]', ' ', text).strip()
        if not clean_text:
            clean_text = text.strip()

        # Check if text contains Urdu script characters
        has_urdu_script = bool(re.search(r'[\u0600-\u06FF]', clean_text))
        if has_urdu_script:
            # Native Pakistani Urdu neural voices with Roman Urdu fallback
            candidate_voices = ["ur-PK-UzmaNeural", "ur-PK-AsadNeural", "ur-IN-GulNeural", "en-IN-NeerjaNeural"]
        else:
            # Authentic bilingual South Asian voices for Roman Urdu & English
            candidate_voices = ["en-IN-NeerjaNeural", "en-IN-PrabhatNeural", "ur-PK-UzmaNeural", "en-US-JennyNeural"]

        for voice_name in candidate_voices:
            try:
                communicate = edge_tts.Communicate(text=clean_text, voice=voice_name)
                audio_yielded = False
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_yielded = True
                        yield chunk["data"]
                if audio_yielded:
                    return
            except Exception as e:
                logger.warning(f"Voice {voice_name} failed: {e}. Trying fallback voice...")

    async def synthesize_bytes(self, text: str) -> bytes:
        """
        Synthesizes complete audio bytes into an in-memory buffer.
        """
        audio = bytearray()
        async for chunk in self.synthesize_stream(text):
            audio.extend(chunk)
        return bytes(audio)


tts_service = TTSService()
