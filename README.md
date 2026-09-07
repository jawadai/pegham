<div align="center">
  <img src="frontend/assets/logo.svg" width="96" height="96" alt="Pegham.ai Logo" />
  <h1>Pegham.ai (پیغام)</h1>
  <p><em>نیا زمانہ، نیا پیغام — The Voice-First WhatsApp Operating Copilot</em></p>

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework: Pipecat](https://img.shields.io/badge/pipeline-Pipecat%20AI-purple.svg)](https://github.com/pipecat-ai/pipecat)
[![Automation: Playwright](https://img.shields.io/badge/automation-Playwright-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
</div>

**Pegham.ai** is an open-source, real-time voice copilot that lets you control your personal WhatsApp completely hands-free using natural spoken **Urdish** (conversational Urdu + English) or pure English.

Speak into your microphone—**Pegham** transcribes your voice, extracts your intended recipient and message, operates WhatsApp Web in the background using Playwright, and confirms the action aloud in real time.

---

## 🌟 Why Pegham? (Why ChatGPT Can't Do This)

Consumer voice assistants like ChatGPT Voice and Gemini Live are walled inside mobile sandboxes:
* ❌ They **cannot** access your personal WhatsApp account.
* ❌ They **cannot** read incoming WhatsApp messages.
* ❌ They **cannot** trigger real-world actions on your local desktop.
* ❌ Setting up the official Meta WhatsApp Cloud API requires business verification, credit cards, and rigid template approvals.

**Pegham.ai solves this directly on your machine:**
* ✅ **Zero Meta Cloud API Required:** Uses Playwright with a persistent browser session. You scan the WhatsApp Web QR code **once**, and it stays authenticated forever.
* ✅ **Native Urdish Understanding:** Built to understand colloquial Pakistani speech patterns (e.g., *"Bhai ko bolo main 10 min mein pohanch raha hoon"*).
* ✅ **Real-Time Voice Streaming:** Powered by **Pipecat**, delivering sub-second voice feedback, barge-in (interruption handling), and Acoustic Echo Cancellation (AEC).
* ✅ **Complete Privacy:** Your session credentials, contacts, and messages remain strictly local in your machine's `./whatsapp_session` directory.

---

## 🏗️ Architecture & Data Flow

```text
                               +--------------------------------------------+
                               |                 Web Client                 |
                               |  • Animated Glowing Voice Orb (Jarvis UI)  |
                               |  • Acoustic Echo Cancellation (AEC)        |
                               |  • Live Real-Time Action Cards             |
                               +---------------------▲----------------------+
                                                     │
                                        WebRTC Audio + WebSocket Events
                                                     │
+────────────────────────────────────────────────────▼────────────────────────────────────────────────────+
|                                         Pegham.ai Backend (FastAPI)                                      |
|                                                                                                         |
|   +-------------------------------------------------------------------------------------------------+   |
|   | 1. WebRTC Audio Transport & Silero VAD (Detects user speech & thinking pauses)                   |   |
|   +------------------------------------------------┬------------------------------------------------+   |
|                                                    │ Spoken Audio Frames                                |
|   +------------------------------------------------▼------------------------------------------------+   |
|   | 2. STT: Groq Whisper-Large-v3 / Azure Speech (High-accuracy Urdish transcription)                |   |
|   +------------------------------------------------┬------------------------------------------------+   |
|                                                    │ User Transcript                                    |
|   +------------------------------------------------▼------------------------------------------------+   |
|   | 3. Conversational Brain & Tool Dispatcher (LLM: GPT-4o / Claude 3.5)                            |   |
|   |    Detects intent -> Dispatches: send_whatsapp_message(contact="Hamza", message="...")           |   |
|   +------------------------------------------------┬------------------------------------------------+   |
|                                                    │                                                    |
|                   ┌────────────────────────────────┴────────────────────────────────┐                   |
|                   │ Tool Execution                                                  │ Text Stream       |
|   +---------------▼-------------------------------+ +-------------------------------▼---------------+   |
|   | 4. Playwright WhatsApp Web Controller         | | 5. TTS: Azure Neural (ur-PK) / ElevenLabs     |   |
|   |    • Locates contact in persistent session    | |    Generates spoken confirmation:             |   |
|   |    • Types message & submits in background    | |    "Hamza ko message bhej diya hai!"          |   |
|   |    • Emits UI event via WebSocket             | |                                               |   |
|   +-----------------------------------------------+ +-------------------------------┬---------------+   |
|                                                                                     │ Audio Response    |
|   +---------------------------------------------------------------------------------▼---------------+   |
|   | 6. Audio Transport Out ──> Streamed back to User via WebRTC                                     |   |
|   +-------------------------------------------------------------------------------------------------+   |
+─────────────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 📁 Project Directory Layout

```text
Pegham/ (Pegham.ai)
├── README.md                 # Project documentation and guide
├── .gitignore                # Protects secrets, browser sessions, and virtualenvs
├── .env.example              # Template for API keys and configuration
├── pyproject.toml            # Python packaging and dependency metadata
├── requirements.txt          # Production dependencies
│
├── backend/                  # Python Backend & Voice Core
│   ├── __init__.py
│   ├── main.py               # FastAPI application, WebSocket hub, and static server
│   ├── config.py             # Pydantic Settings & environment manager
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pipecat_pipeline.py # Pipecat real-time audio pipeline builder
│   │   ├── prompts.py        # Urdish system prompt & conversational personality
│   │   └── tools.py          # LLM function calling schemas & dispatchers
│   ├── services/
│   │   ├── __init__.py
│   │   └── whatsapp.py       # Playwright WhatsApp Web automation service
│   └── utils/
│       ├── __init__.py
│       └── logger.py         # Loguru structured logging
│
├── frontend/                 # Web Interface (The "Command Orb")
│   ├── index.html            # Minimalist Jarvis widget (Tailwind CSS)
│   ├── css/
│   │   └── style.css         # Keyframe animations (orb pulsing, soundwave ripples)
│   └── js/
│       ├── app.js            # UI state, WebSocket client, keyboard shortcuts
│       └── audio.js          # WebRTC audio capture with Echo Cancellation
│
└── scripts/                  # Helper CLI Scripts
    ├── setup_whatsapp.py     # One-time QR code login runner
    └── test_whatsapp.py      # Standalone message sending verification script
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* **OS:** Linux (Ubuntu/Debian recommended), macOS, or Windows WSL2.
* **Python:** 3.11 or newer.
* **Microphone:** Built-in mic or headset.

### 2. Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Pegham.git
   cd Pegham
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install Playwright Chromium browser binaries:**
   ```bash
   playwright install chromium
   ```

---

### 3. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and provide your API keys:
```ini
# Required: At least one LLM key
OPENAI_API_KEY=sk-...

# Recommended: For sub-second Whisper STT
GROQ_API_KEY=gsk_...

# Recommended: For high quality Urdu TTS
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastus
```

---

### 4. One-Time WhatsApp QR Scan

Run the setup script to link your WhatsApp Web session:
```bash
python scripts/setup_whatsapp.py
```
* A browser window will open displaying the WhatsApp Web QR code.
* Open WhatsApp on your phone $\rightarrow$ **Linked Devices** $\rightarrow$ **Link a Device** $\rightarrow$ Scan the QR code.
* Once loaded, the script will automatically save your session in `./whatsapp_session` and close.
* **You will never need to scan the QR code again!**

---

### 5. Run the Application

Start the Pegham.ai server:
```bash
python backend/main.py
```

Open your browser at:
👉 **`http://localhost:8000`**

*(Pro-Tip for Linux/Mac: You can launch it as a borderless desktop widget using Chrome app mode:)*
```bash
google-chrome --app=http://localhost:8000 --window-size=450,650
```

---

## 🎙️ Example Voice Commands

Speak naturally in Urdish or English:

| Intent | What You Say | Action Taken |
| :--- | :--- | :--- |
| **Send Message** | *"Ali ko WhatsApp pe bolo kal meeting 3 baje hai"* | Searches 'Ali', types message, hits enter, confirms aloud. |
| **Send Quick Update** | *"Message Hamza: 'I am running 10 mins late'"* | Dispatches message to Hamza. |
| **Check Messages** | *"Koi naya message aaya hai WhatsApp pe?"* | Scans unread badges and speaks summary. |
| **Bilingual Casual** | *"Aunty ko message bhej do: 'Eid Mubarak!'"* | Sends greetings to contact 'Aunty'. |

---

## 🔒 Privacy & Security

* **No Cloud WhatsApp Access:** Unlike third-party SaaS bots, your WhatsApp session cookies never leave your computer.
* **No Database Logging:** Messages are processed in memory and sent directly through your local Chromium instance.
* **Git Safe:** `.gitignore` is strictly configured to prevent accidental commits of `./whatsapp_session` or `.env`.

---

## 🗺️ Roadmap

- [x] **Milestone 1:** Project architecture, environment scaffolding, and frontend Command Orb widget.
- [ ] **Milestone 2:** Playwright WhatsApp Web driver (DOM selectors, search, and send automation).
- [ ] **Milestone 3:** Full Pipecat real-time audio pipeline integration (WebRTC + Silero VAD + Groq Whisper + Azure TTS).
- [ ] **Milestone 4:** End-to-end testing with hands-free interruptible voice commands.
- [ ] **Milestone 5:** Global system hotkey (e.g. `Super + Space`) for desktop overlay summoning.

---

## 📜 License
Distributed under the MIT License. Built with ❤️ for hands-free productivity.
