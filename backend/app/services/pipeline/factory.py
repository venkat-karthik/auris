"""
Auris - Pipeline Factory
Builds the right STT → LLM → TTS pipeline from agent model_config.
Written from scratch.
"""
from app.core.config import (
    DEEPGRAM_API_KEY, ELEVENLABS_API_KEY,
    GROQ_API_KEY, OPENAI_API_KEY, SARVAM_API_KEY,
)
from app.services.pipeline.engine import PipelineEngine
from app.services.pipeline.llm.groq_llm import GroqLLM
from app.services.pipeline.llm.openai_llm import OpenAILLM
from app.services.pipeline.stt.deepgram_stt import DeepgramSTT
from app.services.pipeline.stt.sarvam_stt import SarvamSTT
from app.services.pipeline.tts.elevenlabs_tts import ElevenLabsTTS
from app.services.pipeline.tts.sarvam_tts import SarvamTTS


def build_pipeline(
    model_config: dict,
    system_prompt: str,
    language: str = "en",
) -> PipelineEngine:
    """
    model_config shape:
    {
      "cost_tier": "economy" | "standard" | "premium",   # optional
      "stt": {"provider": "deepgram"|"sarvam", "api_key": "...", "model": "..."},
      "llm": {"provider": "openai"|"groq", "api_key": "...", "model": "..."},
      "tts": {"provider": "elevenlabs"|"sarvam", "api_key": "...", "voice_id": "..."},
    }
    If api_key is missing in config, falls back to platform master key from env.
    """

    stt_cfg = model_config.get("stt", {})
    llm_cfg = model_config.get("llm", {})
    tts_cfg = model_config.get("tts", {})
    cost_tier = model_config.get("cost_tier", "standard")

    # ── STT ───────────────────────────────────────────────────────────────────
    stt_provider = stt_cfg.get("provider", _default_stt(language))
    stt_key = stt_cfg.get("api_key") or _platform_stt_key(stt_provider)

    if stt_provider == "sarvam":
        stt = SarvamSTT(api_key=stt_key, language=language)
    else:  # deepgram (default for en)
        stt_model = stt_cfg.get("model", "nova-2")
        stt = DeepgramSTT(api_key=stt_key, language=language, model=stt_model)

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_provider = llm_cfg.get("provider", _default_llm(cost_tier))
    llm_key = llm_cfg.get("api_key") or _platform_llm_key(llm_provider)
    llm_model = llm_cfg.get("model") or _default_llm_model(llm_provider, cost_tier)

    if llm_provider == "groq":
        llm = GroqLLM(
            api_key=llm_key,
            model=llm_model,
            system_prompt=system_prompt,
        )
    else:  # openai
        llm = OpenAILLM(
            api_key=llm_key,
            model=llm_model,
            system_prompt=system_prompt,
        )

    # ── TTS ───────────────────────────────────────────────────────────────────
    tts_provider = tts_cfg.get("provider", _default_tts(language))
    tts_key = tts_cfg.get("api_key") or _platform_tts_key(tts_provider)

    if tts_provider == "sarvam":
        tts = SarvamTTS(api_key=tts_key, language=language)
    else:  # elevenlabs (default for en)
        voice_id = tts_cfg.get("voice_id", ElevenLabsTTS.DEFAULT_VOICE_ID)
        tts = ElevenLabsTTS(api_key=tts_key, voice_id=voice_id)

    from app.services.pipeline.stt.vad import VADProcessor
    vad = VADProcessor()

    return PipelineEngine(processors=[vad, stt, llm, tts])


# ── Defaults ──────────────────────────────────────────────────────────────────

def _default_stt(language: str) -> str:
    return "sarvam" if language in ("hi", "te", "ta", "kn", "mr", "bn") else "deepgram"

def _default_tts(language: str) -> str:
    return "sarvam" if language in ("hi", "te", "ta", "kn", "mr", "bn") else "elevenlabs"

def _default_llm(cost_tier: str) -> str:
    return "groq" if cost_tier == "economy" else "openai"

def _default_llm_model(provider: str, cost_tier: str) -> str:
    if provider == "groq":
        return "llama-4-scout-17b-16e-instruct"
    if cost_tier == "premium":
        return "gpt-4o"
    return "gpt-4o-mini"

def _platform_stt_key(provider: str) -> str:
    return SARVAM_API_KEY if provider == "sarvam" else DEEPGRAM_API_KEY

def _platform_llm_key(provider: str) -> str:
    return GROQ_API_KEY if provider == "groq" else OPENAI_API_KEY

def _platform_tts_key(provider: str) -> str:
    return SARVAM_API_KEY if provider == "sarvam" else ELEVENLABS_API_KEY
