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

        # Basic sanitization
        q = (query or "").strip()
        if tech_stack:
            q = f"{q} {tech_stack}".strip()

        # If query is empty, raise a friendly error
        if not q:
            raise ValueError("Query must include job title or keywords.")

        def _valid_location(loc: Optional[str]) -> Optional[str]:
            if not loc:
                return None
            loc_s = loc.strip()
            if len(loc_s) < 2:
                return None
            # Reject purely numeric locations
            if loc_s.isdigit():
                return None
            return loc_s

        sanitized_location = _valid_location(location)

        params: Dict[str, Any] = {
            "engine": "google_jobs",
            "q": q,
            "api_key": self.api_key,
            "num": limit,
        }
        if sanitized_location:
            params["location"] = sanitized_location

        # Attempt request, retry once with simplified query on 4xx/5xx
        last_exc: Optional[Exception] = None
        for attempt in range(2):
            try:
                resp = requests.get(self.BASE, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as exc:
                last_exc = exc
                # On first failure, simplify query and remove location/tech
                if attempt == 0:
                    # keep first two words of q as simplified query
                    simplified = " ".join(q.split()[:2])
                    params["q"] = simplified
                    params.pop("location", None)
                    # don't include explicit tech stack
                    # next attempt will retry with simpler params
                    continue
                raise RuntimeError("Failed to fetch job results from SerpAPI.") from exc

        # The SerpAPI jobs response commonly contains 'jobs_results'
        results: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            if "jobs_results" in data and isinstance(data["jobs_results"], list):
                results = data["jobs_results"]
            else:
                for k, v in data.items():
                    if isinstance(v, list):
                        results = v
                        break

        if not isinstance(results, list):
            results = []

        # Ensure each result has a link if possible: try common fields and related links
        def _find_link(item: Dict[str, Any]) -> Optional[str]:
            for key in ("url", "link", "apply_link"):
                val = item.get(key)
                if isinstance(val, str) and val:
                    return val
            # look for related_links or similar structures
            for alt in ("related_links", "other_links", "links"):
                v = item.get(alt)
                if isinstance(v, list) and v:
                    for entry in v:
                        if isinstance(entry, dict) and "url" in entry:
                            return entry.get("url")
                        if isinstance(entry, str):
                            return entry
            return None

        for it in results:
            if not _find_link(it):
                # try to populate from nested keys
                link = None
                for v in it.values():
                    if isinstance(v, dict):
                        for subk in ("url", "link"):
                            if subk in v and isinstance(v[subk], str):
                                link = v[subk]
                                break
                        if link:
                            break
                if link:
                    it.setdefault("apply_link", link)

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
