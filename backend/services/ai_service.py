"""
Unified AI Brain & Voice Processing Service for Pegham.ai.
Integrates Groq Whisper Large-v3 (STT) + Groq LLaMA 3.3 70B (Brain & Tools).
100% Free with zero cloud subscriptions.
"""

import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from backend.config import settings
from backend.utils.logger import logger
from backend.core.prompts import PEGHAM_SYSTEM_PROMPT
from backend.core.tools import WHATSAPP_TOOLS, handle_tool_call


class AIService:
    """
    Coordinates speech transcription, conversational intelligence, and tool execution.
    """

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if settings.GROQ_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
        elif settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            )
        else:
            logger.warning("No API key configured for Groq or OpenAI in .env")

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """
        Transcribes voice audio using Groq Whisper Large-v3.
        Supports Pakistani Urdu, Roman Urdu, and English.
        """
        if not self.client:
            self._init_client()
        if not self.client:
            raise ValueError("Groq API key is missing. Set GROQ_API_KEY in .env.")

        logger.info(f"🎙️ Transcribing {len(audio_bytes)} bytes of audio using Whisper Large-v3...")
        try:
            transcription = await self.client.audio.transcriptions.create(
                file=(filename, audio_bytes, "audio/webm"),
                model="whisper-large-v3",
                prompt="Pakistani Urdu, Roman Urdu, English conversational voice input for Pegham WhatsApp assistant.",
                response_format="text",
                temperature=0.0
            )
            text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
            logger.info(f"📝 Recognized Speech: \"{text}\"")
            return text
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise e

    async def process_instruction(self, user_text: str) -> Dict[str, Any]:
        """
        Processes user text with Groq LLaMA 3.3 70B, dispatches tool calls,
        and generates a concise verbal response in Urdu/Roman Urdu.
        """
        if not self.client:
            self._init_client()
        if not self.client:
            raise ValueError("Groq API key is missing. Set GROQ_API_KEY in .env.")

        logger.info(f"🧠 Processing instruction with LLaMA 3.3 70B: \"{user_text}\"")

        messages = [
            {"role": "system", "content": PEGHAM_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]

        # 1. Call LLM with WhatsApp tools
        response = await self.client.chat.completions.create(
            model=settings.GROQ_LLM_MODEL,
            messages=messages,
            tools=WHATSAPP_TOOLS,
            tool_choice="auto",
            temperature=0.3
        )

        response_message = response.choices[0].message
        action_result: Optional[Dict[str, Any]] = None

        # 2. Check if the model called any tools
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except Exception:
                    function_args = {}

                logger.info(f"⚡ Executing Tool [{function_name}] with args: {function_args}")
                tool_output = await handle_tool_call(function_name, function_args)
                action_result = {
                    "tool": function_name,
                    "arguments": function_args,
                    "result": tool_output
                }

                # Append assistant tool call & tool response to messages for final reply
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_output, ensure_ascii=False)
                })

            # Call LLM again to synthesize a crisp verbal confirmation
            second_response = await self.client.chat.completions.create(
                model=settings.GROQ_LLM_MODEL,
                messages=messages,
                temperature=0.3
            )
            spoken_response = second_response.choices[0].message.content.strip()
        else:
            spoken_response = (response_message.content or "").strip()

        logger.info(f"🗣️ Pegham Spoken Response: \"{spoken_response}\"")

        return {
            "transcript": user_text,
            "spoken_response": spoken_response,
            "action": action_result
        }


# Global AI Service Instance
ai_service = AIService()
