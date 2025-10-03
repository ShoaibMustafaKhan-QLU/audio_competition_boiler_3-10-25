let mediaRecorder;
let audioChunks = [];

document.getElementById("recordBtn").onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state === "inactive") {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    source.connect(analyser);
    analyser.fftSize = 512;

    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    audioChunks = [];

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      const formData = new FormData();
      formData.append("audio", audioBlob, "input.webm");

      const res = await fetch("/chat", { method: "POST", body: formData });
      const data = await res.json();

      document.getElementById("userText").innerText = "You: " + (data.user_text || "❌ error");
      document.getElementById("botText").innerText = "AI: " + (data.reply_text || "❌ error");

      if (data.audio_urls && data.audio_urls.length > 0) {
        const botAudio = document.getElementById("botAudio");
        let i = 0;
        const playNext = () => {
          if (i < data.audio_urls.length) {
            botAudio.src = data.audio_urls[i];
            botAudio.play();
            i++;
            botAudio.onended = playNext;
          }
        };
        playNext();
      }
    };

    mediaRecorder.start();

    // Silence detection
    const data = new Uint8Array(analyser.frequencyBinCount);
    let silenceStart = performance.now();
    let triggered = false;

    function checkSilence() {
      analyser.getByteFrequencyData(data);
      const volume = data.reduce((a, b) => a + b) / data.length;
      if (volume < 5) { // silence threshold
        if (!triggered && performance.now() - silenceStart > 1000) {
          triggered = true;
          mediaRecorder.stop();
          console.log("🎤 Auto-stopped on silence");
        }
      } else {
        silenceStart = performance.now();
      }
      if (!triggered) requestAnimationFrame(checkSilence);
    }

    checkSilence();
  }
};
