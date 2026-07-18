"""
backend/openrouter_client.py
-----------------------------
Secure, reusable client for the OpenRouter Chat Completions API.

This module powers "LearnMate AI" - a friendly, professional AI Career
Mentor for college students and early-career professionals. It answers
questions about career guidance, personalized learning roadmaps, resume
improvement, interview preparation, skills-gap analysis, certifications,
AI careers, and programming.

Design notes (mirrors backend/watsonx_client.py for consistency):
- Credentials are read only from `config.py` (which itself only reads
  from environment variables / Streamlit secrets) - never hard-coded.
- Uses the `requests` library only (no OpenAI/OpenRouter SDK dependency).
- Retries transient network errors with exponential backoff via tenacity.
- Never raises raw exceptions to the UI layer - every failure path
  returns a friendly, human-readable string so Streamlit never crashes.
"""

from __future__ import annotations

from typing import Any, Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import OPENROUTER_CONFIG, OpenRouterConfig
from backend.logger_setup import get_logger

logger = get_logger(__name__)

# OpenRouter's OpenAI-compatible chat completions endpoint.
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# How long to wait (seconds) for OpenRouter to respond before giving up.
REQUEST_TIMEOUT_SECONDS = 60

# Maximum number of previous turns (user + assistant pairs) to replay back
# to the model. Keeps the payload small and the mentor focused on recent
# context instead of an ever-growing conversation history.
MAX_HISTORY_MESSAGES = 12

# System prompt that defines LearnMate AI's persona and scope. Kept here
# (rather than in the UI layer) so the persona travels with the client and
# stays consistent no matter which page/widget calls generate_chat_response().
SYSTEM_PROMPT = """\
You are LearnMate AI, a friendly and professional AI Career Mentor built \
to help college students and early-career professionals grow their \
careers, especially in technology and AI-related fields.

You specialize in:
- Career guidance and direction setting
- Personalized learning roadmaps
- Resume and LinkedIn profile improvement
- Interview preparation (technical and behavioral)
- Skills-gap analysis
- Certifications and course recommendations
- AI, data, and software careers
- Programming help and best practices
- General guidance for college students entering the workforce

Your tone is warm, encouraging, and beginner-friendly, while still being \
precise and practical. Prefer clear, actionable, and well-structured \
answers (short paragraphs or bullet points) over long walls of text. When \
a question is outside your career-mentoring scope, gently redirect the \
user back to career, learning, or skill-development topics.\
"""


class OpenRouterError(Exception):
    """Raised for any recoverable OpenRouter client/API error."""


class OpenRouterConfigError(OpenRouterError):
    """Raised when required OpenRouter configuration is missing."""


class OpenRouterClient:
    """Thin, secure wrapper around OpenRouter's Chat Completions endpoint."""

    def __init__(self, config: Optional[OpenRouterConfig] = None):
        # Fall back to the shared, environment-driven singleton config so
        # callers don't need to wire credentials through by hand.
        self.config = config or OPENROUTER_CONFIG

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_messages(
        self, message: str, chat_history: Optional[list[dict[str, str]]]
    ) -> list[dict[str, str]]:
        """Assemble the OpenAI-style `messages` array for the API call.

        Args:
            message: The user's latest message.
            chat_history: Optional prior turns, each a dict shaped like
                {"role": "user" | "assistant", "content": "..."}. Any
                other shape is safely skipped rather than raising.

        Returns:
            A list of role/content dicts, starting with the system
            prompt, followed by trimmed prior history, then the new
            user message.
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if chat_history:
            # Only keep the most recent turns so the request payload
            # stays small and the model stays focused on recent context.
            trimmed_history = chat_history[-MAX_HISTORY_MESSAGES:]
            for turn in trimmed_history:
                role = turn.get("role")
                content = turn.get("content")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": str(content)})

        messages.append({"role": "user", "content": message})
        return messages

    # ------------------------------------------------------------------
    # Chat completion
    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        # Only retry on transient network issues - never retry on 4xx/5xx
        # HTTP responses, since those are handled (and returned as
        # friendly messages) explicitly below.
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def _post_chat_completion(self, payload: dict[str, Any]) -> requests.Response:
        """POST the chat-completion request to OpenRouter with retries."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            # OpenRouter uses these optional headers for its public app
            # rankings/analytics - harmless to include, safe to omit.
            "HTTP-Referer": "https://learnmate.ai",
            "X-Title": "LearnMate AI Career Mentor",
        }
        return requests.post(
            OPENROUTER_API_URL,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    def generate_chat_response(
        self,
        message: str,
        chat_history: Optional[list[dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a LearnMate AI mentor reply for a single chat turn.

        Args:
            message: The user's latest message/question.
            chat_history: Optional list of prior turns, oldest first,
                each shaped like {"role": "user"/"assistant", "content": str}.
            temperature: Sampling temperature (higher = more creative).
            max_tokens: Maximum number of tokens to generate in the reply.

        Returns:
            The assistant's reply as plain text. On any failure (missing
            config, network issue, bad response, etc.) this returns a
            friendly, user-safe error message instead of raising.
        """
        # Guard against empty input up front - no need to call the API.
        if not message or not message.strip():
            return "Please type a question so I can help you with your career journey!"

        if not self.config.is_configured:
            logger.error("OpenRouter is not configured (missing API key or model).")
            return (
                "LearnMate AI's chat mentor isn't fully configured yet. "
                "Please set OPENROUTER_API_KEY and OPENROUTER_MODEL and try again."
            )

        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": self._build_messages(message, chat_history),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # --- Network call -------------------------------------------------
        try:
            response = self._post_chat_completion(payload)
        except (requests.ConnectionError, requests.Timeout) as exc:
            # These are the only exceptions tenacity retries; if we're
            # still here, all retry attempts were exhausted.
            logger.error("OpenRouter request failed after retries: %s", exc)
            return (
                "I'm having trouble connecting to the AI service right now. "
                "Please check your internet connection and try again in a moment."
            )
        except requests.RequestException as exc:
            logger.error("OpenRouter request failed: %s", exc)
            return "Something went wrong while reaching the AI service. Please try again."

        # --- HTTP status handling ------------------------------------------
        if response.status_code == 401:
            logger.error("OpenRouter auth failed (401): %s", response.text[:300])
            return (
                "I couldn't authenticate with the AI service. "
                "Please check that OPENROUTER_API_KEY is valid."
            )

        if response.status_code == 402:
            logger.error("OpenRouter quota/billing error (402): %s", response.text[:300])
            return (
                "The AI service reported a billing/credit issue with the "
                "configured OpenRouter account. Please check your OpenRouter balance."
            )

        if response.status_code == 429:
            logger.warning("OpenRouter rate limited (429): %s", response.text[:300])
            return (
                "I'm getting a lot of requests right now. "
                "Please wait a few seconds and try asking again."
            )

        if response.status_code == 404:
            logger.error(
                "OpenRouter 404 - model not found (model=%s): %s",
                self.config.model,
                response.text[:300],
            )
            return (
                "The configured AI model could not be found on OpenRouter. "
                "Please check the OPENROUTER_MODEL setting."
            )

        if response.status_code >= 400:
            logger.error(
                "OpenRouter error [%s]: %s", response.status_code, response.text[:500]
            )
            return (
                "The AI service returned an error while generating a reply. "
                "Please try again in a moment."
            )

        # --- Parse the successful response ---------------------------------
        try:
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            return reply.strip() if reply else (
                "I wasn't able to generate a response that time - could you "
                "please rephrase your question?"
            )
        except (KeyError, IndexError, ValueError) as exc:
            logger.error("Unexpected OpenRouter response shape: %s", response.text[:500])
            return "I received an unexpected response from the AI service. Please try again."

    def health_check(self) -> bool:
        """Lightweight check that OpenRouter credentials/config look valid."""
        return self.config.is_configured


# ----------------------------------------------------------------------
# Module-level singleton + convenience function for easy reuse across the
# Streamlit app, mirroring the `watsonx_client` singleton pattern.
# ----------------------------------------------------------------------
openrouter_client = OpenRouterClient()


def generate_chat_response(
    message: str,
    chat_history: Optional[list[dict[str, str]]] = None,
) -> str:
    """Convenience wrapper around the shared OpenRouterClient singleton.

    This is the primary entry point most of the app should use:

        from backend.openrouter_client import generate_chat_response

        reply = generate_chat_response(
            "How do I break into an AI career?",
            chat_history=st.session_state.chat_history,
        )

    Args:
        message: The user's latest message.
        chat_history: Optional prior conversation turns (oldest first),
            each a dict like {"role": "user"/"assistant", "content": str}.

    Returns:
        The mentor's reply as plain text, or a friendly error message
        if anything went wrong.
    """
    return openrouter_client.generate_chat_response(message, chat_history)
