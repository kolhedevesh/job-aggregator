# RUN_QA — Tests and Manual Checklist

Automated tests

1. Install dependencies (use virtualenv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest -q
```

Manual QA checklist

- Start the app: `streamlit run app.py`
- Open the UI and confirm the sidebar filters appear.
- Search a common job term (e.g., "Software Engineer"). The app should:
  - show a spinner while fetching
  - display up to 10 results per page
  - allow navigating Next/Prev through pages (30 results total)
  - only show an "Apply" link when a job has an external link
- If the SerpAPI call fails, a friendly error should appear instead of raw tracebacks.
- If Ollama is enabled, summaries and skills should be shown; failures should gracefully fall back to raw text.

If tests fail, check network access and environment variables: `SERPAPI_API_KEY`, `OLLAMA_HOST`, and `OLLAMA_MODEL`.
