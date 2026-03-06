import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
import time


class SerpApiClient:
    """Minimal SerpAPI client using the public search endpoint.

    Uses the `engine=google_jobs` parameter to fetch job listings.
    """

    BASE = "https://serpapi.com/search.json"

    def __init__(self, api_key: Optional[str] = None):
        try:
            self.api_key = api_key or st.secrets["SERPAPI_API_KEY"]
        except Exception:
            self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        # Log presence only (do NOT log the actual key)
        try:
            self.logger.debug("SERPAPI_API_KEY_present: %s", bool(self.api_key))
        except Exception:
            pass

        debug_flag = os.getenv("JOB_AGG_DEBUG", "false").lower() in ("1", "true", "yes")
        if debug_flag:
            self.logger.setLevel(logging.DEBUG)

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

        # Basic sanitization and query-building
        q = (query or "").strip()
        parts: List[str] = []
        if q:
            parts.append(q)
        # If filters are provided but not supported as params by SerpAPI,
        # we append them to the free-text query to influence results.
        if remote:
            parts.append(remote)
        if experience_level:
            parts.append(experience_level)
        if employment_type:
            parts.append(employment_type)
        if tech_stack:
            parts.append(tech_stack)
        q_final = " ".join(parts).strip()

        # If query is empty, raise a friendly error
        if not q_final:
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

        # Helper to sanitize location per requirements
        def _sanitize_location(loc: Optional[str]) -> Optional[str]:
            if not loc:
                return None
            s = loc.strip()
            if not s:
                return None
            if s.lower() == "anywhere":
                return None
            # keep first two comma-separated tokens
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if not parts:
                return None
            return ", ".join(parts[:2])

        sanitized_location = _sanitize_location(location)

        # Build paged starts (0,10,20...) up to limit
        step = 10
        starts = list(range(0, limit, step))

        def _do_paged_fetch(q_text: str, loc: Optional[str]):
            results: List[Dict[str, Any]] = []
            provider_limited = False
            last_len = 0
            last_params = {}
            for start in starts:
                params: Dict[str, Any] = {"engine": "google_jobs", "q": q_text, "api_key": self.api_key, "start": start}
                if loc:
                    params["location"] = loc
                last_params = params
                # Log parameters but mask api_key
                try:
                    masked = {k: ("<hidden>" if k.lower() == "api_key" else v) for k, v in params.items()}
                    self.logger.debug("SerpAPI request params (masked): %s", masked)
                except Exception:
                    pass

                resp = requests.get(self.BASE, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                page_items: List[Dict[str, Any]] = []
                if isinstance(data, dict):
                    if "jobs_results" in data and isinstance(data["jobs_results"], list):
                        page_items = data["jobs_results"]
                    else:
                        for k, v in data.items():
                            if isinstance(v, list):
                                page_items = v
                                break

                if not isinstance(page_items, list):
                    page_items = []

                results.extend(page_items)
                if len(results) == last_len:
                    provider_limited = True
                    break
                last_len = len(results)
            return results, provider_limited, last_params

        # Try initial fetch
        try:
            results, provider_limited, last_params = _do_paged_fetch(q_final, sanitized_location)
        except Exception:
            # Retry 1: simplified q (first two words), omit location
            simple_q = " ".join(q_final.split()[:2]) or q_final
            try:
                results, provider_limited, last_params = _do_paged_fetch(simple_q, None)
            except Exception:
                # Retry 2: final fallback: use original query without injected filters
                try:
                    results, provider_limited, last_params = _do_paged_fetch(q, None)
                except Exception:
                    # Surface a friendly runtime error to the caller
                    raise RuntimeError("Unable to fetch results from provider.")

        # Ensure each result has a link if possible
        def _find_link(item: Dict[str, Any]) -> Optional[str]:
            for key in ("apply_link", "job_apply_link", "apply_url", "jobUrl", "url", "link"):
                val = item.get(key)
                if isinstance(val, str) and val:
                    return val
            for alt in ("related_links", "other_links", "links"):
                v = item.get(alt)
                if isinstance(v, list) and v:
                    for entry in v:
                        if isinstance(entry, dict):
                            for subk in ("link", "url", "apply_url", "jobUrl"):
                                if subk in entry and isinstance(entry[subk], str):
                                    return entry[subk]
                        if isinstance(entry, str):
                            return entry
            # some providers (google_jobs) return apply options list with dicts
            ao = item.get("apply_options") or item.get("apply_options_list")
            if isinstance(ao, list) and ao:
                for entry in ao:
                    if isinstance(entry, dict):
                        link = entry.get("link") or entry.get("url")
                        if isinstance(link, str) and link:
                            return link
                    elif isinstance(entry, str):
                        return entry
            return None

        for it in results:
            found = _find_link(it)
            if found:
                it.setdefault("apply_link", found)

        # Logging for debug
        try:
            self.logger.debug("final_q: %s", last_params.get("q") if isinstance(last_params, dict) else q_final)
            self.logger.debug("final_location: %s", last_params.get("location") if isinstance(last_params, dict) else sanitized_location)
            self.logger.debug("jobs_fetched: %d", len(results))
            self.logger.debug("provider_limited: %s", provider_limited)
        except Exception:
            pass

        return results

    def search_page(
        self,
        query: str,
        location: Optional[str] = None,
        remote: Optional[str] = None,
        experience_level: Optional[str] = None,
        employment_type: Optional[str] = None,
        tech_stack: Optional[str] = None,
        next_page_token: Optional[str] = None,
        num: int = 10,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch a single page using SerpAPI `start` and `num` and return results plus meta.

        This method is explicit for UI pagination: it performs a single request (start)
        and returns a tuple of (results, meta).
        """
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY is not configured")

        q = (query or "").strip()
        parts: List[str] = []
        if q:
            parts.append(q)
        if remote:
            parts.append(remote)
        if experience_level:
            parts.append(experience_level)
        if employment_type:
            parts.append(employment_type)
        if tech_stack:
            parts.append(tech_stack)
        q_final = " ".join(parts).strip()

        if not q_final:
            raise ValueError("Query must include job title or keywords.")

        # sanitize location same as search
        def _sanitize_location(loc: Optional[str]) -> Optional[str]:
            if not loc:
                return None
            s = loc.strip()
            if not s:
                return None
            if s.lower() == "anywhere":
                return None
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if not parts:
                return None
            return ", ".join(parts[:2])

        sanitized_location = _sanitize_location(location)

        params: Dict[str, Any] = {"engine": "google_jobs", "q": q_final, "api_key": self.api_key, "num": num}
        if sanitized_location:
            params["location"] = sanitized_location
        if next_page_token:
            params["next_page_token"] = next_page_token

        try:
            masked = {k: ("<hidden>" if k.lower() == "api_key" else v) for k, v in params.items()}
            self.logger.debug("SerpAPI single-page request params (masked): %s", masked)
        except Exception:
            pass

        resp = requests.get(self.BASE, params=params, timeout=10)
        status = resp.status_code
        try:
            resp.raise_for_status()
        except Exception as exc:
            # Return empty list with meta including error body if non-200
            body = None
            try:
                body = resp.text
            except Exception:
                body = ""
            meta = {"status": status, "error_body": body, "jobs_returned": 0}
            return [], meta

        data = resp.json()
        page_items: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            if "jobs_results" in data and isinstance(data["jobs_results"], list):
                page_items = data["jobs_results"]
            else:
                for k, v in data.items():
                    if isinstance(v, list):
                        page_items = v
                        break

        if not isinstance(page_items, list):
            page_items = []

        # Ensure each result has a link if possible
        def _find_link(item: Dict[str, Any]) -> Optional[str]:
            for key in ("apply_link", "job_apply_link", "apply_url", "jobUrl", "url", "link"):
                val = item.get(key)
                if isinstance(val, str) and val:
                    return val
            for alt in ("related_links", "other_links", "links"):
                v = item.get(alt)
                if isinstance(v, list) and v:
                    for entry in v:
                        if isinstance(entry, dict):
                            for subk in ("link", "url", "apply_url", "jobUrl"):
                                if subk in entry and isinstance(entry[subk], str):
                                    return entry[subk]
                        if isinstance(entry, str):
                            return entry
            return None

        for it in page_items:
            found = _find_link(it)
            if found:
                it.setdefault("apply_link", found)

        meta = {"status": status, "error_body": None, "jobs_returned": len(page_items), "next_page_token": None}
        # surface next_page_token if provider returned one
        try:
            token = data.get("next_page_token") if isinstance(data, dict) else None
            if token:
                meta["next_page_token"] = token
        except Exception:
            pass
        return page_items, meta

    def test_fetch_once(self, q: str = "engineer", location: Optional[str] = None) -> None:
        """Utility to print a single request status, error body, and count of jobs for debugging."""
        params: Dict[str, Any] = {"engine": "google_jobs", "q": q, "api_key": self.api_key, "start": 0}
        if location:
            params["location"] = location
        try:
            masked = {k: ("<hidden>" if k.lower() == "api_key" else v) for k, v in params.items()}
            self.logger.info("test_fetch_once params (masked): %s", masked)
        except Exception:
            pass

        resp = requests.get(self.BASE, params=params, timeout=10)
        status = resp.status_code
        body = ""
        try:
            body = resp.text
        except Exception:
            body = ""
        jobs = 0
        try:
            data = resp.json()
            if isinstance(data, dict) and "jobs_results" in data and isinstance(data["jobs_results"], list):
                jobs = len(data["jobs_results"])
        except Exception:
            pass

        print("test_fetch_once -> status:", status)
        print("test_fetch_once -> error/body (truncated):", (body or "")[:800])
        print("test_fetch_once -> jobs:", jobs)

    def health_check(self, q: str = "engineer", location: Optional[str] = None) -> Tuple[int, int]:
        """
        Perform a single google_jobs request and return (status_code, provider_response_length).
        Logs status and length. Raises on request errors.
        """
        params: Dict[str, Any] = {"engine": "google_jobs", "q": q, "api_key": self.api_key, "start": 0}
        if location:
            params["location"] = location
        try:
            masked = {k: ("<hidden>" if k.lower() == "api_key" else v) for k, v in params.items()}
            self.logger.info("health_check request params (masked): %s", masked)
        except Exception:
            pass

        resp = requests.get(self.BASE, params=params, timeout=10)
        status = resp.status_code
        length = 0
        try:
            data = resp.json()
            if isinstance(data, dict):
                if "jobs_results" in data and isinstance(data["jobs_results"], list):
                    length = len(data["jobs_results"])
                else:
                    for v in data.values():
                        if isinstance(v, list):
                            length = len(v)
                            break
        except Exception:
            pass

        self.logger.info("health_check status=%s response_length=%d", status, length)
        return status, length

        # Ensure each result has a link if possible
        def _find_link(item: Dict[str, Any]) -> Optional[str]:
            for key in ("apply_link", "job_apply_link", "apply_url", "jobUrl", "url", "link"):
                val = item.get(key)
                if isinstance(val, str) and val:
                    return val
            for alt in ("related_links", "other_links", "links"):
                v = item.get(alt)
                if isinstance(v, list) and v:
                    for entry in v:
                        if isinstance(entry, dict):
                            for subk in ("link", "url", "apply_url", "jobUrl"):
                                if subk in entry and isinstance(entry[subk], str):
                                    return entry[subk]
                        if isinstance(entry, str):
                            return entry
            return None

        for it in results:
            found = _find_link(it)
            if found:
                it.setdefault("apply_link", found)

        # Logging for debug
        try:
            self.logger.debug("final_q: %s", last_params.get("q") if isinstance(last_params, dict) else q_final)
            self.logger.debug("final_location: %s", last_params.get("location") if isinstance(last_params, dict) else sanitized_location)
            self.logger.debug("jobs_fetched: %d", len(results))
            self.logger.debug("provider_limited: %s", provider_limited)
        except Exception:
            pass

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


@st.cache_data(ttl=300)
def cached_search_page(
    api_key: str,
    q: str,
    location: Optional[str] = None,
    remote: Optional[str] = None,
    experience_level: Optional[str] = None,
    employment_type: Optional[str] = None,
    tech_stack: Optional[str] = None,
    next_page_token: Optional[str] = None,
    num: int = 10,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    client = SerpApiClient(api_key=api_key)
    return client.search_page(
        query=q,
        location=location,
        remote=remote,
        experience_level=experience_level,
        employment_type=employment_type,
        tech_stack=tech_stack,
        next_page_token=next_page_token,
        num=num,
    )
