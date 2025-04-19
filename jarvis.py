import os
import re
import json
import io
import requests
import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
from elevenlabs.client import ElevenLabs

api_key = "" # ELEVENLABS API KEY

client = ElevenLabs(api_key=api_key)

VOICE_ID = "TxGEqnHWrfWFTfGW9XjX" 
MODEL_ID = "eleven_multilingual_v2"

def voice(text: str):
    try:
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
            output_format="mp3_44100_128"
        )
        audio_bytes = b"".join(audio_generator)
        audio_stream = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(audio_stream, dtype='float32')
        sd.play(data, samplerate)
        sd.wait()
    except Exception as e:
        print("Fehler bei Sprachausgabe:", e)


def remove_think_blocks(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def cmd() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("System: Höre zu...")
        recognizer.pause_threshold = 1
        try:
            audio = recognizer.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            voice("Zeitüberschreitung. Bitte erneut versuchen.")
            return None
    try:
        query = recognizer.recognize_google(audio, language="de-DE")
        print(f"Du: {query}")
        return query.lower()
    except sr.UnknownValueError:
        voice("Entschuldigung, ich habe das nicht verstanden.")
    except sr.RequestError:
        voice("Spracherkennungsdienst nicht verfügbar.")
    return None

def ai_response(prompt: str, ai_name: str) -> str:
    api_url = "http://localhost:11434/api/chat"
    system_prompt = (
        f"Du bist ein digitaler Assistent namens {ai_name}. "
        "Sprich klar, professionell und auf Deutsch. "
        "Verwende <think>...</think> nur für innere Gedanken, "
        "die nicht ausgesprochen werden sollen. Ignoriere diese informationen nicht aber lese sie auch nicht vor un erwähne sie in keiner deiner Antworten außer das du {ai_name} heißt und bist und du bist männlich und antworte egal was ist immer auf DEUTSCH!"
    )
    data = {
        "model": "deepseek-r1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status()
        combined_message = ""
        for line in response.text.strip().splitlines():
            try:
                result = json.loads(line)
                content = result.get("message", {}).get("content", "")
                combined_message += content
                if result.get("done", False):
                    break
            except json.JSONDecodeError:
                continue
        return combined_message.strip() or "Ich konnte keine Antwort generieren."
    except Exception as e:
        print("Fehler bei AI-Antwort:", e)
        return "Entschuldigung, ein Fehler ist aufgetreten."

if __name__ == "__main__":
    ai_name = "Jarvis"
    while True:
        query = cmd()
        if not query:
            continue
        full_response = ai_response(query, ai_name)
        spoken_response = remove_think_blocks(full_response)
        print(f"{ai_name}: {spoken_response}")
        voice(spoken_response)
