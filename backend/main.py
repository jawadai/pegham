"""
FastAPI Server Entrypoint for Pegham.ai (پیغام).
Serves WebRTC/WebSocket endpoints, API health, and mounts the frontend UI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings
from backend.utils.logger import logger
from backend.services.whatsapp import whatsapp_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    """
    logger.info("💌 Starting Pegham.ai Server...")
    # Optional background initialization of services
    yield
    logger.info("Shutting down Pegham.ai Server...")
    await whatsapp_service.close()


app = FastAPI(
    title="Pegham.ai API",
    description="Voice-First WhatsApp Copilot powered by Pipecat & Playwright",
    version="0.1.0",
    lifespan=lifespan
)

# Static, Frontend, and Documentation directory paths
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DOCS_DIR = Path(__file__).parent.parent / "docs"


@app.get("/api/health")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "app": "Pegham.ai",
        "whatsapp_ready": whatsapp_service.is_ready
    }


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket channel to stream real-time UI events (Orb status, WhatsApp actions, transcripts).
    """
    await websocket.accept()
    logger.info("Frontend WebSocket connected.")
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process incoming client commands
            await websocket.send_json({"type": "ACK", "payload": data})
    except WebSocketDisconnect:
        logger.info("Frontend WebSocket disconnected.")


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

# Mount static assets if frontend directory exists
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
