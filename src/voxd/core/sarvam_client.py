from __future__ import annotations

from pathlib import Path
from typing import Any

from sarvamai import SarvamAI


class SarvamSTTClient:
    def __init__(self, api_key: str, model: str, language_code: str):
        if not api_key:
            raise ValueError("Missing SARVAM_API_KEY")
        self._client = SarvamAI(api_subscription_key=api_key)
        self._model = model
        self._language_code = language_code

    def transcribe(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            response = self._client.speech_to_text.transcribe(
                file=audio_file,
                model=self._model,
                language_code=self._language_code,
            )
        return self._extract_text(response)

    def _extract_text(self, response: Any) -> str:
        if response is None:
            return ""

        # SDK may return object-like or dict-like responses.
        for key in ("transcript", "text"):
            value = getattr(response, key, None)
            if isinstance(value, str):
                return value.strip()

        if isinstance(response, dict):
            for key in ("transcript", "text"):
                value = response.get(key)
                if isinstance(value, str):
                    return value.strip()

        results = getattr(response, "results", None)
        if isinstance(results, list):
            chunks = []
            for item in results:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("transcript")
                else:
                    text = getattr(item, "text", None) or getattr(item, "transcript", None)
                if text:
                    chunks.append(str(text).strip())
            return " ".join(chunks).strip()

        return str(response).strip()
