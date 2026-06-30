"""
Auris - Pipeline Factory
Builds the right STT → LLM → TTS pipeline from agent model_config.
Written from scratch.
"""
from app.core.config import (
    DEEPGRAM_API_KEY, ELEVENLABS_API_KEY,
    GROQ_API_KEY, OPENAI_API_KEY, SARVAM_API_KEY,
    CARTESIA_API_KEY, ANTHROPIC_API_KEY,
)
from app.services.pipeline.engine import PipelineEngine
from app.services.pipeline.llm.groq_llm import GroqLLM
from app.services.pipeline.llm.openai_llm import OpenAILLM
from app.services.pipeline.llm.anthropic_llm import AnthropicLLM
from app.services.pipeline.stt.deepgram_stt import DeepgramSTT
from app.services.pipeline.stt.sarvam_stt import SarvamSTT
from app.services.pipeline.tts.elevenlabs_tts import ElevenLabsTTS
from app.services.pipeline.tts.sarvam_tts import SarvamTTS
from app.services.pipeline.tts.cartesia_tts import CartesiaTTS


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
    initial_msg = model_config.get("initial_message")

    if llm_provider == "groq":
        llm = GroqLLM(
            api_key=llm_key,
            model=llm_model,
            system_prompt=system_prompt,
            initial_message=initial_msg,
        )
    elif llm_provider == "anthropic":
        llm = AnthropicLLM(
            api_key=llm_key,
            model=llm_model,
            system_prompt=system_prompt,
            initial_message=initial_msg,
        )
    else:  # openai
        llm = OpenAILLM(
            api_key=llm_key,
            model=llm_model,
            system_prompt=system_prompt,
            initial_message=initial_msg,
        )

    # ── TTS ───────────────────────────────────────────────────────────────────
    tts_provider = tts_cfg.get("provider", _default_tts(language))
    tts_key = tts_cfg.get("api_key") or _platform_tts_key(tts_provider)

    if tts_provider == "sarvam":
        tts = SarvamTTS(api_key=tts_key, language=language)
    elif tts_provider == "cartesia":
        voice_id = tts_cfg.get("voice_id", CartesiaTTS.DEFAULT_VOICE_ID)
        tts = CartesiaTTS(api_key=tts_key, voice_id=voice_id)
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
    if provider == "anthropic":
        return "claude-3-5-sonnet-20241022"
    if cost_tier == "premium":
        return "gpt-4o"
    return "gpt-4o-mini"

def _platform_stt_key(provider: str) -> str:
    return SARVAM_API_KEY if provider == "sarvam" else DEEPGRAM_API_KEY

def _platform_llm_key(provider: str) -> str:
    if provider == "groq":
        return GROQ_API_KEY
    if provider == "anthropic":
        return ANTHROPIC_API_KEY
    return OPENAI_API_KEY

def _platform_tts_key(provider: str) -> str:
    if provider == "sarvam":
        return SARVAM_API_KEY
    if provider == "cartesia":
        return CARTESIA_API_KEY
    return ELEVENLABS_API_KEY
