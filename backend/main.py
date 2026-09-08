"""
FastAPI Server Entrypoint for Pegham.ai (پیغام).
Serves WebRTC/WebSocket endpoints, API health, and mounts the frontend UI.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
import asyncio
import urllib.parse
from typing import Set
from pydantic import BaseModel
from backend.utils.logger import logger
from backend.services.whatsapp import whatsapp_service
from backend.services.ai_service import ai_service

# Active WebSocket connections for broadcasting UI updates
active_connections: Set[WebSocket] = set()


async def broadcast_event(event: dict):
    for ws in list(active_connections):
        try:
            await ws.send_json(event)
        except Exception:
            active_connections.discard(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    Automatically initializes WhatsApp Web using persistent session.
    """
    logger.info("💌 Starting Pegham.ai Server...")
    # Launch WhatsApp Web service in background task so server startup isn't blocked
    whatsapp_task = asyncio.create_task(whatsapp_service.initialize())
    yield
    logger.info("Shutting down Pegham.ai Server...")
    if not whatsapp_task.done():
        whatsapp_task.cancel()
    await whatsapp_service.close()


app = FastAPI(
    title="Pegham.ai API",
    description="Voice-First WhatsApp Copilot powered by Pipecat, Groq & Playwright",
    version="0.1.0",
    lifespan=lifespan
)

# Static, Frontend, and Documentation directory paths
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DOCS_DIR = Path(__file__).parent.parent / "docs"


class ChatRequest(BaseModel):
    text: str


@app.get("/api/health")
async def health_check():
    """
    Basic health check endpoint reporting WhatsApp readiness.
    """
    return {
        "status": "healthy",
        "app": "Pegham.ai",
        "whatsapp_ready": whatsapp_service.is_ready,
        "llm_provider": settings.active_llm_provider,
        "tts_provider": settings.TTS_PROVIDER
    }


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket channel to stream real-time UI events (Orb status, WhatsApp actions, transcripts).
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info("Frontend WebSocket connected.")
    try:
        # Send initial status
        await websocket.send_json({
            "type": "STATUS",
            "whatsapp_ready": whatsapp_service.is_ready
        })
        while True:
            data = await websocket.receive_text()
            # Keepalive / echo
            await websocket.send_json({"type": "ACK", "payload": data})
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info("Frontend WebSocket disconnected.")


@app.post("/api/voice/process")
async def process_voice_audio(request: Request):
    """
    Complete Voice-to-Action pipeline:
    1. Audio -> Groq Whisper Large-v3 STT
    2. Transcript -> Groq LLaMA 3.3 70B with tools
    3. Tool -> WhatsApp Web Playwright action
    4. Response -> Edge-TTS Urdu Voice
    """
    import base64
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
            audio_b64 = payload.get("audio", "")
            if not audio_b64:
                raise HTTPException(status_code=400, detail="Missing audio in JSON")
            audio_bytes = base64.b64decode(audio_b64)
        else:
            audio_bytes = await request.body()

        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio payload")

        await broadcast_event({"type": "STATE_CHANGE", "state": "executing"})

        # 1. Transcribe audio with Groq Whisper
        transcript = await ai_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename="audio.webm"
        )
        if not transcript or not transcript.strip() or transcript.strip() in [".", "!", "?", "...", "you", "You", "Thank you."]:
            spoken = "Maazrat, awaaz samajh nahi aayi. Dobara kahiye."
            await broadcast_event({"type": "SPEAK", "text": spoken})
            await broadcast_event({"type": "STATE_CHANGE", "state": "idle"})
            return {
                "transcript": "",
                "spoken_response": spoken,
                "action": None,
                "audio_url": f"/api/tts?text={urllib.parse.quote(spoken)}"
            }

        await broadcast_event({"type": "TRANSCRIPT", "text": transcript})

        # 2. Process instruction with Groq LLaMA 3.3 70B & execute tools
        result = await ai_service.process_instruction(transcript)

        # 3. Broadcast WhatsApp action if executed
        action = result.get("action")
        if action and action.get("tool") == "send_whatsapp_message":
            args = action.get("arguments", {})
            res = action.get("result", {})
            await broadcast_event({
                "type": "WHATSAPP_ACTION",
                "contact": args.get("contact_name", "Contact"),
                "message": args.get("message", ""),
                "status": "Sent" if res.get("success") else "Failed",
                "spoken_response": result.get("spoken_response")
            })

        # 4. Broadcast spoken response
        spoken = result.get("spoken_response", "")
        if spoken:
            await broadcast_event({"type": "SPEAK", "text": spoken})

        audio_url = f"/api/tts?text={urllib.parse.quote(spoken)}" if spoken else ""
        return {
            "transcript": transcript,
            "spoken_response": spoken,
            "action": action,
            "audio_url": audio_url
        }

    except Exception as e:
        logger.error(f"Voice processing pipeline failed: {e}")
        await broadcast_event({"type": "STATE_CHANGE", "state": "idle"})
        return {"error": str(e), "transcript": "", "spoken_response": "Maazrat, awaaz samajh nahi aayi. Dobara kahiye."}


@app.post("/api/chat")
async def process_text_chat(req: ChatRequest):
    """
    Direct text chat endpoint for testing commands without speaking.
    """
    text = req.text.strip()
    if not text:
        return {"error": "Empty text"}

    await broadcast_event({"type": "TRANSCRIPT", "text": text})
    await broadcast_event({"type": "STATE_CHANGE", "state": "executing"})

    result = await ai_service.process_instruction(text)

    action = result.get("action")
    if action and action.get("tool") == "send_whatsapp_message":
        args = action.get("arguments", {})
        res = action.get("result", {})
        await broadcast_event({
            "type": "WHATSAPP_ACTION",
            "contact": args.get("contact_name", "Contact"),
            "message": args.get("message", ""),
            "status": "Sent" if res.get("success") else "Failed",
            "spoken_response": result.get("spoken_response")
        })

    spoken = result.get("spoken_response", "")
    if spoken:
        await broadcast_event({"type": "SPEAK", "text": spoken})

    audio_url = f"/api/tts?text={urllib.parse.quote(spoken)}" if spoken else ""
    return {
        "transcript": text,
        "spoken_response": spoken,
        "action": action,
        "audio_url": audio_url
    }


# Serve index.html at root
@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Pegham.ai API is running. Frontend index.html not found."}


# Serve interactive documentation portal at /guide
@app.get("/guide")
async def serve_guide():
    guide_file = DOCS_DIR / "index.html"
    if guide_file.exists():
        return FileResponse(guide_file)
    return {"message": "Documentation guide not found. Run python scripts/build_docs_html.py"}


# Neural Speech Synthesis Endpoint (100% Free Edge-TTS: Zero Azure Key Required)
@app.get("/api/tts")
async def get_tts_audio(text: str):
    """
    Synthesizes text into high-fidelity Urdu speech (MP3) using edge-tts.
    Zero Azure keys or cloud subscriptions required!
    """
    from fastapi.responses import StreamingResponse, Response
    if not text:
        return Response(status_code=400, content="Missing text query parameter")
    from backend.services.tts import tts_service
    return StreamingResponse(
        tts_service.synthesize_stream(text),
        media_type="audio/mpeg"
    )

# Mount static assets if frontend directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        app_dir=str(PROJECT_ROOT)
    )
