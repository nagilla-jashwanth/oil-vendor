"""
LLM factory – returns a LangChain chat model.

Priority:
  1. If USE_AZURE=true  → AzureChatOpenAI
  2. Otherwise          → ChatOpenAI pointed at the local vLLM server
     (vLLM exposes an OpenAI-compatible /v1 endpoint)
"""
from __future__ import annotations
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_llm():
    use_azure = os.getenv("USE_AZURE", "false").lower() == "true"

    if use_azure:
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            temperature=0.1,
            max_tokens=4096,
        )

    # ── vLLM (AMD ROCm) ───────────────────────────────────────────────────────
    from langchain_openai import ChatOpenAI
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    model_name = os.getenv("VLLM_MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.3")

    return ChatOpenAI(
        base_url=base_url,
        api_key="not-needed",          # vLLM doesn't require a real key
        model=model_name,
        temperature=0.1,
        max_tokens=4096,
        # vLLM may not support all OpenAI kwargs – keep this minimal
    )
