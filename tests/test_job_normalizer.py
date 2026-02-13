from services.job_normalizer import normalize_job


def test_normalize_fallback_links():
    raw = {"title": "Dev", "company_name": "X", "related_links": [{"url": "http://apply"}], "description": "desc"}
    job = normalize_job(raw)
    assert job.apply_link == "http://apply"
    assert job.job_title == "Dev"


def test_apply_link_priority():
    raw = {"title": "Dev", "company_name": "X", "apply_link": "http://a", "job_apply_link": "http://b", "links": [{"link": "http://c"}], "description": "desc"}
    job = normalize_job(raw)
    assert job.apply_link == "http://a"


def test_normalize_relative_url():
    raw = {"title": "Dev", "company_name": "X", "link": "//jobs.example.com/123", "description": "desc"}
    job = normalize_job(raw)
    assert job.apply_link.startswith("https://")
