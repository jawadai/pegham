/**
 * Audio Capture & MediaRecorder handler for Pegham.ai
 * Records speech using hardware Echo Cancellation and sends WebM Opus audio to backend.
 */

class AudioController {
  constructor() {
    this.mediaStream = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isConnected = false;
    this.isRecording = false;
  }

  async requestMicrophone() {
    if (this.mediaStream && this.isConnected) {
      return this.mediaStream;
    }

    try {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
          }
        });
      } catch (constraintErr) {
        console.warn("Retrying microphone with basic constraints:", constraintErr);
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      this.isConnected = true;
      console.log("🎙️ Microphone access granted successfully.");
      return this.mediaStream;
    } catch (err) {
      console.error("Failed to acquire microphone access:", err);
      this.isConnected = false;
      throw err;
    }
  }

  async startRecording() {
    if (this.isRecording) return;

    await this.requestMicrophone();
    this.audioChunks = [];

    // Select supported audio mimeType
    const mimeTypes = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4"
    ];
    let selectedMimeType = "";
    for (const mt of mimeTypes) {
      if (MediaRecorder.isTypeSupported(mt)) {
        selectedMimeType = mt;
        break;
      }
    }

    const options = selectedMimeType ? { mimeType: selectedMimeType } : {};
    this.mediaRecorder = new MediaRecorder(this.mediaStream, options);

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };

    this.mediaRecorder.start(100);
    this.isRecording = true;
    console.log("🔴 Voice recording started...");
  }

  stopRecording() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || !this.isRecording) {
        resolve(null);
        return;
      }

      this.mediaRecorder.onstop = () => {
        this.isRecording = false;
        const blobType = this.mediaRecorder.mimeType || "audio/webm";
        const audioBlob = new Blob(this.audioChunks, { type: blobType });
        console.log(`⏹️ Recording stopped. Generated ${audioBlob.size} bytes (${blobType}).`);
        resolve(audioBlob);
      };

      this.mediaRecorder.onerror = (err) => {
        this.isRecording = false;
        reject(err);
      };

      this.mediaRecorder.stop();
    });
  }

  async processVoice(audioBlob) {
    if (!audioBlob || audioBlob.size < 1000) {
      console.warn("Audio recording was too short or empty.");
      return null;
    }

    const res = await fetch("/api/voice/process", {
      method: "POST",
      body: audioBlob,
      headers: {
        "Content-Type": audioBlob.type || "audio/webm"
      }
    });

    if (!res.ok) {
      throw new Error(`Voice server error: ${res.statusText}`);
    }

    return await res.json();
  }

  stop() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    this.isConnected = false;
    this.isRecording = false;
  }
}

window.audioController = new AudioController();
