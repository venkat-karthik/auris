"""
Auris - Groq LLM Processor
Ultra-fast inference via Groq API (Llama models).
Cost-tier: economy. Use for high-volume / cost-sensitive agents.
Written from scratch.
"""
from app.services.pipeline.llm.openai_llm import OpenAILLM


class GroqLLM(OpenAILLM):
    """
    Groq uses the same OpenAI-compatible API.
    Just point to Groq's base URL and use a Llama model.
    """

    DEFAULT_MODEL = "llama-4-scout-17b-16e-instruct"  # Fast + cheap

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        system_prompt: str = "You are a helpful voice assistant.",
        temperature: float = 0.7,
        max_tokens: int = 500,
        initial_message: str | None = None,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            initial_message=initial_message,
        )
        self.name = "groq-llm"
        # Override OpenAI client with Groq base URL
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
