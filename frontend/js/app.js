/**
 * Main Frontend Application Script for Pegham.ai
 * Handles WebSocket events, Orb animation states, Voice Recording, and WhatsApp Actions.
 */

document.addEventListener("DOMContentLoaded", () => {
  const voiceOrb = document.getElementById("voice-orb");
  const orbStatus = document.getElementById("orb-status");
  const transcriptText = document.getElementById("transcript-text");
  const actionCard = document.getElementById("action-card");
  const actionContact = document.getElementById("action-contact");
  const actionMessage = document.getElementById("action-message");
  const actionStatus = document.getElementById("action-status");
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  const textInput = document.getElementById("text-input");
  const textSendBtn = document.getElementById("text-send-btn");

  let ws = null;
  let isRecordingActive = false;

  // Initialize WebSocket for real-time events
  function initWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/events`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to Pegham Event Bus.");
      checkHealth();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
      } catch (e) {
        console.error("Failed to parse event:", e);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected. Retrying in 3s...");
      setTimeout(initWebSocket, 3000);
    };
  }

  // Poll backend health status
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      updateStatusBadge(data.whatsapp_ready);
    } catch (e) {
      statusDot.className = "w-2 h-2 rounded-full bg-red-500";
      statusText.textContent = "Server Offline";
    }
  }

  function updateStatusBadge(isReady) {
    if (isReady) {
      statusDot.className = "w-2 h-2 rounded-full bg-emerald-400";
      statusText.textContent = "WhatsApp Ready";
    } else {
      statusDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
      statusText.textContent = "Connecting WhatsApp...";
    }
  }

  let currentAudio = null;
  let lastSpokenText = "";
  let lastSpokenTime = 0;

  // Stream & play synthesized Urdu voice audio (Free Edge-TTS)
  function playSpokenAudio(text) {
    if (!text) return;
    const now = Date.now();
    // Prevent duplicate triggers for the same phrase within 3.5s
    if (text === lastSpokenText && (now - lastSpokenTime) < 3500) {
      return;
    }
    lastSpokenText = text;
    lastSpokenTime = now;

    if (currentAudio) {
      try {
        currentAudio.pause();
      } catch (e) {}
      currentAudio = null;
    }

    setOrbState("speaking");
    const audioUrl = `/api/tts?text=${encodeURIComponent(text)}`;
    currentAudio = new Audio(audioUrl);
    currentAudio.onended = () => {
      currentAudio = null;
      setOrbState("idle");
    };
    currentAudio.onerror = (e) => {
      console.warn("Audio playback interrupted or failed:", e);
      currentAudio = null;
      setOrbState("idle");
    };
    currentAudio.play().catch(err => {
      console.warn("Audio autoplay blocked by browser:", err);
      setOrbState("idle");
    });
  }

  // Handle events emitted from backend
  function handleServerEvent(event) {
    if (event.type === "STATUS") {
      updateStatusBadge(event.whatsapp_ready);
    } else if (event.type === "STATE_CHANGE") {
      setOrbState(event.state); // 'idle', 'listening', 'speaking', 'executing'
    } else if (event.type === "TRANSCRIPT") {
      transcriptText.textContent = `"${event.text}"`;
    } else if (event.type === "WHATSAPP_ACTION") {
      showActionCard(event.contact, event.message, event.status);
    } else if (event.type === "SPEAK") {
      playSpokenAudio(event.text);
    }
  }

  // Visual Orb States
  function setOrbState(state) {
    voiceOrb.className = "relative w-32 h-32 rounded-full cursor-pointer flex items-center justify-center transition-all duration-500 shadow-2xl border ";
    if (state === "listening") {
      voiceOrb.classList.add("orb-listening");
      orbStatus.textContent = "Listening... (Tap Orb again to finish)";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-indigo-400 animate-pulse";
    } else if (state === "speaking") {
      voiceOrb.classList.add("orb-speaking");
      orbStatus.textContent = "Pegham is speaking...";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-emerald-400";
    } else if (state === "executing") {
      voiceOrb.classList.add("orb-executing");
      orbStatus.textContent = "Processing & executing...";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-amber-400 animate-pulse";
    } else {
      voiceOrb.classList.add("orb-idle");
      orbStatus.textContent = "Tap or Hold Spacebar to Talk";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-slate-400";
    }
  }

  function showActionCard(contact, message, status) {
    actionContact.textContent = contact || "Contact";
    actionMessage.textContent = `"${message || ""}"`;
    if (status === "Sent") {
      actionStatus.className = "text-[11px] font-medium bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full";
      actionStatus.textContent = "Sent";
    } else {
      actionStatus.className = "text-[11px] font-medium bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full";
      actionStatus.textContent = status || "Failed";
    }
    actionCard.classList.remove("hidden");
  }

  // Start Voice Recording
  async function startRecording() {
    try {
      setOrbState("listening");
      await window.audioController.startRecording();
      isRecordingActive = true;
      console.log("Recording is active.");
    } catch (err) {
      console.error("Microphone error:", err);
      transcriptText.textContent = "Microphone error: " + (err.message || err.name || "Access denied");
      setOrbState("idle");
      isRecordingActive = false;
    }
  }

  // Stop Voice Recording and Process via Backend
  async function stopAndProcessRecording() {
    if (!isRecordingActive) return;
    isRecordingActive = false;
    setOrbState("executing");
    transcriptText.textContent = "Transcribing voice with Groq Whisper...";

    try {
      const audioBlob = await window.audioController.stopRecording();
      if (!audioBlob || audioBlob.size < 50) {
        console.warn("Audio recording empty or too small:", audioBlob ? audioBlob.size : 0);
        transcriptText.textContent = "Audio too brief. Please tap or hold spacebar, speak, then tap again.";
        setOrbState("idle");
        return;
      }

      transcriptText.textContent = "Thinking with LLaMA 3.3 70B & executing WhatsApp...";
      const result = await window.audioController.processVoice(audioBlob);

      if (result) {
        if (result.transcript) {
          transcriptText.textContent = `"${result.transcript}"`;
        }
        if (result.action && result.action.tool === "send_whatsapp_message") {
          const args = result.action.arguments || {};
          const res = result.action.result || {};
          showActionCard(args.contact_name, args.message, res.success ? "Sent" : "Failed");
        }
        if (result.spoken_response) {
          playSpokenAudio(result.spoken_response);
        } else {
          setOrbState("idle");
        }
      } else {
        setOrbState("idle");
      }
    } catch (err) {
      console.error("Error processing voice:", err);
      transcriptText.textContent = "Error processing voice: " + (err.message || "Server error");
      setOrbState("idle");
    }
  }

  // Toggle audio stream on Orb click
  voiceOrb.addEventListener("click", async () => {
    if (!isRecordingActive) {
      await startRecording();
    } else {
      await stopAndProcessRecording();
    }
  });

  // Spacebar Push-to-Talk Handler
  window.addEventListener("keydown", async (e) => {
    if (e.code === "Space" && !e.repeat && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      if (!isRecordingActive) {
        await startRecording();
      }
    }
  });

  window.addEventListener("keyup", async (e) => {
    if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      if (isRecordingActive) {
        await stopAndProcessRecording();
      }
    }
  });

  // Direct Text Command Handler
  async function sendTextCommand() {
    if (!textInput) return;
    const text = textInput.value.trim();
    if (!text) return;

    textInput.value = "";
    setOrbState("executing");
    transcriptText.textContent = `"${text}"`;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.action && data.action.tool === "send_whatsapp_message") {
        const args = data.action.arguments || {};
        const resObj = data.action.result || {};
        showActionCard(args.contact_name, args.message, resObj.success ? "Sent" : "Failed");
      }
      if (data.spoken_response) {
        playSpokenAudio(data.spoken_response);
      } else {
        setOrbState("idle");
      }
    } catch (err) {
      console.error("Error sending text command:", err);
      setOrbState("idle");
    }
  }

  if (textSendBtn) {
    textSendBtn.addEventListener("click", sendTextCommand);
  }
  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendTextCommand();
      }
    });
  }

  // Initialize
  initWebSocket();
  checkHealth();
  setInterval(checkHealth, 5000);
});
