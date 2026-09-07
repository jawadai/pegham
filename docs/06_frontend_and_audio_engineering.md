# 06 — Frontend & Browser Audio Engineering

This document explains the hardware constraints, audio processing parameters, WebRTC configurations, and CSS animation architecture powering the **Pegham.ai Command Orb** frontend.

---

## 🎧 The Critical Role of Acoustic Echo Cancellation (AEC)

In any voice assistant that plays audio through computer speakers while simultaneously recording through a microphone, an acoustic feedback loop occurs:

```text
Without Echo Cancellation (Fatal Loop):
[Assistant Speaks: "Ali ko message bhej diya"] ──> [Laptop Speaker] ──> [Acoustic Wave in Room]
                                                                                │
[Pipecat VAD Triggers Interruption] <── [Assistant Hears Itself] <── [Laptop Microphone]
```

Without AEC, the assistant will continuously interrupt itself, transcribe its own voice, and enter an infinite hallucination loop.

### How Pegham Solves This in `frontend/js/audio.js`:
Pegham explicitly requests the browser's native DSP (Digital Signal Processing) stack:

```javascript
this.mediaStream = await navigator.mediaDevices.getUserMedia({
  audio: {
    echoCancellation: true,   // Activates OS/Hardware Acoustic Echo Cancellation
    noiseSuppression: true,   // Cancels continuous background hum (AC, fan noise)
    autoGainControl: true,    // Normalizes quiet whisper vs loud speech
    channelCount: 1,          // Mono audio (reduces bandwidth by 50%)
    sampleRate: 16000         // Matches Whisper & Silero VAD native sampling
  }
});
```

* **`echoCancellation: true`**: Instructs the browser to take the audio output reference from the `<audio>` or WebAudio context and perform mathematical subtraction from the microphone input signal before emitting frames.
* **`sampleRate: 16000`**: Both Whisper and Silero VAD downsample audio to 16,000 samples per second. Requesting 16kHz directly from the browser saves CPU cycles by preventing double-resampling on the Python server.

---

## 🎹 Keyboard Interaction: Push-to-Talk

While Pegham supports continuous VAD listening, users often prefer a walkie-talkie style push-to-talk mode in noisy environments.

In `frontend/js/app.js`:
```javascript
window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && !e.repeat && document.activeElement.tagName !== "INPUT") {
    e.preventDefault(); // Prevents page from scrolling down on spacebar
    setOrbState("listening");
  }
});

window.addEventListener("keyup", (e) => {
  if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
    e.preventDefault();
    setOrbState("idle");
  }
});
```

---

## 🔮 The Glowing Command Orb: CSS Keyframe Mechanics

Rather than relying on heavy WebGL, Three.js, or Canvas animation libraries (which consume high laptop battery and CPU power), the Command Orb is built entirely using **hardware-accelerated CSS3 transforms and blur filters**:

### State Classes in `frontend/css/style.css`:

#### 1. Idle Breathing State (`orb-idle`)
A soft, steady emerald glow communicating that the assistant is alive and waiting:
```css
.orb-idle {
  background: linear-gradient(135deg, #10b981, #0d9488);
}
```

#### 2. Active Listening Pulse (`orb-listening`)
Scales the orb up by 12% and expands an indigo box-shadow to indicate user speech detection:
```css
@keyframes orbListening {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 35px rgba(99, 102, 241, 0.6);
  }
  50% {
    transform: scale(1.12);
    box-shadow: 0 0 65px rgba(99, 102, 241, 0.9);
  }
}
.orb-listening {
  animation: orbListening 1.5s infinite ease-in-out;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
}
```

#### 3. Assistant Speaking State (`orb-speaking`)
Subtle rhythmic brightness modulation mimicking vocal cords and prosody:
```css
@keyframes orbSpeaking {
  0%, 100% { transform: scale(0.98); filter: brightness(1); }
  50%      { transform: scale(1.06); filter: brightness(1.25); }
}
.orb-speaking {
  animation: orbSpeaking 1.2s infinite ease-in-out;
  background: linear-gradient(135deg, #10b981, #3b82f6) !important;
}
```

#### 4. Tool Execution Spin (`orb-executing`)
Amber-red gradient with slow rotation while Playwright automation operates in the background:
```css
.orb-executing {
  animation: spinSlow 3s linear infinite;
  background: linear-gradient(135deg, #f59e0b, #ef4444) !important;
}
```
