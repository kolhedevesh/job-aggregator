from typing import Dict, List

from models.job import Job


def _first(*args):
    for a in args:
        if a:
            return a
    return ""


def normalize_job(raw: Dict) -> Job:
    # Map common SerpAPI / job keys to our schema with safe fallbacks
    title = _first(raw.get("title"), raw.get("job_title"), raw.get("position"))
    company = _first(raw.get("company_name"), raw.get("employer_name"), raw.get("company"))
    location = _first(raw.get("location"), raw.get("formatted_location"), raw.get("city"))
    short = _first(raw.get("snippet"), raw.get("description"), raw.get("summary"))
    employment = _first(raw.get("employment_type"), raw.get("job_type"), "")

    # Determine apply_link with a clear priority
    apply_link = _first(
        raw.get("apply_link"),
        raw.get("job_apply_link"),
        raw.get("url"),
        raw.get("link"),
    )
    if not apply_link:
        rl = raw.get("related_links") or raw.get("other_links") or raw.get("links")
        if isinstance(rl, list) and rl:
            first = rl[0]
            if isinstance(first, dict):
                apply_link = first.get("link") or first.get("url")
            elif isinstance(first, str):
                apply_link = first

    # Clean description: remove literal 'Description' header and trim to ~300 chars
    short_text = (short or "").replace("Description", "").strip()
    if len(short_text) > 300:
        short_text = short_text[:297].rstrip() + "..."

    # source_site: prefer explicit fields if present
    source_site = _first(raw.get("source"), raw.get("site"), raw.get("source_site"), raw.get("company_website"))

    return Job(
        company_name=company or "",
        job_title=title or "",
        location=location or "",
        short_description=short_text,
        employment_type=employment or "",
        source_site=source_site or "unknown",
        apply_link=apply_link or "",
    )


def normalize_jobs(raw_list: List[Dict]) -> List[Job]:
    return [normalize_job(r) for r in raw_list]
