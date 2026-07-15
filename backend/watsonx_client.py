"""
backend/watsonx_client.py
---------------------------
Secure, reusable client for the IBM watsonx.ai foundation model REST API
(Granite models or any other model deployed on your watsonx.ai project).

- Credentials are read only from `config.CONFIG` (which itself only reads
  from environment variables / Streamlit secrets) - never hard-coded.
- Handles IBM Cloud IAM token exchange + caching (tokens expire ~1 hour).
- Retries transient network errors with exponential backoff.
- Raises typed exceptions the UI layer can catch and display cleanly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import CONFIG, WatsonxConfig
from backend.logger_setup import get_logger

logger = get_logger(__name__)

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class WatsonxError(Exception):
    """Raised for any recoverable watsonx.ai client/API error."""


class WatsonxAuthError(WatsonxError):
    """Raised when IAM authentication fails (bad/missing API key)."""


class WatsonxConfigError(WatsonxError):
    """Raised when required configuration is missing."""


@dataclass
class _CachedToken:
    token: str
    expires_at: float


class WatsonxClient:
    """Thin, secure wrapper around IBM watsonx.ai's text-generation endpoint."""

    def __init__(self, config: Optional[WatsonxConfig] = None):
        self.config = config or CONFIG
        self._cached_token: Optional[_CachedToken] = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _get_access_token(self) -> str:
        if self._cached_token and self._cached_token.expires_at - 60 > time.time():
            return self._cached_token.token

        if not self.config.api_key:
            raise WatsonxConfigError(
                "WATSONX_API_KEY is not set. Add it to your .env file or "
                "Streamlit secrets."
            )

        try:
            resp = requests.post(
                IAM_TOKEN_URL,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.config.api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=20,
            )
        except requests.RequestException as exc:
            logger.error("IAM token request failed: %s", exc)
            raise WatsonxError(f"Could not reach IBM Cloud IAM: {exc}") from exc

        if resp.status_code != 200:
            logger.error("IAM auth failed [%s]: %s", resp.status_code, resp.text[:300])
            raise WatsonxAuthError(
                "IBM Cloud authentication failed. Check that WATSONX_API_KEY "
                "is valid and active."
            )

        payload = resp.json()
        token = payload["access_token"]
        expires_in = payload.get("expires_in", 3600)
        self._cached_token = _CachedToken(token=token, expires_at=time.time() + expires_in)
        return token

    # ------------------------------------------------------------------
    # Text generation
    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        max_new_tokens: int = 2500,
        temperature: float = 0.6,
    ) -> str:
        """Call the watsonx.ai /text/generation endpoint and return raw text."""
        if not self.config.is_configured:
            raise WatsonxConfigError(
                "watsonx.ai is not fully configured. Please set "
                "WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL and "
                "WATSONX_MODEL_ID in your .env file."
            )

        token = self._get_access_token()
        url = (
            f"{self.config.base_url.rstrip('/')}/ml/v1/text/generation"
            f"?version={self.config.api_version}"
        )

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        body: dict[str, Any] = {
            "input": full_prompt,
            "model_id": self.config.model_id,
            "project_id": self.config.project_id,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_new_tokens,
                "min_new_tokens": 50,
                "temperature": temperature,
                "repetition_penalty": 1.05,
            },
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=90)
        except requests.RequestException as exc:
            logger.error("watsonx.ai request failed: %s", exc)
            raise

        if resp.status_code == 401:
            # Token might have just expired server-side - clear cache once
            self._cached_token = None
            raise WatsonxAuthError("watsonx.ai rejected the request (401 Unauthorized).")

        if resp.status_code >= 400:
            logger.error("watsonx.ai error [%s]: %s", resp.status_code, resp.text[:500])
            raise WatsonxError(
                f"watsonx.ai returned an error ({resp.status_code}). "
                f"Check your Project ID, Model ID, and region URL."
            )

        data = resp.json()
        try:
            return data["results"][0]["generated_text"].strip()
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected watsonx.ai response shape: %s", data)
            raise WatsonxError("Unexpected response format from watsonx.ai.") from exc

    def health_check(self) -> bool:
        """Lightweight check that credentials + connectivity are valid."""
        try:
            self._get_access_token()
            return True
        except WatsonxError as exc:
            logger.warning("Health check failed: %s", exc)
            return False


# Module-level singleton for convenient reuse across the Streamlit app
watsonx_client = WatsonxClient()
