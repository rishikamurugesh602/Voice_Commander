"""
voice_service.py
------------------
Converts recorded audio bytes into text using Google's free Speech-to-Text API.
"""

import speech_recognition as sr
import io
from pydub import AudioSegment


LANGUAGE_CODES = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
}


def transcribe_audio(audio_bytes, language="English"):
    """
    Takes raw audio bytes (from streamlit-mic-recorder) and returns transcribed text.
    Returns (success: bool, result: str) — result is either the transcript or an error message.
    """
    try:
        # Convert whatever format the mic gave us into WAV (what SpeechRecognition needs)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        lang_code = LANGUAGE_CODES.get(language, "en-IN")
        text = recognizer.recognize_google(audio_data, language=lang_code)
        return True, text

    except sr.UnknownValueError:
        return False, "Could not understand the audio. Please try speaking more clearly."
    except sr.RequestError:
        return False, "Speech recognition service is unavailable. Check your internet connection."
    except Exception as e:
        return False, f"Error processing audio: {str(e)}"