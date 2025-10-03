# app.py
import uuid
import re
from pathlib import Path
import soundfile as sf
from pydub import AudioSegment

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from groq_client import GroqClient
from tts_clone import XTTSClone
from whisper_asr import WhisperASR
from conversation import ConversationMemory

# -------------------
# Setup
# -------------------
app = FastAPI(title="Voice Chat Clone")

groq = GroqClient(api_key="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")
tts = XTTSClone()
asr = WhisperASR()
memory = ConversationMemory()

AUDIO_DIR = Path("generated_audio")
AUDIO_DIR.mkdir(exist_ok=True)

# -------------------
# Helpers
# -------------------
def convert_to_wav(in_path: str) -> str:
    """Convert uploaded audio (webm/ogg/mp4) into wav format."""
    out_path = str(in_path).rsplit(".", 1)[0] + ".wav"
    try:
        audio = AudioSegment.from_file(in_path)
        audio = audio.set_channels(1).set_frame_rate(16000)  # normalize for Whisper/XTTS
        audio.export(out_path, format="wav")
        print(f"🎵 Converted {in_path} → {out_path}")
        return out_path
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None


def is_valid_audio(path: str) -> bool:
    """Ensure audio file is long enough to be used as reference."""
    try:
        data, sr = sf.read(path)
        duration = len(data) / sr
        return duration >= 1.0  # must be at least 1 second
    except Exception as e:
        print(f"❌ Audio validation failed: {e}")
        return False


def sentence_splitter():
    """Return a closure that buffers tokens into sentences."""
    buffer = ""
    def feed(token: str):
        nonlocal buffer
        buffer += token
        if re.search(r"[.!?]\s", buffer):
            sentences = re.split(r"(?<=[.!?])\s+", buffer)
            finished, buffer = sentences[:-1], sentences[-1]
            return finished
        return []
    def flush():
        nonlocal buffer
        last = buffer.strip()
        buffer = ""
        return [last] if last else []
    return feed, flush


def synthesize_sentence(sentence, ref_audio, audio_urls):
    """Sequentially synthesize audio for a sentence."""
    out_path = AUDIO_DIR / f"reply_{uuid.uuid4()}.wav"
    chunk_paths = tts.synthesize(sentence, str(out_path), ref_audio, "en")
    if chunk_paths:
        for cp in chunk_paths:
            audio_urls.append(f"/audio/{Path(cp).name}")
        print(f"🔊 TTS done for: {sentence}")


# -------------------
# Chat Route
# -------------------
@app.post("/chat")
async def chat(audio: UploadFile = File(...)):
    try:
        # Save uploaded file first
        ext = Path(audio.filename).suffix or ".webm"
        raw_path = AUDIO_DIR / f"user_{uuid.uuid4()}{ext}"
        with open(raw_path, "wb") as f:
            f.write(await audio.read())
        print(f"✅ Saved uploaded audio: {raw_path}")

        # Convert to wav
        wav_path = convert_to_wav(str(raw_path))
        if not wav_path:
            raise HTTPException(status_code=400, detail="Failed to convert audio")

        # Validate audio
        if not is_valid_audio(wav_path):
            print("⚠️ Skipping too-short/invalid ref audio")
            return {"user_text": "", "reply_text": "", "audio_urls": []}

        # Step 1: Speech → Text
        user_text = asr.transcribe(wav_path).strip()
        if not user_text:
            print("⚠️ Ignored empty/quiet input")
            return {"user_text": "", "reply_text": "", "audio_urls": []}

        print(f"📝 Transcribed: {user_text}")
        memory.add("user", user_text)

        # Step 2: Stream LLM tokens → sequential sentence-level TTS
        feed, flush = sentence_splitter()
        audio_urls = []
        llm_full_text = ""

        async for token in groq.stream_chat(memory.get()):
            llm_full_text += token
            sentences = feed(token)
            for sentence in sentences:
                print(f"🚀 Synthesizing: {sentence}")
                synthesize_sentence(sentence, wav_path, audio_urls)

        # Flush leftovers
        for sentence in flush():
            print(f"🚀 Synthesizing final: {sentence}")
            synthesize_sentence(sentence, wav_path, audio_urls)

        memory.add("assistant", llm_full_text)

        return {
            "user_text": user_text,
            "reply_text": llm_full_text,
            "audio_urls": audio_urls
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backend error: {str(e)}")


# -------------------
# Serve Audio + Frontend
# -------------------
@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


# Serve frontend
app.mount("/", StaticFiles(directory="web", html=True), name="web")
