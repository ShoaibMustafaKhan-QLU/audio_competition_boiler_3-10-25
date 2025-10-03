# tts_clone.py
import torch
import re
from TTS.api import TTS

MAX_CHARS = 300  # safe chunk length


def clean_text(text: str) -> str:
    """Normalize text for XTTS input."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def safe_chunk(text: str, max_chars=MAX_CHARS):
    """Split text into smaller chunks."""
    text = clean_text(text)
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


class XTTSClone:
    def __init__(self, model_name="tts_models/multilingual/multi-dataset/xtts_v2", device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🔊 Loading XTTS model on {self.device} ...")
        self.tts = TTS(model_name, gpu=(self.device == "cuda"))

    def synthesize(self, text: str, out_path: str, ref_audio: str, lang: str = "en"):
        """Generate cloned audio for the given text using reference audio."""
        if not text.strip():
            print("⚠️ Empty text given to TTS, skipping.")
            return []

        chunks = safe_chunk(text)
        outputs = []

        for i, chunk in enumerate(chunks):
            try:
                wav = self.tts.tts(
                    text=chunk,
                    speaker_wav=ref_audio,   # always use current speaker audio
                    language=lang
                )
                chunk_path = out_path if i == 0 else out_path.replace(".wav", f"_{i}.wav")
                self.tts.synthesizer.save_wav(wav, chunk_path)
                print(f"✅ Saved TTS chunk {i} → {chunk_path}")
                outputs.append(chunk_path)
            except Exception as e:
                print(f"❌ XTTS failed on chunk {i}: {chunk[:50]}... error={e}")
                continue

        return outputs
