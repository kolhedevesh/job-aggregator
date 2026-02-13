import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


class SerpApiClient:
    """Minimal SerpAPI client using the public search endpoint.

    Uses the `engine=google_jobs` parameter to fetch job listings.
    """

    BASE = "https://serpapi.com/search.json"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")

    def search(
        self,
        query: str,
        location: Optional[str] = None,
        remote: Optional[str] = None,
        experience_level: Optional[str] = None,
        employment_type: Optional[str] = None,
        tech_stack: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY is not configured")

        q = query or ""
        if tech_stack:
            q = f"{q} {tech_stack}".strip()

        params: Dict[str, Any] = {
            "engine": "google_jobs",
            "q": q,
            "api_key": self.api_key,
            "num": limit,
        }
        if location:
            params["location"] = location

        # Some optional filters can be passed in the query or left to normalizer
        try:
            resp = requests.get(self.BASE, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # keep failure simple for UI
            raise RuntimeError(f"SerpAPI request failed: {exc}") from exc

        # The SerpAPI jobs response commonly contains 'jobs_results'
        results: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            if "jobs_results" in data and isinstance(data["jobs_results"], list):
                results = data["jobs_results"]
            else:
                # fallback: if a results-like list is present under other keys
                for k, v in data.items():
                    if isinstance(v, list):
                        results = v
                        break

        if not isinstance(results, list):
            results = []

        return results


# Module-level cached wrapper to avoid hashing `self`.
@st.cache_data(ttl=300)
def cached_search(
    api_key: str,
    q: str,
    location: Optional[str] = None,
    remote: Optional[str] = None,
    experience_level: Optional[str] = None,
    employment_type: Optional[str] = None,
    tech_stack: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    client = SerpApiClient(api_key=api_key)
    return client.search(
        query=q,
        location=location,
        remote=remote,
        experience_level=experience_level,
        employment_type=employment_type,
        tech_stack=tech_stack,
        limit=limit,
    )
