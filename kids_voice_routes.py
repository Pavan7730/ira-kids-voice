import os
import tempfile
import traceback
import logging
from urllib.parse import quote
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kids", tags=["Kids Voice"])

groq_client    = Groq(api_key=os.getenv("GROQ_API_KEY"))
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")

CHARACTERS = {
    "doro": {
        "voice_id": os.getenv("VOICE_DORO"),
        "system": "You are Doro, a friendly enthusiastic robot who loves helping children learn! Speak in simple fun language kids aged 5-12 can understand. Keep responses SHORT — 2 to 3 sentences maximum. Always be warm, encouraging, and curious. You can say Beep boop occasionally."
    },
    "chintu": {
        "voice_id": os.getenv("VOICE_CHINTU"),
        "system": "You are Chintu, a fun lovable cartoon character who makes learning hilarious! Keep responses SHORT — 2 to 3 sentences maximum. Make kids laugh while sneaking in real learning. Use phrases like Hehe, Oops, No way!"
    },
    "bheemu": {
        "voice_id": os.getenv("VOICE_BHEEMU"),
        "system": "You are Bheemu, a strong brave cartoon hero who loves helping children! Keep responses SHORT — 2 to 3 sentences maximum. Use phrases like We can do this together, Nothing is impossible!"
    }
}

LANGUAGE_CODES = {
    "english": "en",
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "kannada": "kn"
}


@router.post("/converse")
async def full_pipeline(
    audio: UploadFile = File(...),
    character: str = Form("doro"),
    language: str = Form("english")
):
    try:
        logger.info(f"=== New request: character={character}, language={language} ===")
        
        char = CHARACTERS.get(character.lower(), CHARACTERS["doro"])
        lang_code = LANGUAGE_CODES.get(language.lower(), "en")

        # Step 1: Transcribe
        logger.info("Step 1: Transcribing audio...")
        audio_bytes = await audio.read()
        logger.info(f"Audio size: {len(audio_bytes)} bytes")

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=("audio.webm", f, "audio/webm"),
                    model="whisper-large-v3",
                    language=lang_code,
                    response_format="text"
                )
        finally:
            os.unlink(tmp_path)

        kid_text = str(transcription).strip()
        logger.info(f"Kid said: {kid_text}")

        if not kid_text:
            return JSONResponse({"error": "Could not hear anything"}, status_code=400)

        # Step 2: LLaMA via Groq
        logger.info("Step 2: Getting LLM response...")
        lang_instruction = f"Respond ONLY in {language.capitalize()}." if language.lower() != "english" else ""
        system_prompt = f"{char['system']} {lang_instruction}".strip()

        llm_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=150,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": kid_text}
            ]
        )
        reply_text = llm_response.choices[0].message.content.strip()
        logger.info(f"AI replied: {reply_text}")

        # Step 3: ElevenLabs TTS
        logger.info("Step 3: Calling ElevenLabs...")
        voice_id = char["voice_id"]
        logger.info(f"Voice ID: {voice_id}")
        logger.info(f"ElevenLabs key starts with: {ELEVENLABS_KEY[:10] if ELEVENLABS_KEY else 'MISSING'}")

        if not voice_id:
            raise HTTPException(status_code=500, detail="Voice ID not set!")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
        payload = {
            "text": reply_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.80,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }

        tts_response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        logger.info(f"ElevenLabs status: {tts_response.status_code}")

        if tts_response.status_code != 200:
            logger.error(f"ElevenLabs error: {tts_response.text}")
            raise HTTPException(status_code=500, detail=f"ElevenLabs error: {tts_response.text}")

        logger.info("Success! Streaming audio back...")
        return StreamingResponse(
            tts_response.iter_content(chunk_size=2048),
            media_type="audio/mpeg",
            headers={
                "X-Kid-Said": quote(kid_text),
                "X-AI-Replied": quote(reply_text),
                "X-Character": character,
                "Access-Control-Expose-Headers": "X-Kid-Said, X-AI-Replied, X-Character"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health():
    return {
        "status": "ok",
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "elevenlabs": bool(ELEVENLABS_KEY),
        "voice_doro": os.getenv("VOICE_DORO"),
        "voice_chintu": os.getenv("VOICE_CHINTU"),
        "voice_bheemu": os.getenv("VOICE_BHEEMU"),
    }
