from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse
import re

from models.job import Job


def _first(*args):
    for a in args:
        if a:
            return a
    return ""


def _normalize_url(u: Optional[str]) -> Optional[str]:
    if not u or not isinstance(u, str):
        return None
    s = u.strip()
    parsed = urlparse(s)
    if not parsed.scheme:
        if s.startswith("//"):
            s = "https:" + s
            parsed = urlparse(s)
        else:
            # If looks like domain/path, add https
            if re.match(r"^[\w.-]+(:?\d+)?(/|$)", s):
                s = "https://" + s
                parsed = urlparse(s)
    if parsed.scheme not in ("http", "https"):
        return None
    return urlunparse(parsed)


def normalize_job(raw: Dict) -> Job:
    # Map common SerpAPI / job keys to our schema with safe fallbacks
    title = _first(raw.get("title"), raw.get("job_title"), raw.get("position"))
    company = _first(raw.get("company_name"), raw.get("employer_name"), raw.get("company"))
    location = _first(raw.get("location"), raw.get("formatted_location"), raw.get("city"))
    short = _first(raw.get("snippet"), raw.get("description"), raw.get("summary"))
    employment = _first(raw.get("employment_type"), raw.get("job_type"), "")

    # Determine apply_link with a clear priority and normalization
    candidates = [
        raw.get("apply_link"),
        raw.get("job_apply_link"),
        raw.get("apply_url"),
        raw.get("jobUrl"),
        raw.get("url"),
        raw.get("link"),
    ]
    apply_link = None
    for c in candidates:
        v = _normalize_url(c)
        if v:
            apply_link = v
            break

    if not apply_link:
        rl = raw.get("related_links") or raw.get("other_links") or raw.get("links")
        if isinstance(rl, list) and rl:
            for entry in rl:
                if isinstance(entry, dict):
                    for k in ("link", "url", "apply_url", "jobUrl"):
                        v = _normalize_url(entry.get(k))
                        if v:
                            apply_link = v
                            break
                    if apply_link:
                        break
                elif isinstance(entry, str):
                    v = _normalize_url(entry)
                    if v:
                        apply_link = v
                        break

    # Also consider google_jobs-style 'apply_options' lists
    if not apply_link:
        ao = raw.get("apply_options") or raw.get("apply_options_list")
        if isinstance(ao, list) and ao:
            for entry in ao:
                if isinstance(entry, dict):
                    link = entry.get("link") or entry.get("url")
                    v = _normalize_url(link)
                    if v:
                        apply_link = v
                        break
                elif isinstance(entry, str):
                    v = _normalize_url(entry)
                    if v:
                        apply_link = v
                        break

    # Clean description: remove literal 'Description' header and trim to ~300 chars
    short_text = (short or "").replace("Description", "").strip()
    # Keep more of the original description available; downstream will truncate for summaries.
    if len(short_text) > 2000:
        short_text = short_text[:1997].rstrip() + "..."

    # source_site: prefer explicit fields if present; allow empty string
    source_site = _first(raw.get("source"), raw.get("site"), raw.get("source_site"), raw.get("company_website"))

    return Job(
        company_name=company or "",
        job_title=title or "",
        location=location or "",
        short_description=short_text,
        employment_type=employment or "",
        source_site=source_site or "",
        apply_link=apply_link or "",
    )


def normalize_jobs(raw_list: List[Dict]) -> List[Job]:
    return [normalize_job(r) for r in raw_list]
