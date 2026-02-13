from services.job_normalizer import normalize_job


def test_normalize_fallback_links():
    raw = {"title": "Dev", "company_name": "X", "related_links": [{"url": "http://apply"}], "description": "desc"}
    job = normalize_job(raw)
    assert job.apply_link == "http://apply"
    assert job.job_title == "Dev"
