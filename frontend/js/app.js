/**
 * Main Frontend Application Script for Pegham.ai
 * Handles WebSocket events, Orb animation states, and UI updates.
 */

document.addEventListener("DOMContentLoaded", () => {
  const voiceOrb = document.getElementById("voice-orb");
  const orbStatus = document.getElementById("orb-status");
  const transcriptText = document.getElementById("transcript-text");
  const actionCard = document.getElementById("action-card");
  const actionContact = document.getElementById("action-contact");
  const actionMessage = document.getElementById("action-message");
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");

  let ws = null;
  let isListening = false;

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
      if (data.whatsapp_ready) {
        statusDot.className = "w-2 h-2 rounded-full bg-emerald-400";
        statusText.textContent = "WhatsApp Ready";
      } else {
        statusDot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
        statusText.textContent = "WhatsApp Idle";
      }
    } catch (e) {
      statusDot.className = "w-2 h-2 rounded-full bg-red-400";
      statusText.textContent = "Server Offline";
    }
  }

  // Stream & play synthesized Urdu voice audio (Free Edge-TTS)
  function playSpokenAudio(text) {
    if (!text) return;
    setOrbState("speaking");
    const audioUrl = `/api/tts?text=${encodeURIComponent(text)}`;
    const audio = new Audio(audioUrl);
    audio.onended = () => {
      setOrbState("idle");
    };
    audio.onerror = (e) => {
      console.warn("Audio playback interrupted or failed:", e);
      setOrbState("idle");
    };
    audio.play().catch(err => {
      console.warn("Audio autoplay blocked by browser:", err);
      setOrbState("idle");
    });
  }

  // Handle events emitted from backend
  function handleServerEvent(event) {
    if (event.type === "STATE_CHANGE") {
      setOrbState(event.state); // 'idle', 'listening', 'speaking', 'executing'
    } else if (event.type === "TRANSCRIPT") {
      transcriptText.textContent = `"${event.text}"`;
    } else if (event.type === "WHATSAPP_ACTION") {
      showActionCard(event.contact, event.message, event.status);
      if (event.status === "Sent") {
        playSpokenAudio(event.spoken_response || `${event.contact} ko message bhej diya hai!`);
      }
    } else if (event.type === "SPEAK") {
      playSpokenAudio(event.text);
    }
  }

  // Visual Orb States
  function setOrbState(state) {
    voiceOrb.className = "relative w-32 h-32 rounded-full cursor-pointer flex items-center justify-center transition-all duration-500 shadow-2xl border ";
    if (state === "listening") {
      voiceOrb.classList.add("orb-listening");
      orbStatus.textContent = "Listening...";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-indigo-400";
    } else if (state === "speaking") {
      voiceOrb.classList.add("orb-speaking");
      orbStatus.textContent = "Pegham is speaking...";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-emerald-400";
    } else if (state === "executing") {
      voiceOrb.classList.add("orb-executing");
      orbStatus.textContent = "Sending WhatsApp message...";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-amber-400";
    } else {
      voiceOrb.classList.add("orb-idle");
      orbStatus.textContent = "Tap or Hold Spacebar to Talk";
      orbStatus.className = "text-sm font-medium tracking-wide uppercase text-slate-400";
    }
  }

  function showActionCard(contact, message, status) {
    actionContact.textContent = contact;
    actionMessage.textContent = `"${message}"`;
    actionCard.classList.remove("hidden");
  }

  // Toggle audio stream on Orb click
  voiceOrb.addEventListener("click", async () => {
    if (!window.audioController.isConnected) {
      try {
        await window.audioController.requestMicrophone();
        setOrbState("listening");
      } catch (err) {
        alert("Please allow microphone permissions to use Pegham.ai.");
      }
    } else {
      setOrbState("idle");
    }
  });

  // Spacebar Push-to-Talk Handler
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && !e.repeat && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      setOrbState("listening");
    }
  });

  window.addEventListener("keyup", (e) => {
    if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      setOrbState("idle");
    }
  });

  // Initialize
  initWebSocket();
  setInterval(checkHealth, 10000);
});
