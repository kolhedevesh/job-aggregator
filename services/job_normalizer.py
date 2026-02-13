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
    apply_link = _first(raw.get("url"), raw.get("link"), raw.get("apply_link"))
    source_site = _first(raw.get("source"), raw.get("site"), "unknown")

    # Truncate short description to a few lines (approx 240 chars)
    short_text = (short or "").strip()
    if len(short_text) > 240:
        short_text = short_text[:237].rstrip() + "..."

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
