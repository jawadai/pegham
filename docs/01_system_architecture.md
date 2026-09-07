# 01 — System Architecture & Data Flow

This document details the architectural topology, data pipelines, event loops, and latency budgets that allow **Pegham.ai** to deliver sub-second, voice-driven WhatsApp automation.

---

## 🏛️ System Topology Diagram

Pegham.ai operates on a client-server architecture hosted locally on the user's workstation. The diagram below illustrates the components and their boundaries:

```mermaid
graph TB
    subgraph Client ["Client Tier (Browser UI)"]
        MIC["Microphone Capture<br/>(16kHz, Mono, AEC enabled)"]
        ORB["Glowing Command Orb UI<br/>(State: Idle, Listening, Speaking)"]
        CARD["Action Card Component<br/>(Real-time WhatsApp Status)"]
        SPK["Speaker Playback<br/>(WebRTC / WebAudio Stream)"]
    end

    subgraph Backend ["Pegham Backend Server (FastAPI + Asyncio)"]
        WS_HUB["WebSocket Event Bus<br/>(/ws/events)"]
        STATIC["Static Asset Server<br/>(Mounts /static)"]
        HEALTH["Health API Endpoint<br/>(/api/health)"]

        subgraph Core ["Pipecat Real-Time Pipeline"]
            TRANSPORT_IN["WebRTC / Audio Transport In"]
            VAD["Silero VAD<br/>(Detects Speech Start/Stop)"]
            STT["Whisper Large-v3 (Groq)<br/>(Speech-to-Text Transcription)"]
            LLM["Conversational Brain (GPT-4o/Claude)<br/>(Intent Extraction & Tool Calling)"]
            TTS["Neural TTS (Azure ur-PK / ElevenLabs)<br/>(Text-to-Speech Audio Generation)"]
            TRANSPORT_OUT["WebRTC Audio Transport Out"]
        end

        subgraph Service ["Automation Services"]
            DISPATCH["Tool Dispatcher<br/>(backend/core/tools.py)"]
            PW_SRV["Playwright WhatsApp Service<br/>(backend/services/whatsapp.py)"]
        end
    end

    subgraph OS ["Operating System & Persistence"]
        SESSION_DIR["Local Session Directory<br/>(./whatsapp_session)"]
        CHROME["Headless Chromium Process<br/>(web.whatsapp.com)"]
    end

    %% Audio & Control Connections
    MIC -->|WebRTC Audio Frames| TRANSPORT_IN
    TRANSPORT_IN --> VAD
    VAD -->|Voice Frames| STT
    STT -->|User Transcript Text| LLM
    LLM -->|Function Call Payload| DISPATCH
    DISPATCH -->|Async Task| PW_SRV
    PW_SRV <-->|DevTools Protocol / CDP| CHROME
    CHROME <-->|Read / Write Cookies & IndexedDB| SESSION_DIR
    PW_SRV -->|Action Status Event| WS_HUB
    WS_HUB -->|JSON Events| CARD
    WS_HUB -->|Orb State Sync| ORB
    LLM -->|Spoken Response Text| TTS
    TTS -->|Synthesized Audio Stream| TRANSPORT_OUT
    TRANSPORT_OUT -->|WebRTC Audio Stream| SPK
```

---

## 🔄 End-to-End Voice-to-Action Lifecycle

When a user says: *"Hamza ko WhatsApp pe bolo main 10 min mein pohanch raha hoon"*, the system executes the following chronological sequence:

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Voice)
    participant UI as Browser (Command Orb)
    participant Pipe as Pipecat Audio Engine
    participant Groq as Groq (Whisper STT)
    participant LLM as Conversational LLM
    participant Tools as Tool Dispatcher
    participant WA as Playwright WhatsApp
    participant TTS as Azure Neural TTS

    User->>UI: Speaks voice command
    UI->>Pipe: WebRTC streaming audio chunks (16kHz PCM)
    Note over Pipe: Silero VAD detects speech onset.<br/>Orb transitions to LISTENING state.
    Pipe->>Groq: Stream audio frames for inference
    Groq-->>Pipe: Return text: "Hamza ko WhatsApp pe bolo main 10 min mein pohanch raha hoon"
    Pipe->>UI: Emit WS event: TRANSCRIPT
    UI-->>User: Render transcript text in real time

    Note over Pipe: Silero VAD detects end-of-speech silence (~400ms).
    Pipe->>LLM: Send conversation context + Urdish System Prompt + Tool Schema
    
    Note over LLM: LLM determines function call:<br/>send_whatsapp_message(contact="Hamza", message="main 10 min mein pohanch raha hoon")
    
    par Parallel Execution
        LLM->>Tools: Dispatch send_whatsapp_message
        Tools->>WA: Locate contact 'Hamza' & submit message
        WA-->>UI: Emit WS event: WHATSAPP_ACTION (Status: Sent)
        UI-->>User: Action Card slides open with recipient & text
    and
        LLM->>TTS: Stream response text: "Hamza ko message bhej diya hai!"
        TTS-->>Pipe: Stream synthesized PCM audio frames
        Pipe->>UI: Stream WebRTC audio response
        UI->>User: Spoken confirmation through speakers
    end
```

---

## ⏱️ The 800ms Latency Budget

In voice user interfaces (VUI), human conversational psychology dictates that **any response taking longer than 1,000ms creates an awkward, robotic pause**.

Pegham targets an **end-to-end turnaround latency under 800ms**. Here is how the latency budget is partitioned:

| Processing Stage | Target Latency | Optimization Technique |
| :--- | :---: | :--- |
| **1. Audio Ingestion & Transport** | $\approx 20\text{ms}$ | Browser WebRTC Opus stream over local `localhost` network. |
| **2. Voice Activity Detection (VAD)** | $\approx 350\text{ms}$ | Silero VAD chunking. Requires ~350–400ms of consecutive silence to confirm user finished speaking without cutting off thought pauses. |
| **3. Speech-to-Text (STT)** | $\approx 150\text{ms}$ | Whisper Large-v3 running on Groq LPUs (capable of 300+ words per second transcription). |
| **4. LLM Time to First Token (TTFT)** | $\approx 200\text{ms}$ | Streaming completion using low-latency reasoning models with zero pre-prompt fluff. |
| **5. Text-to-Speech First Chunk** | $\approx 100\text{ms}$ | Azure Neural TTS streaming endpoint emitting chunked audio frames as tokens arrive. |
| **Total Turnaround to Voice Output** | **$\approx 820\text{ms}$** | **Sub-second, human-like voice response.** |

> [!NOTE]
> The WhatsApp Playwright automation executes **concurrently** with the audio response synthesis. The user hears the spoken confirmation *"Hamza ko message bhej diya hai"* at the exact instant the browser DOM action finishes submitting the message.

---

## 🚦 Frontend State Synchronization Machine

The Command Orb in `frontend/js/app.js` is driven by a finite state machine synchronized over WebSockets:

```mermaid
stateDiagram-v2
    [*] --> Idle: Page Load & WS Connected
    Idle --> Listening: Mic Input Active / Spacebar Down
    Listening --> Executing: VAD Silence Confirmed / Tool Dispatched
    Executing --> Speaking: TTS Stream Arriving
    Speaking --> Idle: TTS Stream Finished
    Listening --> Idle: User Interruption / Silence Timeout
```

1. **`orb-idle` (Emerald Green):** System is ready and waiting for microphone activation.
2. **`orb-listening` (Electric Indigo Pulse):** Silero VAD detects active speech; pulse expands with user's voice cadence.
3. **`orb-executing` (Amber Glow):** WhatsApp automation is clicking contacts and typing text in Chromium.
4. **`orb-speaking` (Teal-Blue Wave):** The assistant is actively speaking confirmation back to the user.
