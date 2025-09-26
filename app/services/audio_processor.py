import whisper
from pydub import AudioSegment
import tempfile
import os

class AudioProcessor:
    def __init__(self):
        self.model = whisper.load_model("large-v3")

    async def process_audio(self, file_path: str) -> str:
        # Convert audio to wav if needed
        audio = AudioSegment.from_file(file_path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio.export(temp_file.name, format="wav")
            result = self.model.transcribe(temp_file.name)
            os.unlink(temp_file.name)
        return result["text"]