import os
from typing import Optional, Dict, Any

import requests
import streamlit as st


class LLMService:
    """Simple wrapper for a local Ollama instance. If Ollama is unreachable,
    the methods will return None (caller should gracefully fall back).
    """

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama2")

    def _post(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.host}/api/generate"
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def summarize(self, text: str, max_tokens: int = 150) -> Optional[str]:
        if not text:
            return None
        prompt = (
            "Summarize the following job description in 2-3 concise sentences:\n\n" + text
        )
        payload = {"model": self.model, "prompt": prompt, "max_tokens": max_tokens}
        data = self._post(payload)
        if not data:
            return None
        # Best-effort: try common response shapes
        if isinstance(data, dict):
            if "text" in data:
                return data.get("text")
            if "content" in data:
                return data.get("content")
        return None

    def summarize_description(self, text: str, max_tokens: int = 350) -> Optional[str]:
        """Produce a concise professional summary (120-150 words) focusing on
        role, responsibilities, key skills, seniority, location, and company context.
        """
        if not text:
            return None
        prompt = (
            "Write a concise professional summary (120-150 words) of the following job description."
            " Focus on the role, main responsibilities, key technical and soft skills, seniority level,"
            " location, and company context. Use a neutral professional tone.\n\n" + text
        )
        payload = {"model": self.model, "prompt": prompt, "max_tokens": max_tokens}
        data = self._post(payload)
        if not data:
            return None
        if isinstance(data, dict):
            return data.get("text") or data.get("content")
        return None

    def extract_skills(self, text: str) -> Optional[str]:
        if not text:
            return None
        prompt = (
            "Extract a short comma-separated list of key technical skills/keywords from the job description:\n\n"
            + text
        )
        payload = {"model": self.model, "prompt": prompt, "max_tokens": 80}
        data = self._post(payload)
        if not data:
            return None
        if isinstance(data, dict):
            return data.get("text") or data.get("content")
        return None


# Cached module-level helpers to avoid hashing `self` and speed repeated calls
@st.cache_data(ttl=60 * 60 * 24)
def cached_summarize(host: Optional[str], model: Optional[str], text: str, max_tokens: int = 150) -> Optional[str]:
    svc = LLMService(host=host, model=model)
    return svc.summarize(text, max_tokens=max_tokens)


@st.cache_data(ttl=60 * 60 * 24)
def cached_extract_skills(host: Optional[str], model: Optional[str], text: str) -> Optional[str]:
    svc = LLMService(host=host, model=model)
    return svc.extract_skills(text)


@st.cache_data(ttl=60 * 60 * 24)
def cached_summarize_description(host: Optional[str], model: Optional[str], text: str) -> Optional[str]:
    svc = LLMService(host=host, model=model)
    return svc.summarize_description(text)
