from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI

from app.config import Settings, get_settings


def create_model(settings: Settings | None = None):
    """Create the configured language model."""
    settings = settings or get_settings()

    common = {
        "max_retries": settings.max_retries,
        "timeout": settings.request_timeout_seconds,
    }

    if settings.model_provider == "gpt":
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required.")
        if not settings.azure_openai_deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is required.")

        return AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
            api_key=(
                settings.azure_openai_api_key.get_secret_value()
                if settings.azure_openai_api_key else None
            ),
            max_tokens=settings.max_output_tokens,
            **common,
        )

    if settings.model_provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required.")

        return ChatAnthropic(
            model=settings.model_name,
            api_key=settings.anthropic_api_key,
            max_tokens=settings.max_output_tokens,
            **common,
        )

    if settings.model_provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required.")

        return ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.google_api_key.get_secret_value(),
            max_output_tokens=settings.max_output_tokens,
            **common,
        )

    if settings.model_provider == "llama":
        return ChatOllama(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
            **common,
        )

    if settings.model_provider == "mistral":
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required.")

        return ChatMistralAI(
            model=settings.model_name,
            api_key=settings.mistral_api_key,
            max_tokens=settings.max_output_tokens,
            **common,
        )

    raise ValueError("Unsupported model provider.")
