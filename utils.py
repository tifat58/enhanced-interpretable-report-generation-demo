import whisper
import pydub
from io import BytesIO

def simulate_file_upload(file_name):
    with open(file_name, 'rb') as f:
        file_data = BytesIO(f.read())
        file_data.name = file_name
    return file_data

def transcribe(file):
    model = whisper.load_model("base")
    result = model.transcribe(file)
    return result['text']