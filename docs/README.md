# 📚 Pegham.ai Developer & Architecture Knowledge Hub

Welcome to the definitive architectural, engineering, and system design guide for **Pegham.ai (پیغام)**.

Whether you are onboarding as a contributor, reviewing the codebase for security and privacy, or using this project as a case study to learn modern **Voice AI Pipelines**, **WebRTC Audio Engineering**, and **Headless Browser Automation**, this documentation is built to be your comprehensive source of truth.

---

## 🧭 Core Architectural Philosophy

Modern consumer voice assistants (such as ChatGPT Voice, Siri, Google Gemini Live) are sandboxed inside mobile and cloud operating systems. By design:
* ❌ They cannot inspect, search, or trigger actions within your personal WhatsApp account.
* ❌ They cannot automate un-API'd desktop workflows without costly enterprise SaaS intermediaries.
* ❌ The official Meta WhatsApp Business Cloud API requires formal business verification, credit card billing per conversation, rigid template approvals, and prohibits personal WhatsApp account binding.

**Pegham.ai was architected to solve this problem entirely on the user's local machine:**

```text
                                  +---------------------------------------+
                                  |           User Spoken Audio           |
                                  +-------------------┬-------------------+
                                                      │ Spoken Voice
                                                      ▼
+─────────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                      Pegham.ai Local Machine Engine                                     |
|                                                                                                         |
|   1. Audio Ingestion    ──>  2. Real-Time VAD   ──>  3. Low-Latency STT ──>  4. Conversational LLM     |
|      (WebRTC + AEC)          (Silero VAD)            (Groq Whisper)          (Tool Dispatcher)          |
|                                                                                      │                  |
|                                                                                      ▼                  |
|   7. Audio Playback     <──  6. Speech Synthesis <── 5. Action Execution <───────────┘                  |
|      (Streamed to User)      (Azure ur-PK TTS)       (Playwright Local WhatsApp)                        |
+─────────────────────────────────────────────────────────────────────────────────────────────────────────+
```

### The 4 Core Architectural Pillars

1. **🔒 Zero-Cloud Privacy & Local Persistence**
   All authentication state (session cookies, IndexedDB crypto tokens, WhatsApp keys) lives strictly inside `./whatsapp_session` on your local SSD. No database, no third-party telemetry, no cloud relays.
2. **⚡ Sub-Second Voice Turnaround (Low Latency)**
   To feel conversational, response latency must stay below **800ms**. Pegham achieves this by utilizing **streaming audio frames**, ultra-fast Whisper inference via Groq, and parallel tool dispatching.
3. **🗣️ Native Urdish & Code-Switching Comprehension**
   Real human speech in South Asia is rarely purely standard English or formal Urdu. Pegham is explicitly prompt-engineered to understand Roman Urdu, Pakistani colloquial idioms (*"Bhai ko bolo"*, *"Eid Mubarak bol do"*), and phonetic transcriptions without hallucination.
4. **🌐 Zero-Dependency Playwright Automation**
   Rather than relying on fragile reverse-engineered WhatsApp Web wrappers that get banned, Pegham controls an authentic Chromium instance via Playwright with anti-detection flags enabled.

---

## 📖 Curriculum Roadmap & Reading Order

For any developer studying this repository, we recommend reading through the documentation in the following structured sequence:

| Chapter | Document | What You Will Learn |
| :---: | :--- | :--- |
| **01** | [**System Architecture & Data Flow**](01_system_architecture.md) | The complete end-to-end lifecycle of a voice command, sequence diagrams, latency budgeting, and component interactions. |
| **02** | [**Technology Stack Deep Dive**](02_technology_stack_deep_dive.md) | Technical rationale for every library and tool chosen (Pipecat, Playwright, Silero, Whisper, FastAPI, Loguru) vs. alternative approaches. |
| **03** | [**Codebase Walkthrough**](03_codebase_walkthrough.md) | File-by-file guided tour of the directory tree, explaining the purpose, functions, and data contracts of every module. |
| **04** | [**WhatsApp Automation Mechanics**](04_playwright_whatsapp_mechanics.md) | How Chromium persistent contexts (`user_data_dir`) work, DOM query strategies, QR code login preservation, and anti-bot mitigation. |
| **05** | [**Voice Agent & Prompt Engineering**](05_voice_agent_and_prompt_engineering.md) | Designing prompts for conversational voice vs. chat, Urdish bilingual understanding, structured JSON tool schemas, and output guardrails. |
| **06** | [**Frontend & Audio Engineering**](06_frontend_and_audio_engineering.md) | WebRTC audio constraints, Acoustic Echo Cancellation (AEC), hardware sampling (16kHz), push-to-talk, and reactive CSS Orb animation states. |

---

## 🔑 Key Engineering Glossary

* **AEC (Acoustic Echo Cancellation):** Browser/hardware algorithm that subtracts the speaker audio from the microphone input, preventing the AI voice from feeding back into itself.
* **VAD (Voice Activity Detection):** Machine learning model (e.g. Silero VAD) that analyzes raw audio chunks to detect human speech boundaries, speech onset, and thinking pauses.
* **STT (Speech-to-Text):** Converting raw audio frames into text transcripts (e.g. OpenAI Whisper Large-v3 running on Groq LPU hardware).
* **TTS (Text-to-Speech):** Synthesizing text into natural-sounding audio streams (e.g. Azure Neural Speech with `ur-PK` voice models).
* **Persistent Browser Context:** A Playwright Chromium session configured with an on-disk profile directory (`user_data_dir`), preserving cookies, local storage, and IndexedDB between process restarts.
* **Urdish:** Colloquial code-switching between Urdu and English common across Pakistan and the South Asian diaspora (e.g., *"Meeting cancel ho gayi hai"*).
* **Barge-In:** The capability of a real-time voice pipeline to immediately cancel TTS playback and tool execution when the user starts speaking over the bot.
