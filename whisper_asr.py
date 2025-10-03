import whisper

class WhisperASR:
    def __init__(self, model="small"):
        self.model = whisper.load_model(model)

    def transcribe(self, audio_file: str) -> str:
        """Transcribe audio (wav, mp3, webm) to text"""
        result = self.model.transcribe(audio_file)
        return result["text"].strip()
