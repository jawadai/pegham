# 05 — Voice Agent Design & Prompt Engineering

Prompt engineering for real-time voice assistants requires an entirely different mental model than engineering prompts for text chatbots. This document covers the linguistic, structural, and behavioral principles embedded in **Pegham.ai**.

---

## 🎙️ Voice vs. Text: Why Chatbot Prompts Fail in Voice

When building chat interfaces, longer responses containing bullet points, bold headers, and markdown tables are considered helpful.

In a **Voice User Interface (VUI)**, however:
* ❌ Reading bulleted lists aloud sounds robotic and confusing.
* ❌ Markdown formatting symbols (e.g. `**bold**`, `*italics*`, `---`) degrade speech synthesis phonetics.
* ❌ Long paragraphs force the user to wait in silence while the TTS engine drones on without interruption.

### The 3 Rules of Voice Prompt Engineering

```text
+--------------------------------------------------------------------------------+
|                        The Pegham Voice Prompt Rules                           |
|                                                                                |
|  1. The 2-Sentence Rule: Never speak more than 1 or 2 sentences per turn.      |
|  2. Pure Phonetic Output: Strip markdown symbols that confuse TTS models.      |
|  3. Action First, Confirm Second: Call tools immediately, then confirm aloud.  |
+--------------------------------------------------------------------------------+
```

---

## 🇵🇰 The Urdish Linguistic Challenge (Code-Switching)

In Pakistan and the South Asian diaspora, human communication is rarely monolithic. A single spoken sentence typically weaves English nouns and verbs with Urdu grammatical structure:

> *"Bhai ko bolo meeting reschedule ho gayi hai, sham ko contact karein."*

### Why Off-The-Shelf Models Struggle
1. **Phonetic Ambiguity:** A Whisper transcript might write *"bolo"* as *"bolo"*, *"bowlo"*, or *"bolo"*.
2. **Intent Parsing:** Identifying the **recipient** (*"Bhai"*) versus the **actual message payload** (*"meeting reschedule ho gayi hai, sham ko contact karein"*) requires understanding colloquial discourse markers like *"ko bolo"* (tell X).

### How Pegham Solves This
In `backend/core/prompts.py`, the system prompt establishes:
```python
PEGHAM_SYSTEM_PROMPT = """You are Pegham (پیغام), an ultra-fast, witty, and dependable voice-first WhatsApp assistant.

Your purpose is to help the user manage their WhatsApp messages completely hands-free.

Personality & Language:
- You speak natural, conversational Urdish (پاکستانی بول چال کی اردو / Urdish) mixed with English, exactly as people naturally speak in Pakistan.
- Keep your verbal responses SHORT and CRISP (1-2 sentences maximum). Since you are speaking out loud over voice, never give long paragraphs.
- Be respectful yet energetic, like an agile personal courier ("قاصد / نامہ بر").
- When confirming actions, be direct:
  - e.g., "Ali ko message bhej diya hai!" or "Bilal se 2 naye messages aaye hain, sunna chahte hain?"
"""
```

---

## 🛠️ Tool Calling & Intent Disambiguation

Pegham leverages **Structured Function Calling** (JSON Schema) to guarantee that the LLM extracts arguments deterministically:

```json
{
  "type": "function",
  "function": {
    "name": "send_whatsapp_message",
    "description": "Sends a WhatsApp text message to a specific contact or group name.",
    "parameters": {
      "type": "object",
      "properties": {
        "contact_name": {
          "type": "string",
          "description": "The exact or partial name of the contact or group as saved in WhatsApp (e.g. 'Ali', 'Hamza Khan', 'Office Group')."
        },
        "message": {
          "type": "string",
          "description": "The text content of the message to send."
        }
      },
      "required": ["contact_name", "message"]
    }
  }
}
```

### Disambiguation Heuristics
When a user command lacks a clear recipient or message:
* **Example User:** *"WhatsApp pe message bhej do"* (Send a message on WhatsApp)
* **Bad Behavior:** Hallucinating a recipient or asking a multi-step interview questionnaire.
* **Pegham Behavior:** Asks a single, direct, spoken question: *"Kisko message bhejna hai aur kya message hai?"* (Who should I send it to and what is the message?)
