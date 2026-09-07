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

    async def _call_llm(self, messages: list, tools: Optional[list] = None):
        """
        Calls Groq chat completions with automatic fallback across supported models
        in case a specific model is not accessible or deprecated.
        """
        candidate_models = [
            settings.GROQ_LLM_MODEL,
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "llama3-70b-8192",
            "llama3-8b-8192"
        ]
        # De-duplicate while preserving order
        models = []
        for m in candidate_models:
            if m and m not in models:
                models.append(m)

        last_error = None
        for model_name in models:
            try:
                kwargs: Dict[str, Any] = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.3
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = await self.client.chat.completions.create(**kwargs)
                return response
            except Exception as e:
                err_str = str(e).lower()
                if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
                    logger.warning(f"Groq model '{model_name}' not found. Trying fallback...")
                    last_error = e
                    continue
                raise e

        raise last_error or RuntimeError("No accessible Groq models available.")

    async def process_instruction(self, user_text: str) -> Dict[str, Any]:
        """
        Processes user text with Groq LLM Brain, dispatches tool calls,
        and generates a concise verbal response in Urdu/Roman Urdu.
        """
        if not self.client:
            self._init_client()
        if not self.client:
            raise ValueError("Groq API key is missing. Set GROQ_API_KEY in .env.")

        logger.info(f"🧠 Processing instruction with Groq: \"{user_text}\"")

        messages = [
            {"role": "system", "content": PEGHAM_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]

        # 1. Call LLM with WhatsApp tools (with automatic model fallback)
        response = await self._call_llm(messages=messages, tools=WHATSAPP_TOOLS)

        response_message = response.choices[0].message
        action_result: Optional[Dict[str, Any]] = None

        # 2. Check if the model called any tools
        if response_message.tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": response_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in response_message.tool_calls
                ]
            }
            messages.append(assistant_msg)

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

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_output, ensure_ascii=False)
                })

            # Call LLM again to synthesize a crisp verbal confirmation
            try:
                second_response = await self._call_llm(messages=messages)
                spoken_response = (second_response.choices[0].message.content or "").strip()
            except Exception as e:
                logger.warning(f"Secondary confirmation LLM call failed: {e}")
                contact = (action_result.get("arguments") or {}).get("contact_name", "Contact")
                if action_result.get("result", {}).get("success"):
                    spoken_response = f"{contact} ko message bhej diya hai!"
                else:
                    err_msg = action_result.get("result", {}).get("error", "Chat nahi khul saki")
                    spoken_response = f"{contact} ko message nahi ja saka. {err_msg}"
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

