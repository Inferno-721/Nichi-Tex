"""
Shared Gemini AI Client

A single, robust wrapper around the Google GenAI SDK used by every service
(parsers, LaTeX generator, prompt analyzer). It centralises:

- lazy client initialisation (so importing a service never crashes)
- a clear `available` flag and `status()` for health checks
- safe text generation that never raises and never returns ``None``
- structured (JSON) generation via ``response_schema`` with parsing/fallback

If the API key is missing, invalid or expired, every method degrades
gracefully: text helpers return the supplied fallback and structured helpers
return ``None`` so callers can fall back to offline (regex) behaviour.
"""

import json
import sys
import threading
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.logger import get_logger
from config.settings import GOOGLE_API_KEY, GEMINI_MODEL, ENABLE_AI

logger = get_logger(__name__)

T = TypeVar("T")

# Detect SDK availability once, at import time, without instantiating a client.
try:
    from google import genai
    from google.genai import types as genai_types

    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on environment
    genai = None
    genai_types = None
    _SDK_AVAILABLE = False
    logger.warning(
        "google-genai SDK not installed. AI features disabled. "
        "Install with: pip install google-genai"
    )

# Whether the installed SDK exposes ThinkingConfig (Gemini 2.5 "thinking").
_SUPPORTS_THINKING = _SDK_AVAILABLE and hasattr(genai_types, "ThinkingConfig")


class AIClient:
    """Thread-safe, lazily-initialised wrapper around the Gemini client."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 disable_thinking: bool = True):
        self.api_key = (api_key if api_key is not None else GOOGLE_API_KEY or "").strip()
        self.model = model or GEMINI_MODEL
        # Disabling "thinking" on Gemini 2.5 models dramatically reduces latency
        # for structured extraction / rewriting tasks, which don't need it.
        self.disable_thinking = disable_thinking
        self._client = None
        self._init_error: Optional[str] = None
        self._lock = threading.Lock()

        if not ENABLE_AI:
            self._init_error = "AI disabled via ENABLE_AI=false"
        elif not _SDK_AVAILABLE:
            self._init_error = "google-genai SDK not installed"
        elif not self.api_key:
            self._init_error = "GOOGLE_API_KEY is not set"

    # ------------------------------------------------------------------ #
    # Initialisation / status
    # ------------------------------------------------------------------ #
    def _ensure_client(self):
        """Create the underlying SDK client on first use."""
        if self._client is not None or self._init_error is not None:
            return self._client

        with self._lock:
            if self._client is not None or self._init_error is not None:
                return self._client
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialised (model: {self.model})")
            except Exception as e:  # pragma: no cover - network/SDK dependent
                self._init_error = str(e)
                logger.error(f"Failed to initialise Gemini client: {e}")
        return self._client

    @property
    def available(self) -> bool:
        """True when the SDK is installed and an API key is configured.

        Note: this does not guarantee the key is valid/unexpired — that is
        only known once a real request is made. Calls degrade gracefully.
        """
        return (
            ENABLE_AI and _SDK_AVAILABLE
            and bool(self.api_key) and self._init_error is None
        )

    def status(self) -> dict:
        """Diagnostic info for health endpoints."""
        return {
            "sdk_installed": _SDK_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "model": self.model,
            "available": self.available,
            "error": self._init_error,
        }

    # ------------------------------------------------------------------ #
    # Generation helpers
    # ------------------------------------------------------------------ #
    def _build_config(self, **extra):
        """Build a GenerateContentConfig, disabling thinking when supported."""
        kwargs = dict(extra)
        if _SUPPORTS_THINKING and self.disable_thinking:
            kwargs["thinking_config"] = genai_types.ThinkingConfig(thinking_budget=0)
        if not kwargs:
            return None
        return genai_types.GenerateContentConfig(**kwargs)

    def generate_text(self, prompt: str, fallback: str = "",
                      max_output_tokens: Optional[int] = None) -> str:
        """Generate plain text. Never raises; returns ``fallback`` on any failure.

        ``max_output_tokens`` caps the response length, which directly bounds
        latency for long-form generations.
        """
        if not self.available:
            return fallback

        client = self._ensure_client()
        if client is None:
            return fallback

        extra = {}
        if max_output_tokens:
            extra["max_output_tokens"] = max_output_tokens

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._build_config(**extra),
            )
            text = getattr(response, "text", None)
            if not text or not text.strip():
                logger.warning("AI returned empty text; using fallback")
                return fallback
            return text.strip()
        except Exception as e:
            logger.warning(f"AI text generation failed: {e}")
            return fallback

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Type[T]] = None,
    ) -> Optional[Any]:
        """Generate a structured JSON response.

        Args:
            prompt: The instruction prompt.
            schema: Optional Pydantic model class used as the response schema.
                    When provided, a validated instance is returned.

        Returns:
            A parsed Pydantic instance (if ``schema`` given), a ``dict``/``list``
            from raw JSON otherwise, or ``None`` if the call fails. Callers
            should treat ``None`` as "fall back to offline behaviour".
        """
        if not self.available:
            return None

        client = self._ensure_client()
        if client is None:
            return None

        config_kwargs: dict = {"response_mime_type": "application/json"}
        if schema is not None:
            config_kwargs["response_schema"] = schema

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._build_config(**config_kwargs),
            )

            # Preferred: SDK-parsed Pydantic instance.
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                return parsed

            # Fallback: parse the raw JSON text ourselves.
            text = getattr(response, "text", None)
            if not text:
                logger.warning("AI returned no JSON text")
                return None
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"AI returned invalid JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"AI structured generation failed: {e}")
            return None


# Shared singleton — services import this rather than building their own client.
_default_client: Optional[AIClient] = None
_default_lock = threading.Lock()


def get_ai_client() -> AIClient:
    """Return the process-wide shared AIClient instance."""
    global _default_client
    if _default_client is None:
        with _default_lock:
            if _default_client is None:
                _default_client = AIClient()
    return _default_client
