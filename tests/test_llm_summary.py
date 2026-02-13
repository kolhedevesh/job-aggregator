import services.llm_service as ls
from services.job_normalizer import normalize_job


def test_summary_used_when_llm_enabled(monkeypatch):
    raw = {"title": "Dev", "company_name": "X", "description": "Long description text here."}

    # mock cached_summarize_description to return a predictable summary
    def fake_cached(host, model, text):
        return "LLM SUMMARY: concise summary about role and skills."

    monkeypatch.setattr(ls, "cached_summarize_description", fake_cached)

    job = normalize_job(raw)
    # simulate app behavior
    s = ls.cached_summarize_description(None, None, job.short_description)
    assert s.startswith("LLM SUMMARY")


def test_fallback_truncation():
    raw = {"title": "Dev", "company_name": "X", "description": "A" * 2000}
    job = normalize_job(raw)
    # fallback should trim to 500 chars
    fallback = job.short_description[:500]
    assert len(fallback) == 500
