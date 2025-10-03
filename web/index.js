let mediaRecorder;
let audioChunks = [];
let bubble = document.getElementById("bubble");
let statusEl = document.getElementById("status");
const chatBox = document.getElementById("chat");

// meter bar
let meterBar = document.createElement("div");
meterBar.style.position = "absolute";
meterBar.style.bottom = "5px";
meterBar.style.left = "5px";
meterBar.style.height = "6px";
meterBar.style.width = "0%";
meterBar.style.background = "limegreen";
meterBar.style.borderRadius = "3px";
bubble.appendChild(meterBar);

// chat helper
function addMessage(text, role) {
  const msg = document.createElement("div");
  msg.classList.add("message", role);
  msg.textContent = text;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// -------------------
// Tunable VAD settings
// -------------------
const silenceThreshold = 5;
const minSilenceDuration = 2000;
const minSpeechDuration = 1000;
let silenceTimeout;
let recordingStartTime;

// -------------------
// Start listening (with noise suppression)
// -------------------
async function startListening() {
  console.log("🎙️ Starting mic with noise suppression...");

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      noiseSuppression: true,
      echoCancellation: true,
      autoGainControl: true
    }
  });

  const ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  const analyser = ctx.createAnalyser();
  src.connect(analyser);

  analyser.fftSize = 512;
  const data = new Uint8Array(analyser.fftSize);

  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.onstart = () => {
    audioChunks = [];
    recordingStartTime = Date.now();
    bubble.classList.add("talking");
    statusEl.textContent = "Listening...";
    watchSilence(analyser, data);
    drawVisuals(analyser, data);
    setTimeout(forceStop, 15000);
  };

  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

  mediaRecorder.onstop = async () => {
    bubble.classList.remove("talking");
    statusEl.textContent = "Processing...";

    const blob = new Blob(audioChunks, { type: "audio/webm" });
    await sendToBackend(blob);
  };

  mediaRecorder.start();
}

// -------------------
// Silence detection (RMS-based + meter bar)
// -------------------
function watchSilence(analyser, data) {
  function loop() {
    if (!mediaRecorder || mediaRecorder.state !== "recording") return;

    analyser.getByteTimeDomainData(data);

    let sumSquares = 0;
    for (let i = 0; i < data.length; i++) {
      let val = data[i] - 128;
      sumSquares += val * val;
    }
    const rms = Math.sqrt(sumSquares / data.length);

    const percent = Math.min(100, (rms / 50) * 100);
    meterBar.style.width = percent + "%";
    meterBar.style.background = rms > silenceThreshold ? "limegreen" : "red";

    const isQuiet = rms < silenceThreshold;
    const elapsed = Date.now() - recordingStartTime;

    if (isQuiet && elapsed > minSpeechDuration) {
      if (!silenceTimeout) {
        silenceTimeout = setTimeout(() => {
          console.log("⏹️ Silence detected, stopping...");
          mediaRecorder.stop();
          silenceTimeout = null;
        }, minSilenceDuration);
      }
    } else {
      clearTimeout(silenceTimeout);
      silenceTimeout = null;
    }

    requestAnimationFrame(loop);
  }
  loop();
}

// -------------------
// Fallback stop
// -------------------
function forceStop() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    console.log("⏹️ Forced stop (timeout)");
    mediaRecorder.stop();
  }
}

// -------------------
// Send audio → Backend
// -------------------
async function sendToBackend(blob) {
  const formData = new FormData();
  formData.append("audio", blob, "recording.webm");

  const res = await fetch("/chat", { method: "POST", body: formData });
  const data = await res.json();

  console.log("🤖 AI Response:", data.reply_text);

  // display user's transcribed text from Whisper
  if (data.user_text) {
    addMessage(data.user_text, "user");
  } else {
    addMessage("🎤 [voice input sent]", "user");
  }

  // display assistant's reply
  addMessage(data.reply_text, "assistant");

  // play TTS chunks sequentially
  for (const url of data.audio_urls) {
    await playAudio(url);
  }

  setTimeout(startListening, 500);
}

// -------------------
// Play audio helper
// -------------------
function playAudio(url) {
  return new Promise((resolve, reject) => {
    const audio = new Audio(url);
    audio.onplay = () => {
      bubble.classList.add("ai-speaking");
      statusEl.textContent = "AI Speaking...";
    };
    audio.onended = () => {
      bubble.classList.remove("ai-speaking");
      statusEl.textContent = "Idle...";
      resolve();
    };
    audio.onerror = reject;
    audio.play();
  });
}

// -------------------
// Visualizers
// -------------------
const waveCanvas = document.getElementById("waveform");
const spectCanvas = document.getElementById("spectrogram");
const fftCanvas = document.getElementById("fft");

function drawVisuals(analyser, data) {
  const waveCtx = waveCanvas.getContext("2d");
  const spectCtx = spectCanvas.getContext("2d");
  const fftCtx = fftCanvas.getContext("2d");
  let spectData = [];

  function loop() {
    if (!mediaRecorder || mediaRecorder.state !== "recording") return;

    analyser.getByteTimeDomainData(data);

    // waveform
    waveCtx.fillStyle = "#1e1e1e";
    waveCtx.fillRect(0, 0, waveCanvas.width, waveCanvas.height);
    waveCtx.strokeStyle = "lime";
    waveCtx.beginPath();
    const slice = waveCanvas.width / data.length;
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128.0;
      const y = waveCanvas.height / 2 + v * (waveCanvas.height / 2);
      if (i === 0) waveCtx.moveTo(0, y);
      else waveCtx.lineTo(i * slice, y);
    }
    waveCtx.stroke();

    // fft
    const freqData = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(freqData);
    fftCtx.fillStyle = "#1e1e1e";
    fftCtx.fillRect(0, 0, fftCanvas.width, fftCanvas.height);
    const barWidth = fftCanvas.width / freqData.length;
    for (let i = 0; i < freqData.length; i++) {
      const v = freqData[i];
      fftCtx.fillStyle = `rgb(${v+50},50,150)`;
      fftCtx.fillRect(i * barWidth, fftCanvas.height - v/2, barWidth, v/2);
    }

    // spectrogram
    const col = spectCanvas.height;
    const spectColumn = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(spectColumn);
    spectData.push([...spectColumn]);
    if (spectData.length > spectCanvas.width) spectData.shift();

    spectCtx.fillStyle = "#1e1e1e";
    spectCtx.fillRect(0, 0, spectCanvas.width, spectCanvas.height);
    for (let x = 0; x < spectData.length; x++) {
      for (let y = 0; y < col; y++) {
        const v = spectData[x][y];
        spectCtx.fillStyle = `rgb(${v}, ${v/2}, ${255-v})`;
        spectCtx.fillRect(x, col - y, 1, 1);
      }
    }

    requestAnimationFrame(loop);
  }
  loop();
}

// -------------------
// Auto-start loop
// -------------------
startListening();
