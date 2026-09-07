# 03 — Codebase Guided Tour & Data Contracts

This document provides a line-level and module-level walkthrough of the entire Pegham.ai repository. Use this to understand how control flows through the codebase and how data structures are passed between layers.

---

## 🗂️ Complete Directory Layout

```text
Pegham/
├── README.md                     # Public documentation and quickstart
├── pyproject.toml                # Standard PEP 517/621 packaging metadata
├── requirements.txt              # Pinned production Python dependencies
├── .env.example                  # Environment configuration template
├── .gitignore                    # Prevents leaking ./whatsapp_session and secrets
│
├── backend/                      # Python Async Backend Core
│   ├── __init__.py               # Package metadata (__version__ = "0.1.0")
│   ├── main.py                   # FastAPI server, WebSockets, static file server
│   ├── config.py                 # Pydantic V2 settings and path resolver
│   │
│   ├── core/                     # Voice AI Pipeline & Intelligence
│   │   ├── __init__.py
│   │   ├── pipecat_pipeline.py   # Pipecat DAG pipeline builder
│   │   ├── prompts.py            # Urdish system prompt & voice personality
│   │   └── tools.py              # LLM function calling schemas and execution dispatcher
│   │
│   ├── services/                 # Hardware & Browser Automation Services
│   │   ├── __init__.py
│   │   └── whatsapp.py           # Playwright Chromium persistent automation engine
│   │
│   └── utils/                    # Shared Utilities
│       ├── __init__.py
│       └── logger.py             # Loguru structured logging configuration
│
├── frontend/                     # Modern Web Client (The "Command Orb")
│   ├── index.html                # Single-page UI with Tailwind CSS
│   ├── css/
│   │   └── style.css             # Keyframe animations for Voice Orb states
│   └── js/
│       ├── app.js                # State machine, WebSocket handler, push-to-talk
│       └── audio.js              # Hardware microphone capture with AEC
│
├── docs/                         # Developer & Architecture Knowledge Hub
│   ├── README.md
│   ├── 01_system_architecture.md
│   ├── 02_technology_stack_deep_dive.md
│   ├── 03_codebase_walkthrough.md
│   ├── 04_playwright_whatsapp_mechanics.md
│   ├── 05_voice_agent_and_prompt_engineering.md
│   └── 06_frontend_and_audio_engineering.md
│
└── scripts/                      # Developer CLI Utilities
    ├── setup_whatsapp.py         # One-time QR code authenticator
    └── test_whatsapp.py          # Standalone headless message test script
```

---

## 🔬 Backend Module Walkthrough

### 1. `backend/config.py` — Settings & Path Resolution
Uses **Pydantic Settings** (`pydantic_settings.BaseSettings`) to load and validate environment variables with type safety:
* **Server Settings:** `HOST` (`0.0.0.0`), `PORT` (`8000`), `DEBUG` (`bool`).
* **Credentials:** `OPENAI_API_KEY`, `GROQ_API_KEY`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`.
* **Automation Parameters:** `WHATSAPP_SESSION_DIR` (`./whatsapp_session`), `WHATSAPP_HEADLESS` (`bool`).
* **`session_path` Property:** Dynamically resolves the session directory into an absolute `pathlib.Path` and ensures it exists via `mkdir(parents=True, exist_ok=True)`.

### 2. `backend/main.py` — Application Entrypoint & Event Hub
* **`lifespan` Context Manager:** FastAPI modern lifecycle handler. Initializes services on boot and guarantees graceful cleanup (closing the Playwright browser context) on server shutdown.
* **`GET /api/health`:** Lightweight status probe returning `{"status": "healthy", "app": "Pegham.ai", "whatsapp_ready": bool}`. The frontend polls this on connect.
* **`WebSocket /ws/events`:** Real-time bi-directional channel streaming event envelopes between the Python backend and the browser interface.
* **Static File Mount:** Mounts the `frontend/` folder to `/static`, serving HTML, CSS, and JS to the browser.

### 3. `backend/core/prompts.py` — Voice Personality & Guardrails
Contains `PEGHAM_SYSTEM_PROMPT` (with `KABOOTAR_SYSTEM_PROMPT` aliased for backward compatibility):
* Instructs the LLM to speak in natural, colloquial **Urdish** (Roman Urdu + English).
* Enforces a strict **1–2 sentence maximum** rule for verbal responses (preventing unlistenable wall-of-text TTS output).
* Defines direct confirmation phrasing (*"Ali ko message bhej diya hai!"*).

### 4. `backend/core/tools.py` — LLM Tool Definitions
Exports the standard OpenAI / Groq tool definitions:
* **`send_whatsapp_message`:** Requires `contact_name` (`string`) and `message` (`string`).
* **`check_unread_messages`:** Scans unread chat badges.
* **`handle_tool_call(function_name, arguments)`:** Asynchronously routes LLM function invocations directly to `backend.services.whatsapp.whatsapp_service`.

### 5. `backend/services/whatsapp.py` — Playwright Automation Engine
Encapsulates all browser control:
* **`initialize()`:** Launches Chromium using `launch_persistent_context` pointed at `./whatsapp_session`.
* **`send_message(contact_name, message)`:** Locates the chat search bar, selects the contact, enters text into the WhatsApp Web contenteditable input field, and triggers the send event.
* **`close()`:** Safely shuts down the browser context to ensure session SQLite/IndexedDB locks are released.

---

## 🎨 Frontend Module Walkthrough

### 1. `frontend/index.html` — The Voice Orb Interface
* Styled using **Tailwind CSS** with a dark, minimalist theme (`#0a0d14`).
* Renders the central glowing Voice Orb with three layered elements:
  * An ambient blur halo (`#orb-halo`).
  * The interactive glowing sphere (`#voice-orb`).
  * The microphone SVG icon (`#mic-icon`).
* Houses the real-time transcript box and the auto-revealing **WhatsApp Action Card**.

### 2. `frontend/js/app.js` — Client Event Loop & State Machine
* **`initWebSocket()`:** Connects to `/ws/events` with auto-reconnect fallback (3s retry).
* **`setOrbState(state)`:** Switches CSS classes (`orb-idle`, `orb-listening`, `orb-speaking`, `orb-executing`) to animate the central sphere.
* **Spacebar Push-to-Talk:** Listens for `keydown` / `keyup` on `Space` to allow keyboard-driven walkie-talkie mode.

### 3. `frontend/js/audio.js` — Hardware Audio Capture
* Manages `navigator.mediaDevices.getUserMedia`.
* Specifically requests:
  ```javascript
  {
    audio: {
      echoCancellation: true,  // Hardware AEC
      noiseSuppression: true,  // Ambient filtering
      autoGainControl: true,   // Voice leveling
      channelCount: 1,         // Mono
      sampleRate: 16000        // Whisper optimal rate
    }
  }
  ```

---

## 📬 Data Contracts: WebSocket Event Schemas

All communication across the `/ws/events` WebSocket adheres to a standardized JSON schema:

#### 1. State Change Event (`STATE_CHANGE`)
Emitted by backend to drive the visual Orb state:
```json
{
  "type": "STATE_CHANGE",
  "state": "listening" // Options: "idle" | "listening" | "speaking" | "executing"
}
```

#### 2. Live Transcript Event (`TRANSCRIPT`)
Emitted as Whisper STT transcribes spoken chunks:
```json
{
  "type": "TRANSCRIPT",
  "text": "Ali ko WhatsApp pe bolo kal meeting 3 baje hai"
}
```

#### 3. WhatsApp Action Event (`WHATSAPP_ACTION`)
Emitted when the browser driver finishes sending a message:
```json
{
  "type": "WHATSAPP_ACTION",
  "contact": "Ali",
  "message": "kal meeting 3 baje hai",
  "status": "Sent" // Options: "Searching" | "Typing" | "Sent" | "Failed"
}
```
