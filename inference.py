import torch
from TTS.api import TTS

# -------------------
# Config
# -------------------
TEXT = "Hello, this is my cloned voice speaking locally with XTTS v2."
REFERENCE_AUDIO = "my_reference.wav"
OUTPUT_PATH = "cloned_voice.wav"
LANG = "hi"  # "en", "es", "fr", "de", etc.

# -------------------
# Load XTTS v2
# -------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device=="cuda"))

# -------------------
# Generate audio
# -------------------
tts.tts_to_file(
    text=TEXT,
    file_path=OUTPUT_PATH,
    speaker_wav=REFERENCE_AUDIO,
    language=LANG
)

print(f"✅ Done! Your cloned audio is saved at {OUTPUT_PATH}")


