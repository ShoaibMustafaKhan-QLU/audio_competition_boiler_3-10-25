Here’s a clean `README.md` for your project, written in a straightforward style without emojis:

---

# Voice Chat Clone

This project implements a voice-based conversational assistant that integrates real-time speech recognition, large language model responses, and voice cloning. The system allows continuous, natural interaction between a user and an AI assistant with automatic speech detection and animated frontend visualizations.

## Features

* **Automatic Speech Recognition (ASR):**
  Uses Whisper to transcribe user speech into text.

* **Conversational AI:**
  User transcriptions are passed to a Groq-powered large language model, which generates responses in natural language.

* **Voice Cloning (TTS):**
  Assistant responses are synthesized using XTTS v2, cloning the user’s own voice from the current session audio.

* **Silence Detection:**
  Voice activity detection (RMS-based) automatically stops recording after silence is detected, and resumes listening when the AI response is finished.

* **Streaming TTS:**
  Responses are divided into sentences and converted to audio chunks in parallel, so playback starts while longer responses are still being generated.

* **Frontend Visualizations:**

  * Animated talking bubble
  * Chat transcript (user speech + AI responses)
  * Real-time audio visualizers: waveform, FFT bars, spectrogram

* **Noise Handling:**
  Uses browser-level noise suppression, echo cancellation, and gain control to reduce background noise.

## Project Structure

```
.
├── app.py              # FastAPI backend server
├── groq_client.py      # Groq LLM client wrapper
├── tts_clone.py        # XTTS voice cloning wrapper
├── whisper_asr.py      # Whisper ASR wrapper
├── conversation.py     # Conversation memory manager
├── web/
│   ├── index.html      # Frontend UI
│   └── index.js        # Frontend logic (mic, silence detection, visualizers)
├── generated_audio/    # Temporary audio storage
└── README.md
```

## Requirements

### Backend

* Python 3.10+
* FastAPI
* Uvicorn
* Coqui TTS (XTTS v2)
* Whisper
* Groq API client
* NumPy, Librosa (for audio handling)

Install dependencies:

```bash
pip install fastapi uvicorn numpy librosa TTS openai-whisper groq
```

### Frontend

The frontend is plain HTML/JS/CSS. It runs directly in the browser and communicates with the backend via REST endpoints.

## Usage

1. **Start Backend**

```bash
uvicorn app:app --reload
```

2. **Open Frontend**

   * Navigate to `http://127.0.0.1:8000` in your browser.

3. **Interaction Flow**

   * The system starts listening automatically.
   * Speak into the microphone.
   * Whisper transcribes your speech and sends it to the LLM.
   * The assistant response is generated and synthesized into your cloned voice.
   * While the AI speaks, visualizations and chat transcripts are updated.
   * When the response ends, the system automatically resumes listening.

## Customization

* **Silence Detection Sensitivity:**
  Tuned in `index.js` (`silenceThreshold`, `minSilenceDuration`, `minSpeechDuration`).
* **LLM Prompting:**
  Adjust system prompt in `groq_client.py`.
* **UI Styling:**
  Modify `index.html` and CSS for bubble styles, chat box size, or visualizer layout.

## Known Issues

* Some background noise may still leak through depending on hardware.
* Long pauses in speech can trigger premature silence detection if thresholds are too strict.
* Certain voices may sound distorted if the reference audio is too short or noisy.

## Future Improvements

* WebSocket streaming for lower latency.
* Adjustable sensitivity controls in frontend UI.
* Option to switch between multiple cloned voices mid-conversation.
* Collapsible transcript panel to maximize visualization space.

---

Do you want me to also include **example screenshots / diagrams** of the UI and pipeline in this README, or should we keep it strictly text-based for now?
