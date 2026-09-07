/**
 * Audio Capture and WebRTC Stream handler for Kabootar.ai
 * Ensures hardware/browser Echo Cancellation is active.
 */

class AudioController {
  constructor() {
    this.mediaStream = null;
    this.audioContext = null;
    this.isConnected = false;
  }

  async requestMicrophone() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });
      this.isConnected = true;
      console.log("🎙️ Microphone access granted with Acoustic Echo Cancellation.");
      return this.mediaStream;
    } catch (err) {
      console.error("Failed to acquire microphone access:", err);
      throw err;
    }
  }

  stop() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    this.isConnected = false;
  }
}

window.audioController = new AudioController();
